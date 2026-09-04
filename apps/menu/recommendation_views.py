from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_recommendation import recommend_menu
from .recommendation_serializers import RecommendationRequestSerializer


class MenuRecommendationView(APIView):
    """Turn a natural-language request (or edited tokens) into menu suggestions."""

    permission_classes = [AllowAny]

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
