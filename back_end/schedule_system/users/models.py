# users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


# 自定义用户管理器
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


# 自定义用户模型
class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)  # 用户ID
    username = models.CharField(max_length=50, unique=True)  # 用户名
    email = models.EmailField(unique=True)  # 邮箱
    # password_hash = models.CharField(max_length=255)  # 加密后的密码
    role = models.CharField(
        max_length=10,
        choices=[("user", "普通用户"), ("admin", "管理员")],
        default="user",
    )  # 用户角色
    created_at = models.DateTimeField(default=timezone.now)  # 用户创建时间
    last_login = models.DateTimeField(default=timezone.now)  # 最后一次登录时间

    USERNAME_FIELD = "username"  # 用于登录的字段
    REQUIRED_FIELDS = ["email"]  # 必需字段

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    # 添加 id 属性作为 user_id 的别名
    @property
    def id(self):
        return self.user_id

    def __str__(self):
        return self.username

    # has_perm 和 has_module_perms 是权限相关的方法，这里直接返回True，表示用户有所有权限
    def has_perm(self, perm):
        return True  # 这里可以根据需求进行扩展

    def has_module_perms(self, app_label):
        return True  # 这里可以根据需求进行扩展
