from rest_framework import serializers

from .ai_recommendation import MODEL_STATUSES
from .serializers import MenuItemSerializer


class RecommendationTokenSerializer(serializers.Serializer):
    value = serializers.CharField(max_length=120)
    label = serializers.CharField(max_length=120, required=False, allow_blank=True)
    kind = serializers.CharField(max_length=40, required=False, default="preference")
    state = serializers.ChoiceField(choices=("wanted", "excluded"), default="wanted")
    source = serializers.CharField(max_length=40, required=False, allow_blank=True)


class RecommendationRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500, required=False, allow_blank=False)
    tokens = RecommendationTokenSerializer(many=True, required=False)

    def validate(self, attrs):
        if "question" not in attrs and "tokens" not in attrs:
            raise serializers.ValidationError("Send either 'question' or 'tokens'.")
        if "question" in attrs and "tokens" in attrs:
            raise serializers.ValidationError("Send 'question' or 'tokens', not both.")
        return attrs


class RecommendedMenuItemSerializer(MenuItemSerializer):
    """A menu item as the recommender returns it: the usual shape, plus why.

    Declared for the OpenAPI schema — ``rank_menu_items`` builds these dicts by
    hand rather than instantiating this class.
    """

    recommendation_score = serializers.FloatField(
        read_only=True, help_text="Higher means a closer match to the wanted tokens."
    )
    matched_tokens = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="Which token values this item matched.",
    )

    class Meta(MenuItemSerializer.Meta):
        fields = MenuItemSerializer.Meta.fields + (
            "recommendation_score",
            "matched_tokens",
        )


class RecommendationModelSerializer(serializers.Serializer):
    """Whether the transformer contributed, or the menu fallback did the work."""

    status = serializers.ChoiceField(choices=MODEL_STATUSES, read_only=True)
    used = serializers.BooleanField(
        read_only=True, help_text="True only when the model produced an expression."
    )
    expression = serializers.CharField(
        read_only=True,
        allow_null=True,
        help_text="Raw EXR output, for debugging. Not shown to customers.",
    )


class RecommendationResponseSerializer(serializers.Serializer):
    """What the recommendation endpoint returns."""

    tokens = RecommendationTokenSerializer(
        many=True,
        read_only=True,
        help_text="Detected preferences, editable and re-submittable as 'tokens'.",
    )
    items = RecommendedMenuItemSerializer(many=True, read_only=True)
    model = RecommendationModelSerializer(read_only=True)
