from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .utils import send_verification_email, send_file_notification_email
from .models import EmailVerificationCode

logger = logging.getLogger(__name__)

@shared_task
def send_verification_email_task(email, code, code_type='register'):
    """异步发送验证码邮件"""
    try:
        result = send_verification_email(email, code, code_type)
        if result:
            logger.info(f'异步发送验证码邮件成功: {email}')
        else:
            logger.error(f'异步发送验证码邮件失败: {email}')
        return result
    except Exception as e:
        logger.error(f'异步发送验证码邮件异常: {email} - {str(e)}')
        return False

@shared_task
def send_file_notification_email_task(email, file_name, sender_name, download_url):
    """异步发送文件通知邮件"""
    try:
        result = send_file_notification_email(email, file_name, sender_name, download_url)
        if result:
            logger.info(f'异步发送文件通知邮件成功: {email}')
        else:
            logger.error(f'异步发送文件通知邮件失败: {email}')
        return result
    except Exception as e:
        logger.error(f'异步发送文件通知邮件异常: {email} - {str(e)}')
        return False

@shared_task
def cleanup_expired_verification_codes():
    """清理过期的验证码"""
    try:
        expired_time = timezone.now()
        deleted_count = EmailVerificationCode.objects.filter(
            expires_at__lt=expired_time
        ).delete()[0]
        
        logger.info(f'清理过期验证码完成，删除了 {deleted_count} 条记录')
        return deleted_count
    except Exception as e:
        logger.error(f'清理过期验证码失败: {str(e)}')
        return 0