# pizza_project integration

The menu endpoint `POST /menu/recommend/` lazily loads the trained FLAN-T5
checkpoint used by `pizza_project/inference.py`.

## Add the trained model

Copy the **contents** of your trained folder:

```
checkpoints/flan_t5_pizza/
```

into:

```
bihes-back/pizza_ai/checkpoints/flan_t5_pizza/
```

Typical Hugging Face files include `config.json`, model weights,
`tokenizer_config.json`, `special_tokens_map.json`, and SentencePiece/tokenizer
files.

Alternatively set an absolute path before starting Django:

```bash
export PIZZA_MODEL_PATH=/absolute/path/to/checkpoints/flan_t5_pizza
```

Install the optional AI dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-ai.txt
```

The API remains usable without the checkpoint. In that case it uses a
menu-aware deterministic fallback, and reports `model.status =
"checkpoint_missing"` in the JSON response.

## Request flow

First request:

```json
{"question": "something chocolate but no almond"}
```

After the user edits chips, send the tokens instead of the sentence. This
re-ranks the database without re-running the transformer:

```json
{
  "tokens": [
    {"value": "chocolate", "state": "wanted", "kind": "preference"},
    {"value": "almond", "state": "excluded", "kind": "preference"}
  ]
}
```

## tree.rar

The supplied archive contains semantic-tree/evaluation utilities. The runtime
integration uses the same parenthesised EXR structure but includes a small
self-contained S-expression reader in `apps/menu/ai_recommendation.py`, so the
web API does not require `anytree` or the catalog files that were not present
in the archive.
