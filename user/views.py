from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import json
import logging
from captcha.image import ImageCaptcha
import io
import base64
import random
import string

from .models import User, EmailVerificationCode, UserLoginLog
from .utils import (
    generate_verification_code, 
    send_verification_email, 
    get_client_ip,
    rate_limit_check,
    generate_jwt_token,
    verify_jwt_token
)
from .tasks import send_verification_email_task

logger = logging.getLogger(__name__)

class RegisterView(View):
    """用户注册视图"""
    
    def get(self, request):
        """显示注册页面"""
        if request.user.is_authenticated:
            return redirect('user:dashboard')
        return render(request, 'user/register.html')
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """处理注册请求"""
        try:
            # 解析请求数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            email_code = data.get('email_code', '').strip()
            
            # 验证必填字段
            if not all([username, email, password, email_code]):
                return JsonResponse({
                    'success': False,
                    'message': '请填写所有必填字段'
                })
            
            # 检查用户名是否已存在
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': '用户名已存在'
                })
            
            # 检查邮箱是否已存在
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': '邮箱已被注册'
                })
            
            # 验证邮箱验证码
            verification_code = EmailVerificationCode.objects.filter(
                email=email,
                code=email_code,
                code_type='register',
                is_used=False
            ).order_by('-created_at').first()
            
            if not verification_code:
                return JsonResponse({
                    'success': False,
                    'message': '验证码无效'
                })
            
            if verification_code.is_expired():
                return JsonResponse({
                    'success': False,
                    'message': '验证码已过期'
                })
            
            # 创建用户
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_email_verified=True
                )
                
                # 标记验证码为已使用
                verification_code.is_used = True
                verification_code.save()
                
                # 记录登录日志
                UserLoginLog.objects.create(
                    user=user,
                    login_type='username',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    is_success=True
                )
                
                # 自动登录
                login(request, user)
                
                logger.info(f'用户注册成功: {username} ({email})')
                
                return JsonResponse({
                    'success': True,
                    'message': '注册成功',
                    'redirect_url': '/user/dashboard/'
                })
                
        except Exception as e:
            logger.error(f'注册失败: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': '注册失败，请稍后重试'
            })

class LoginView(View):
    """用户登录视图"""
    
    def get(self, request):
        """显示登录页面"""
        if request.user.is_authenticated:
            return redirect('user:dashboard')
        return render(request, 'user/login.html')
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """处理登录请求"""
        try:
            # 解析请求数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            login_type = data.get('login_type', 'username')
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            email_code = data.get('email_code', '').strip()
            
            user = None
            
            if login_type == 'username':
                # 用户名密码登录
                if not username or not password:
                    return JsonResponse({
                        'success': False,
                        'message': '请输入用户名和密码'
                    })
                
                user = authenticate(request, username=username, password=password)
                if not user:
                    return JsonResponse({
                        'success': False,
                        'message': '用户名或密码错误'
                    })
            
            elif login_type == 'email':
                # 邮箱密码登录
                if not email or not password:
                    return JsonResponse({
                        'success': False,
                        'message': '请输入邮箱和密码'
                    })
                
                try:
                    user_obj = User.objects.get(email=email)
                    user = authenticate(request, username=user_obj.username, password=password)
                    if not user:
                        return JsonResponse({
                            'success': False,
                            'message': '邮箱或密码错误'
                        })
                except User.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': '邮箱未注册'
                    })
            
            elif login_type == 'email_code':
                # 邮箱验证码登录
                if not email or not email_code:
                    return JsonResponse({
                        'success': False,
                        'message': '请输入邮箱和验证码'
                    })
                
                # 验证邮箱验证码
                verification_code = EmailVerificationCode.objects.filter(
                    email=email,
                    code=email_code,
                    code_type='login',
                    is_used=False
                ).order_by('-created_at').first()
                
                if not verification_code:
                    return JsonResponse({
                        'success': False,
                        'message': '验证码无效'
                    })
                
                if verification_code.is_expired():
                    return JsonResponse({
                        'success': False,
                        'message': '验证码已过期'
                    })
                
                try:
                    user = User.objects.get(email=email)
                    # 标记验证码为已使用
                    verification_code.is_used = True
                    verification_code.save()
                except User.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': '邮箱未注册'
                    })
            
            if user and user.is_active:
                # 记录登录日志
                UserLoginLog.objects.create(
                    user=user,
                    login_type=login_type,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    is_success=True
                )
                
                login(request, user)
                logger.info(f'用户登录成功: {user.username} ({login_type})')
                
                return JsonResponse({
                    'success': True,
                    'message': '登录成功',
                    'redirect_url': '/user/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '账户已被禁用'
                })
                
        except Exception as e:
            logger.error(f'登录失败: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': '登录失败，请稍后重试'
            })

