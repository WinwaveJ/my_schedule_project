# users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
import re


# 自定义用户管理器
# 继承自Django的BaseUserManager，提供创建用户和管理员用户的方法
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        """
        创建普通用户方法
        参数:
            username: 用户名(必填)
            email: 邮箱(必填)
            password: 密码(可选，至少8位字符)
        返回值:
            创建的用户对象
        异常:
            ValueError: 当必填字段为空或用户名/邮箱已存在时抛出
        """
        if not email:
            raise ValueError("The Email field must be set")
        if password and len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not username.strip():
            raise ValueError("Username cannot be empty")
        email = self.normalize_email(email)
        if self.filter(username__exact=username).exists():
            raise ValueError("A user with that username already exists.")
        if self.filter(email__iexact=email).exists():
            raise ValueError("A user with that email already exists.")
        user = self.model(username=username, email=email)
        user.set_password(make_password(password) if password else None)
        user.save(using=self._db)
        return user

    def create_user_admin(self, username, email, password=None):
        """
        创建管理员用户方法
        参数:
            username: 用户名(必填)
            email: 邮箱(必填)
            password: 密码(必填，至少12位字符)
        返回值:
            创建的管理员用户对象
        异常:
            ValueError: 当密码不符合要求时抛出
        """
        if not password:
            raise ValueError("Admin users must have a password")
        if len(password) < 12:
            raise ValueError("Admin password must be at least 12 characters")
        user = self.create_user(username, email, password)
        user.role = self.model.Role.USERADMIN
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        """
        通过用户名获取用户(用于Django认证系统)
        参数:
            username: 要查找的用户名
        返回值:
            匹配的用户对象
        """
        return self.get(username__exact=username)


# 继承自Django的AbstractBaseUser，实现自定义用户认证模型
class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)  # 用户ID，自增主键
    username = models.CharField(
        max_length=50,
        unique=True,
        db_collation="utf8_bin",  # 使用utf8_bin排序规则，用户名区分大小写
    )  # 用户名，唯一且不能为空
    email = models.EmailField(unique=True)  # 邮箱地址，唯一且不能为空

    class Role(models.TextChoices):  # 用户角色枚举类
        USER = "user", "普通用户"
        USERADMIN = "user_admin", "用户管理员"

    role = models.CharField(
        max_length=15,
        choices=Role.choices,
        default=Role.USER,  # 默认角色为普通用户
    )  # 用户角色字段

    created_at = models.DateTimeField(auto_now_add=True)  # 用户创建时间，自动设置
    updated_at = models.DateTimeField(auto_now=True)  # 用户最后更新时间，自动设置

    USERNAME_FIELD = "username"  # 指定用户名字段作为认证标识
    REQUIRED_FIELDS = ["email"]  # 创建用户时必须提供的字段(除用户名外)

    is_active = models.BooleanField(default=True)  # 用户是否激活，默认激活
    is_deleted = models.BooleanField(default=False)  # 用户是否被删除，默认未删除
    deleted_at = models.DateTimeField(null=True, blank=True)  # 用户删除时间，可为空

    def delete(self, *args, **kwargs):
        """
        软删除用户方法
        将is_deleted设为True并记录删除时间
        不实际删除数据库记录
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """
        恢复已删除用户方法
        将is_deleted设为False并清除删除时间
        异常:
            ValueError: 当用户未被删除时抛出
        """
        if not self.is_deleted:
            raise ValueError("User is not deleted")
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def is_admin(self):
        """
        检查用户是否为管理员
        返回值:
            bool: 如果是管理员返回True，否则返回False
        """
        return self.role == "user_admin"

    objects = UserManager()

    class Meta:  # 模型元数据配置
        db_table = "users_user"  # 指定数据库表名
        ordering = ["-created_at"]  # 默认按创建时间降序排序
        indexes = [
            models.Index(fields=["email"]),  # 为邮箱字段创建索引
            models.Index(fields=["is_active"]),  # 为激活状态字段创建索引
            models.Index(fields=["is_deleted"]),  # 为删除状态字段创建索引
        ]
        constraints = [  # 定义模型约束
            models.UniqueConstraint(
                fields=["username"], name="case_sensitive_username"  # 用户名区分大小写
            ),
            models.UniqueConstraint(fields=["email"], name="case_sensitive_email"),  # 邮箱区分大小写
        ]

    @property
    def id(self):
        """
        用户ID属性
        返回值:
            int: 用户ID
        """
        return self.user_id

    def save(self, *args, **kwargs):
        """
        保存用户方法
        自动将邮箱转为小写并确保有默认角色
        """
        self.email = self.email.lower()
        if not hasattr(self, "role"):
            self.role = self.Role.USER
        super().save(*args, **kwargs)

    def __str__(self):
        """
        用户字符串表示
        返回值:
            str: 用户名
        """
        return self.username

    def clean(self):
        """
        模型验证方法
        验证用户名和邮箱的有效性
        异常:
            ValidationError: 当用户名或邮箱无效时抛出
        """
        super().clean()
        if not self.username.strip():
            raise ValidationError("Username cannot be empty")
        if not self.email.strip():
            raise ValidationError("Email cannot be empty")
        if not re.match(r"^[\w.@+-]+$", self.username):
            raise ValidationError("Username contains invalid characters")
        if len(self.username) > 50:
            raise ValidationError("Username cannot exceed 50 characters")
