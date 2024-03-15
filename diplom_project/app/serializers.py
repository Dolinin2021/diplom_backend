from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import File

user = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    last_login = serializers.DateTimeField(read_only=True, format='%d-%m-%Y, %H:%M')

    class Meta:
        model = get_user_model()
        fields = ('id', 'last_login', 'username', 'first_name', 'last_name', 'password', 'email')
        read_only_fields = ('is_staff', 'is_superuser', 'is_active')


class UserChanger(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['is_superuser']


class FileListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True)
    share = serializers.UUIDField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(read_only=True, format='%d-%m-%Y %H:%M')
    url = serializers.URLField(read_only=True)

    def create(self, validated_data):
        validated_data['title'] = validated_data.get('file')
        if validated_data.get('user'):
            validated_data['user'] = validated_data.get('user')
        else:
            validated_data['user'] = self.context['request'].user
        return File.objects.create(**validated_data)

    class Meta:
        model = File
        fields = '__all__'


class FileDetailSerializer(serializers.ModelSerializer):
    file = serializers.FileField(read_only=True)
    share = serializers.UUIDField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(read_only=True, format='%d-%m-%Y %H:%M')
    user = serializers.CharField(max_length=100, read_only=True)

    class Meta:
        model = File
        fields = '__all__'