@csrf_exempt
@require_http_methods(["POST"])
def send_email_code(request):
    """发送邮箱验证码"""
    try:
        # 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        email = data.get('email', '').strip()
        code_type = data.get('type', 'register')  # register, login, reset_password
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': '请输入邮箱地址'
            })
        
        # 速率限制检查
        client_ip = get_client_ip(request)
        if not rate_limit_check(f'email_code_{client_ip}', 60, 1):  # 1分钟内只能发送1次
            return JsonResponse({
                'success': False,
                'message': '发送过于频繁，请稍后再试'
            })
        
        # 检查邮箱是否已注册（根据验证码类型）
        user_exists = User.objects.filter(email=email).exists()
        
        if code_type == 'register' and user_exists:
            return JsonResponse({
                'success': False,
                'message': '邮箱已被注册'
            })
        
        if code_type in ['login', 'reset_password'] and not user_exists:
            return JsonResponse({
                'success': False,
                'message': '邮箱未注册'
            })
        
        # 生成验证码
        code = generate_verification_code()
        expires_at = timezone.now() + timedelta(minutes=10)  # 10分钟有效期
        
        # 保存验证码
        EmailVerificationCode.objects.create(
            email=email,
            code=code,
            code_type=code_type,
            expires_at=expires_at
        )
        
        # 异步发送邮件
        send_verification_email_task.delay(email, code, code_type)
        
        logger.info(f'验证码发送成功: {email} ({code_type})')
        
        return JsonResponse({
            'success': True,
            'message': '验证码已发送，请查收邮件'
        })
        
    except Exception as e:
        logger.error(f'发送验证码失败: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': '发送失败，请稍后重试'
        })

@csrf_exempt
@require_http_methods(["GET"])
def get_captcha(request):
    """获取图形验证码"""
    try:
        # 生成随机验证码
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # 生成验证码图片
        image = ImageCaptcha(width=120, height=40)
        data = image.generate(captcha_text)
        
        # 转换为base64
        img_buffer = io.BytesIO()
        img_buffer.write(data.getvalue())
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # 将验证码保存到session
        request.session['captcha'] = captcha_text.lower()
        request.session['captcha_time'] = timezone.now().timestamp()
        
        return JsonResponse({
            'success': True,
            'captcha_image': f'data:image/png;base64,{img_base64}'
        })
        
    except Exception as e:
        logger.error(f'生成验证码失败: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': '生成验证码失败'
        })

@login_required
def dashboard(request):
    """用户仪表盘"""
    # 获取用户统计信息
    from transfer.models import FileTransfer
    
    user_stats = {
        'total_transfers': FileTransfer.objects.filter(sender=request.user).count(),
        'received_transfers': FileTransfer.objects.filter(recipient_email=request.user.email).count(),
        'recent_transfers': FileTransfer.objects.filter(
            sender=request.user
        ).order_by('-created_at')[:5]
    }
    
    return render(request, 'user/dashboard.html', {
        'user_stats': user_stats
    })

@login_required
def logout_view(request):
    """用户注销"""
    username = request.user.username
    logout(request)
    messages.success(request, '已成功注销')
    logger.info(f'用户注销: {username}')
    return redirect('user:login')

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def delete_account(request):
    """删除账户"""
    try:
        # 解析请求数据
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        password = data.get('password', '')
        
        if not password:
            return JsonResponse({
                'success': False,
                'message': '请输入密码确认删除'
            })
        
        # 验证密码
        if not request.user.check_password(password):
            return JsonResponse({
                'success': False,
                'message': '密码错误'
            })
        
        username = request.user.username
        
        # 删除用户账户
        with transaction.atomic():
            request.user.delete()
        
        logger.info(f'用户删除账户: {username}')
        
        return JsonResponse({
            'success': True,
            'message': '账户已删除',
            'redirect_url': '/user/register/'
        })
        
    except Exception as e:
        logger.error(f'删除账户失败: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': '删除失败，请稍后重试'
        })

@login_required
def profile(request):
    """用户个人资料"""
    if request.method == 'POST':
        try:
            # 更新用户信息
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            
            messages.success(request, '个人资料更新成功')
            logger.info(f'用户更新个人资料: {user.username}')
            
        except Exception as e:
            logger.error(f'更新个人资料失败: {str(e)}')
            messages.error(request, '更新失败，请稍后重试')
    
    return render(request, 'user/profile.html')