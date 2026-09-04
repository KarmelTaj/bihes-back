"""AI-assisted menu recommendation.

The trained ``pizza_project`` model produces PIZZA-style EXR S-expressions,
for example::

    (ORDER (PIZZAORDER (TOPPING PEPPERONI) (NOT (TOPPING OLIVES))))

This module keeps model inference separate from menu ranking.  The frontend can
therefore let a customer edit/toggle/remove the detected tokens and ask us to
re-rank without running the transformer again.

The S-expression reader follows the structure of the ``tree.rar`` utilities
provided with the project, but is intentionally dependency-free so the Django
API can still boot when the optional AI packages/model checkpoint are absent.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from threading import Lock
from typing import Any

from django.conf import settings

from .models import MenuItem
from .serializers import MenuItemSerializer


TOKEN_NODE_TYPES = {
    "TOPPING",
    "SIZE",
    "STYLE",
    "DRINKTYPE",
    "VOLUME",
    "CONTAINERTYPE",
}

# Small domain aliases make the current café demo data useful even though the
# supplied model was trained on pizza/drink orders.
TOKEN_ALIASES = {
    "coffee": {"coffee", "espresso", "ristretto", "latte", "mocha", "cold brew"},
    "sweet": {"sweet", "dessert", "cake", "chocolate", "cocoa", "danish", "croissant"},
    "cold": {"cold", "ice", "iced", "cold brew"},
    "hot": {"hot", "steamed", "espresso", "latte", "mocha"},
    "chocolate": {"chocolate", "cocoa", "mocha"},
    "almond": {"almond", "almonds", "frangipane"},
    "milk": {"milk", "latte", "flat white", "microfoam"},
    "pastry": {"pastry", "croissant", "danish", "baked"},
    "dessert": {"dessert", "cake", "tiramisu", "sweet"},
}

STOP_WORDS = {
    "a", "an", "and", "any", "are", "can", "could", "do", "for", "from", "get",
    "give", "have", "i", "id", "i'd", "in", "is", "it", "like", "me", "my", "of",
    "on", "one", "please", "recommend", "show", "some", "something", "that", "the",
    "to", "want", "with", "would", "you", "your", "really", "food", "item", "items",
}

NEGATION_WORDS = {"no", "not", "without", "avoid", "excluding", "exclude", "except"}


def _normalise_text(value: str) -> str:
    value = value.replace("_", " ").replace("-", " ").lower()
    value = re.sub(r"[^a-z0-9.\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _display_label(value: str) -> str:
    return _normalise_text(value).title()


def _token_key(token: dict[str, Any]) -> str:
    # The customer should see one chip per semantic value even when the model
    # and the database-aware fallback discovered it using different kinds.
    return _normalise_text(str(token["value"]))


def _clean_token(token: dict[str, Any], *, default_source: str = "user") -> dict[str, str]:
    value = _normalise_text(str(token.get("value", "")))
    state = str(token.get("state", "wanted")).lower()
    if state not in {"wanted", "excluded"}:
        state = "wanted"
    kind = str(token.get("kind", "preference")).lower()
    label = str(token.get("label") or _display_label(value))
    source = str(token.get("source") or default_source)
    return {"value": value, "label": label, "kind": kind, "state": state, "source": source}


def merge_tokens(*groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    """De-duplicate tokens. Explicit exclusion wins for the same value/kind."""
    merged: dict[str, dict[str, str]] = {}
    order: list[str] = []

    for group in groups:
        for raw in group:
            token = _clean_token(raw)
            if not token["value"]:
                continue
            key = _token_key(token)
            if key not in merged:
                merged[key] = token
                order.append(key)
            elif token["state"] == "excluded":
                merged[key]["state"] = "excluded"
    return [merged[key] for key in order]


# ---------------------------------------------------------------------------
# tree.rar-compatible EXR parsing
# ---------------------------------------------------------------------------


def parse_sexp(expression: str) -> list[Any]:
    """Parse a simple parenthesised EXR expression into nested Python lists."""
    tokens = re.findall(r"\(|\)|[^()\s,]+", expression or "")
    if not tokens:
        raise ValueError("Empty semantic expression")

    stack: list[list[Any]] = []
    root: list[Any] | None = None

    for token in tokens:
        if token == "(":
            node: list[Any] = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
            if root is None:
                root = node
        elif token == ")":
            if not stack:
                raise ValueError("Unexpected closing parenthesis")
            stack.pop()
        else:
            if not stack:
                raise ValueError("Token outside semantic group")
            stack[-1].append(token)

    if stack:
        raise ValueError("Unclosed semantic group")
    if root is None:
        raise ValueError("Invalid semantic expression")
    return root


def tokens_from_exr(expression: str) -> list[dict[str, str]]:
    """Convert model EXR output to editable wanted/excluded tokens."""
    try:
        root = parse_sexp(expression)
    except (TypeError, ValueError):
        return []

    found: list[dict[str, str]] = []

    def walk(node: Any, *, excluded: bool = False) -> None:
        if not isinstance(node, list) or not node:
            return

        label = str(node[0]).upper()
        child_excluded = excluded or label == "NOT"

        if label in TOKEN_NODE_TYPES:
            atoms = [str(part) for part in node[1:] if not isinstance(part, list)]
            if atoms:
                raw_value = " ".join(atoms)
                found.append(
                    {
                        "value": _normalise_text(raw_value),
                        "label": _display_label(raw_value),
                        "kind": label.lower(),
                        "state": "excluded" if child_excluded else "wanted",
                        "source": "model",
                    }
                )

        for child in node[1:]:
            if isinstance(child, list):
                walk(child, excluded=child_excluded)

    walk(root)
    return merge_tokens(found)


# ---------------------------------------------------------------------------
# Lazy transformer inference
# ---------------------------------------------------------------------------


class PizzaModelService:
    """Load the user's FLAN-T5 checkpoint only when the endpoint is called."""

    _lock = Lock()
    _model = None
    _tokenizer = None
    _device = None
    _loaded_path: str | None = None

    @classmethod
    def model_path(cls) -> Path:
        configured = os.getenv("PIZZA_MODEL_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        return Path(settings.BASE_DIR) / "pizza_ai" / "checkpoints" / "flan_t5_pizza"

    @classmethod
    def predict(cls, text: str) -> tuple[str | None, str]:
        path = cls.model_path()
        # A directory alone is not a Hugging Face checkpoint; config.json is a
        # reliable minimum marker and keeps an empty placeholder directory from
        # being reported as a model failure.
        if not path.exists() or not (path / "config.json").exists():
            return None, "checkpoint_missing"

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError:
            return None, "dependencies_missing"

        path_string = str(path)
        try:
            with cls._lock:
                if cls._model is None or cls._loaded_path != path_string:
                    cls._tokenizer = AutoTokenizer.from_pretrained(path_string, local_files_only=True)
                    cls._model = AutoModelForSeq2SeqLM.from_pretrained(path_string, local_files_only=True)
                    cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    cls._model.to(cls._device)
                    cls._model.eval()
                    cls._loaded_path = path_string

            prompt = f"parse pizza order: {text.strip()}"
            inputs = cls._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=128)
            inputs = {key: value.to(cls._device) for key, value in inputs.items()}

            with torch.no_grad():
                output_ids = cls._model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                )

            prediction = cls._tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
            return prediction, "ready"
        except Exception:
            # The recommendation endpoint should remain usable if a checkpoint is
            # incomplete/incompatible.  The deterministic menu fallback still runs.
            return None, "model_error"


