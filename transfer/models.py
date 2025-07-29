from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import os
import hashlib

User = get_user_model()

def generate_share_code():
    """生成8位分享码"""
    return str(uuid.uuid4()).replace('-', '')[:8].upper()

def upload_to(instance, filename):
    """文件上传路径"""
    # 按日期分目录存储
    date_path = timezone.now().strftime('%Y/%m/%d')
    # 使用UUID作为文件名，保留原始扩展名
    ext = os.path.splitext(filename)[1]
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return f'uploads/{date_path}/{new_filename}'

class FileUpload(models.Model):
    """文件上传模型"""
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='上传用户')
    original_filename = models.CharField(max_length=255, verbose_name='原始文件名')
    file_path = models.CharField(max_length=500, verbose_name='文件路径', default='uploads/default.txt')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    file_hash = models.CharField(max_length=64, verbose_name='文件哈希值', db_index=True)
    mime_type = models.CharField(max_length=100, verbose_name='MIME类型')
    share_code = models.CharField(max_length=8, unique=True, default=generate_share_code, verbose_name='分享码')
    download_count = models.PositiveIntegerField(default=0, verbose_name='下载次数')
    max_downloads = models.PositiveIntegerField(default=0, verbose_name='最大下载次数(0为无限制)')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '文件上传'
        verbose_name_plural = '文件上传'
        db_table = 'transfer_file_upload'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_code']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['expires_at', 'is_active']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # 默认72小时过期
            self.expires_at = timezone.now() + timezone.timedelta(hours=72)
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """检查文件是否过期"""
        return timezone.now() > self.expires_at
    
    def can_download(self):
        """检查是否可以下载"""
        if not self.is_active:
            return False, '文件不可用'
        if self.is_expired():
            return False, '文件已过期'
        if self.max_downloads > 0 and self.download_count >= self.max_downloads:
            return False, '下载次数已达上限'
        return True, '可以下载'
    
    def generate_file_path(self, filename):
        """生成文件存储路径"""
        # 按日期分目录存储
        date_path = timezone.now().strftime('%Y/%m/%d')
        # 使用UUID作为文件名，保留原始扩展名
        ext = os.path.splitext(filename)[1]
        new_filename = f"{uuid.uuid4().hex}{ext}"
        return f'uploads/{date_path}/{new_filename}'
    
    def get_download_url(self):
        """获取下载链接"""
        return f'/transfer/download/{self.share_code}/'
    
    def get_file_size_display(self):
        """格式化文件大小显示"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def __str__(self):
        return f'{self.original_filename} ({self.share_code})'

class DownloadLog(models.Model):
    """下载日志模型"""
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, verbose_name='文件')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.TextField(verbose_name='用户代理')
    download_time = models.DateTimeField(auto_now_add=True, verbose_name='下载时间')
    is_success = models.BooleanField(default=True, verbose_name='下载成功')
    
    class Meta:
        verbose_name = '下载日志'
        verbose_name_plural = '下载日志'
        db_table = 'transfer_download_log'
        ordering = ['-download_time']
        indexes = [
            models.Index(fields=['file_upload', 'download_time']),
            models.Index(fields=['ip_address', 'download_time']),
        ]
    
    def __str__(self):
        return f'{self.file_upload.original_filename} - {self.ip_address} - {self.download_time}'

class FileUploadChunk(models.Model):
    """文件分片上传模型(支持断点续传)"""
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, verbose_name='文件上传')
    chunk_number = models.PositiveIntegerField(verbose_name='分片序号')
    chunk_size = models.PositiveIntegerField(verbose_name='分片大小')
    chunk_hash = models.CharField(max_length=64, verbose_name='分片哈希值')
    is_uploaded = models.BooleanField(default=False, verbose_name='已上传')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '文件分片'
        verbose_name_plural = '文件分片'
        db_table = 'transfer_file_upload_chunk'
        unique_together = ['file_upload', 'chunk_number']
        indexes = [
            models.Index(fields=['file_upload', 'chunk_number']),
        ]
    
    def __str__(self):
        return f'{self.file_upload.original_filename} - 分片{self.chunk_number}'