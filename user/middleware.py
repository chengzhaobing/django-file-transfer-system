from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    """登录验证中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # 不需要登录的路径
        self.public_paths = [
            '/user/login/',
            '/user/register/',
            '/user/api/login/',
            '/user/api/register/',
            '/user/api/send-email-code/',
            '/user/api/send-verification-email/',
            '/user/api/get-captcha/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/transfer/download/',  # 允许匿名下载
        ]
    
    def __call__(self, request):
        # 检查是否为公共路径
        if any(request.path.startswith(path) for path in self.public_paths):
            response = self.get_response(request)
            return response
        
        # 检查用户是否已登录
        if not request.user.is_authenticated:
            # 如果是API请求，返回JSON响应
            if request.path.startswith('/api/') or request.headers.get('Content-Type') == 'application/json':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': '请先登录',
                    'redirect_url': '/user/login/'
                }, status=401)
            else:
                # 重定向到登录页面
                return redirect('user:login')
        
        response = self.get_response(request)
        return response