# ---------------------------------------------------------------------------
# Database-aware fallback + ranking
# ---------------------------------------------------------------------------


def _question_words(question: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", question.lower())


def _is_negated(words: list[str], index: int) -> bool:
    start = max(0, index - 4)
    window = words[start:index]
    if any(word in NEGATION_WORDS for word in window):
        return True
    # Handle "don't / doesn't / do not" after apostrophe tokenisation.
    joined = " ".join(window)
    return "don't" in joined or "dont" in joined or "do not" in joined


def menu_tokens_from_question(question: str, items: list[MenuItem]) -> list[dict[str, str]]:
    """Extract obvious menu/category preferences without requiring the model."""
    words = _question_words(question)
    vocabulary: set[str] = set(TOKEN_ALIASES)

    for item in items:
        fields = [item.name, item.description, item.category.name]
        for field in fields:
            normal = _normalise_text(field)
            if normal:
                vocabulary.add(normal)
                vocabulary.update(
                    word for word in normal.split() if len(word) >= 3 and word not in STOP_WORDS
                )

    found: list[dict[str, str]] = []
    for index, word in enumerate(words):
        if word in STOP_WORDS or word in NEGATION_WORDS or len(word) < 3:
            continue

        normal = _normalise_text(word)
        is_menu_word = normal in vocabulary
        is_explicitly_negated = _is_negated(words, index)
        if not is_menu_word and not is_explicitly_negated:
            continue

        found.append(
            {
                "value": normal,
                "label": _display_label(normal),
                "kind": "preference",
                "state": "excluded" if is_explicitly_negated else "wanted",
                "source": "menu",
            }
        )

    # Prefer a category phrase over an individual duplicate word when the user
    # explicitly mentions the category name.
    normal_question = _normalise_text(question)
    for item in items:
        category = _normalise_text(item.category.name)
        if category and re.search(rf"\b{re.escape(category)}\b", normal_question):
            found.insert(
                0,
                {
                    "value": category,
                    "label": _display_label(category),
                    "kind": "category",
                    "state": "excluded" if re.search(
                        rf"\b(?:no|not|without|avoid|exclude|excluding)\b(?:\s+\w+){{0,3}}\s+{re.escape(category)}\b",
                        normal_question,
                    ) else "wanted",
                    "source": "menu",
                },
            )

    return merge_tokens(found)


def _simple_stem(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _term_matches(value: str, item_text: str) -> bool:
    value = _normalise_text(value)
    if not value:
        return False
    if re.search(rf"\b{re.escape(value)}\b", item_text):
        return True

    value_words = {_simple_stem(word) for word in value.split()}
    item_words = {_simple_stem(word) for word in item_text.split()}
    if value_words and value_words.issubset(item_words):
        return True

    aliases = TOKEN_ALIASES.get(value, set())
    return any(re.search(rf"\b{re.escape(_normalise_text(alias))}\b", item_text) for alias in aliases)


def rank_menu_items(items: list[MenuItem], tokens: list[dict[str, str]], *, limit: int = 8) -> list[dict[str, Any]]:
    wanted = [token for token in tokens if token["state"] == "wanted"]
    excluded = [token for token in tokens if token["state"] == "excluded"]

    ranked: list[tuple[float, MenuItem, list[str]]] = []
    for item in items:
        text = _normalise_text(f"{item.category.name} {item.name} {item.description}")

        if any(_term_matches(token["value"], text) for token in excluded):
            continue

        score = 0.0
        matched: list[str] = []
        for token in wanted:
            if _term_matches(token["value"], text):
                score += 4.0 if _normalise_text(token["value"]) in text else 2.5
                if token["kind"] == "category":
                    score += 2.0
                matched.append(token["value"])

        # With positive constraints, don't pretend zero-match products are AI
        # recommendations. With exclusions only (or no tokens), all surviving
        # products remain valid choices.
        if wanted and score <= 0:
            continue
        ranked.append((score, item, matched))

    ranked.sort(key=lambda row: (-row[0], row[1].price, row[1].name.lower()))

    result: list[dict[str, Any]] = []
    for score, item, matched in ranked[:limit]:
        data = MenuItemSerializer(item).data
        data["recommendation_score"] = score
        data["matched_tokens"] = matched
        result.append(data)
    return result


def recommend_menu(*, question: str | None = None, tokens: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = list(
        MenuItem.objects.select_related("category")
        .filter(is_available=True, category__is_active=True)
        .order_by("category__name", "name")
    )

    model_status = "not_run"
    raw_expression = None

    if tokens is not None:
        resolved_tokens = merge_tokens([_clean_token(token) for token in tokens])
    else:
        question = (question or "").strip()
        raw_expression, model_status = PizzaModelService.predict(question)
        model_tokens = tokens_from_exr(raw_expression) if raw_expression else []
        fallback_tokens = menu_tokens_from_question(question, items)
        resolved_tokens = merge_tokens(model_tokens, fallback_tokens)

    return {
        "tokens": resolved_tokens,
        "items": rank_menu_items(items, resolved_tokens),
        "model": {
            "status": model_status,
            "used": model_status == "ready" and bool(raw_expression),
            # Helpful while integrating/training; the React UI intentionally
            # does not display this implementation detail to customers.
            "expression": raw_expression,
        },
    }
