# users/views.py
from .models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    ChangePasswordSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserUpdateSerializer,
)
from django.contrib.auth import login, authenticate
from django.utils import timezone


# 用户注册视图
@permission_classes([AllowAny])
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer


# 用户登录视图
@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    if request.method == "POST":
        print("收到登录请求:", request.data)  # 添加请求数据日志
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # 区分大小写查找用户
                user = User.objects.get(username__exact=request.data["username"])
                if user.check_password(request.data["password"]):
                    if not user.is_active:
                        print("用户被禁用:", user.username)  # 添加错误日志
                        return Response(
                            {"detail": "用户账号已被禁用"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    # 更新最后登录时间
                    user.last_login = timezone.now()
                    user.save()
                    # 创建 JWT 令牌
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                    print("登录成功:", user.username)  # 添加成功日志
                    return Response(
                        {
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "user": {
                                "username": user.username,
                                # "email": user.email,
                                "user_id": user.user_id,
                            },
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    print("密码错误:", user.username)  # 添加错误日志
                    return Response(
                        {"detail": "密码错误"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                print("用户不存在:", request.data["username"])  # 添加错误日志
                return Response(
                    {"detail": "用户不存在"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        # 处理验证错误
        print("验证错误:", serializer.errors)  # 添加验证错误日志
        if "unauthorized" in serializer.errors:
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 用户更新视图
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def user_update(request):
    user = request.user

    if request.method == "GET":
        serializer = UserUpdateSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = UserUpdateSerializer(
        user, data=request.data, partial=True
    )  # partial=True 允许部分更新
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 修改密码视图
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user

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


# 用户退出登录视图
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def user_logout(request):
    try:
        # 由于我们使用的是JWT token，客户端只需要删除token即可
        # 这里我们只需要返回成功响应
        return Response(
            {"detail": "Successfully logged out"}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"detail": "Logout failed"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
