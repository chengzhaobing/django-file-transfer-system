from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    # 注册相关
    path('register/', views.RegisterView.as_view(), name='register'),
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    
    # 登录相关
    path('login/', views.LoginView.as_view(), name='login'),
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 验证码相关API
    path('api/send-email-code/', views.send_email_code, name='send_email_code'),
    path('api/send-verification-email/', views.send_email_code, name='send_verification_email'),
    path('api/get-captcha/', views.get_captcha, name='get_captcha'),
    
    # 用户中心
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # 账户管理
    path('api/delete-account/', views.delete_account, name='delete_account'),
]