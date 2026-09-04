from rest_framework import serializers


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
