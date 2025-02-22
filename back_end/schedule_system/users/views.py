# users/views.py
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from django.contrib.auth import login, authenticate


# 用户注册视图
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer


# 用户登录视图
@api_view(["POST"])
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
