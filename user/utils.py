import random
import string
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def generate_jwt_token(user_id, expires_hours=24):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_hours),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def verify_jwt_token(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_verification_code(length=6):
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email, code, code_type='register'):
    """发送验证码邮件"""
    try:
        # 根据验证码类型设置邮件主题和模板
        subjects = {
            'register': '注册验证码',
            'login': '登录验证码',
            'reset_password': '重置密码验证码'
        }
        
        subject = subjects.get(code_type, '验证码')
        
        # 渲染邮件模板
        html_message = render_to_string('emails/verification_code.html', {
            'code': code,
            'code_type': code_type,
            'subject': subject
        })
        
        plain_message = strip_tags(html_message)
        
        # 发送邮件
        send_mail(
            subject=f'【文件传输系统】{subject}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f'验证码邮件发送成功: {email}')
        return True
        
    except Exception as e:
        logger.error(f'发送验证码邮件失败: {email} - {str(e)}')
        return False

def send_file_notification_email(email, file_name, sender_name, download_url):
    """发送文件通知邮件"""
    try:
        subject = '您收到了一个新文件'
        
        # 渲染邮件模板
        html_message = render_to_string('emails/file_notification.html', {
            'file_name': file_name,
            'sender_name': sender_name,
            'download_url': download_url
        })
        
        plain_message = strip_tags(html_message)
        
        # 发送邮件
        send_mail(
            subject=f'【文件传输系统】{subject}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f'文件通知邮件发送成功: {email}')
        return True
        
    except Exception as e:
        logger.error(f'发送文件通知邮件失败: {email} - {str(e)}')
        return False

def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def rate_limit_check(key, window_seconds, max_requests):
    """速率限制检查"""
    current_requests = cache.get(key, 0)
    
    if current_requests >= max_requests:
        return False
    
    # 增加请求计数
    cache.set(key, current_requests + 1, window_seconds)
    return True