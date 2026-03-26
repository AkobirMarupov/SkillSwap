from rest_framework import serializers

class RegisterINputSErializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128)


class ConfirmTokenSerializer(serializers.Serializer):
    token = serializers.CharField()