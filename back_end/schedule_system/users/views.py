# users/views.py
from .models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    ChangePasswordSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserUpdateSerializer,
)
from django.contrib.auth import login, authenticate


# 用户注册视图
@permission_classes([AllowAny])
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer


# 用户登录视图
@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    if request.method == "POST":
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            # 创建 JWT 令牌
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response(
                {
                    "access_token": access_token,
                    "refresh_token": str(refresh),  # 刷新令牌
                    "message": "Login successful!",
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 用户更新视图
@api_view(["PUT"])
def user_update(request, user_id):

    # 添加认证和权限
    if not request.user.is_authenticated:
        return Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # 检查请求的用户是否是当前登录的用户或者管理员
    if request.user != user and not request.user.is_admin:
        return Response(
            {"detail": "You do not have permission to update this user"},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = UserUpdateSerializer(
        user, data=request.data, partial=True
    )  # partial=True 允许部分更新
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 修改密码视图
@api_view(["POST"])
def change_password(request, user_id):
    # 添加认证和权限
    if not request.user.is_authenticated:
        return Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # 检查请求的用户是否是当前登录的用户
    if request.user != user:
        return Response(
            {"detail": "You do not have permission to change this user's password"},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        # 验证当前密码
        old_password = serializer.validated_data["old_password"]
        if not user.check_password(old_password):
            return Response(
                {"detail": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 设置新密码
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(
            {"detail": "Password updated successfully"}, status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
