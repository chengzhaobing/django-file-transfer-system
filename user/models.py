from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """扩展用户模型"""
    email = models.EmailField(unique=True, verbose_name='邮箱')
    is_email_verified = models.BooleanField(default=False, verbose_name='邮箱已验证')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'auth_user'

class EmailVerificationCode(models.Model):
    """邮箱验证码模型"""
    email = models.EmailField(verbose_name='邮箱')
    code = models.CharField(max_length=6, verbose_name='验证码')
    code_type = models.CharField(max_length=20, choices=[
        ('register', '注册验证'),
        ('login', '登录验证'),
        ('reset_password', '重置密码')
    ], verbose_name='验证码类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    is_used = models.BooleanField(default=False, verbose_name='已使用')
    
    class Meta:
        verbose_name = '邮箱验证码'
        verbose_name_plural = '邮箱验证码'
        db_table = 'user_email_verification_code'
        indexes = [
            models.Index(fields=['email', 'code_type', 'created_at']),
        ]
    
    def is_expired(self):
        """检查验证码是否过期"""
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f'{self.email} - {self.code_type} - {self.code}'

class UserLoginLog(models.Model):
    """用户登录日志"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    login_type = models.CharField(max_length=20, choices=[
        ('username', '用户名登录'),
        ('email', '邮箱登录'),
        ('email_code', '邮箱验证码登录')
    ], verbose_name='登录方式')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.TextField(verbose_name='用户代理')
    login_time = models.DateTimeField(auto_now_add=True, verbose_name='登录时间')
    is_success = models.BooleanField(default=True, verbose_name='登录成功')
    
    class Meta:
        verbose_name = '用户登录日志'
        verbose_name_plural = '用户登录日志'
        db_table = 'user_login_log'
        ordering = ['-login_time']
    
    def __str__(self):
        return f'{self.user.username} - {self.login_type} - {self.login_time}'