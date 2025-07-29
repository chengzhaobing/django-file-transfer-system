from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    """首页重定向 - 已登录用户到上传页面，未登录用户到登录页面"""
    if request.user.is_authenticated:
        return redirect('/transfer/upload/')
    else:
        return redirect('/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 首页重定向
    path('', home_redirect, name='home'),
    
    # 用户相关路由
    path('', include('user.urls')),
    
    # 文件传输相关路由
    path('transfer/', include('transfer.urls')),
    
    # 验证码路由
    path('captcha/', include('captcha.urls')),
    
    # 管理面板路由
    path('admin_panel/', include('admin_panel.urls')),
]

# 开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)