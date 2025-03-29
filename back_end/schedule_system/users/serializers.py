# users/serializers.py
from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# 用户注册序列化器
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        try:
            validate_password(value)  # 使用 Django 内置的密码验证
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_username(self, value):
        if not value:
            raise serializers.ValidationError("用户名不能为空")
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("邮箱不能为空")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


# 用户登录序列化器
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(error_messages={
        'blank': '用户名不能为空',
        'required': '用户名不能为空'
    })
    password = serializers.CharField(error_messages={
        'blank': '密码不能为空',
        'required': '密码不能为空'
    })

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username and password:
            # 使用精确匹配查找用户
            try:
                # 区分大小写查找用户
                user = User.objects.get(username__exact=username)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.", code="unauthorized"
                )

            # 验证密码
            if not user.check_password(password):
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.", code="unauthorized"
                )

            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")

            return user
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'.")


# 用户更新序列化器
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "created_at",
            "last_login"
        ]  # 可以扩展更多字段
        extra_kwargs = {
            "username": {"required": False},
            "email": {"required": False},
            "created_at": {"read_only": True},
            "last_login": {"read_only": True}
        }

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("邮箱不能为空")
        return value


# 用户密码修改序列化器
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not value:
            raise serializers.ValidationError("旧密码不能为空")
        return value

    def validate_new_password(self, value):
        if not value:
            raise serializers.ValidationError("新密码不能为空")
        try:
            validate_password(value)  # 使用 Django 内置的密码验证
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError("新密码不能与旧密码相同")
        return data
