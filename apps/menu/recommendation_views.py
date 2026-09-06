from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_recommendation import recommend_menu
from .recommendation_serializers import (
    RecommendationRequestSerializer,
    RecommendationResponseSerializer,
)


@extend_schema(
    summary="Recommend menu items",
    description=(
        "Turn a natural-language request into ranked menu suggestions.\n\n"
        "Send **either** `question` (free text, parsed into preference tokens) "
        "**or** `tokens` (the tokens from a previous response, after the customer "
        "edited them) — never both. Re-ranking from tokens skips model inference, "
        "so a customer can toggle a chip off and get a fresh ranking instantly.\n\n"
        "Public: no authentication required, matching the rest of the menu reads. "
        "The endpoint always returns ranked items — if the model checkpoint is "
        "absent or fails, a deterministic menu-matching fallback takes over and "
        "`model.status` says why."
    ),
    request=RecommendationRequestSerializer,
    responses={200: RecommendationResponseSerializer},
    examples=[
        OpenApiExample(
            "Ask a question",
            summary="Free-text request",
            description="The usual first call. Tokens come back for the UI to render as editable chips.",
            value={"question": "something sweet with chocolate, no coffee"},
            request_only=True,
        ),
        OpenApiExample(
            "Re-rank from edited tokens",
            summary="Follow-up after the customer edits the chips",
            description="Send the tokens back with `state` flipped or entries removed. No model inference runs.",
            value={
                "tokens": [
                    {"value": "chocolate", "label": "Chocolate", "state": "wanted"},
                    {"value": "coffee", "label": "Coffee", "state": "excluded"},
                ]
            },
            request_only=True,
        ),
    ],
)
class MenuRecommendationView(APIView):
    """Turn a natural-language request (or edited tokens) into menu suggestions."""

    permission_classes = [AllowAny]
    serializer_class = RecommendationRequestSerializer

    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(
            recommend_menu(
                question=data.get("question"),
                tokens=data.get("tokens") if "tokens" in data else None,
            )
        )
