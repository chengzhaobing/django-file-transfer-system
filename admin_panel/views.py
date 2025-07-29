from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
import os
from user.models import User, UserLoginLog
from transfer.models import FileUpload, DownloadLog
from django.conf import settings


def is_admin(user):
    """检查用户是否为管理员"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """管理员仪表板"""
    return render(request, 'admin/dashboard.html')


@login_required
@user_passes_test(is_admin)
def users(request):
    """用户管理页面"""
    return render(request, 'admin/users.html')


@login_required
@user_passes_test(is_admin)
def files(request):
    """文件管理页面"""
    return render(request, 'admin/files.html')


@login_required
@user_passes_test(is_admin)
def system(request):
    """系统管理页面"""
    return render(request, 'admin/system.html')


# API视图
@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """获取仪表板统计数据"""
    try:
        # 用户统计
        total_users = User.objects.count()
        active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()
        
        # 文件统计
        total_files = FileUpload.objects.count()
        total_storage = FileUpload.objects.aggregate(Sum('file_size'))['file_size__sum'] or 0
        
        # 下载统计
        total_downloads = DownloadLog.objects.count()
        
        # 今日统计
        today = timezone.now().date()
        today_uploads = FileUpload.objects.filter(created_at__date=today).count()
        today_downloads = DownloadLog.objects.filter(created_at__date=today).count()
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'total_files': total_files,
                'total_storage': total_storage,
                'total_downloads': total_downloads,
                'today_uploads': today_uploads,
                'today_downloads': today_downloads,
                'system_load': 0  # 可以添加系统负载监控
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_users_list(request):
    """获取用户列表"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', 'all')
        sort = request.GET.get('sort', 'created_desc')
        
        # 构建查询
        users = User.objects.all()
        
        # 搜索
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )
        
        # 状态筛选
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        elif status_filter == 'staff':
            users = users.filter(is_staff=True)
        
        # 排序
        if sort == 'created_desc':
            users = users.order_by('-date_joined')
        elif sort == 'created_asc':
            users = users.order_by('date_joined')
        elif sort == 'username_asc':
            users = users.order_by('username')
        elif sort == 'username_desc':
            users = users.order_by('-username')
        
        # 分页
        paginator = Paginator(users, per_page)
        page_obj = paginator.get_page(page)
        
        # 序列化数据
        users_data = []
        for user in page_obj:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'file_count': FileUpload.objects.filter(user=user).count(),
            })
        
        return JsonResponse({
            'success': True,
            'users': users_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_user_detail(request, user_id):
    """获取用户详情"""
    try:
        user = User.objects.get(id=user_id)
        
        # 用户文件统计
        files = FileUpload.objects.filter(user=user)
        total_files = files.count()
        total_size = files.aggregate(Sum('file_size'))['file_size__sum'] or 0
        
        # 登录日志
        recent_logins = UserLoginLog.objects.filter(user=user).order_by('-created_at')[:10]
        login_data = []
        for log in recent_logins:
            login_data.append({
                'login_type': log.login_type,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'is_success': log.is_success,
                'created_at': log.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_email_verified': user.is_email_verified,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'total_files': total_files,
                'total_size': total_size,
                'recent_logins': login_data,
            }
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@csrf_exempt
@require_http_methods(["POST"])
def api_update_user(request, user_id):
    """更新用户信息"""
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_staff' in data:
            user.is_staff = data['is_staff']
        
        user.save()
        
        return JsonResponse({'success': True, 'message': '用户信息更新成功'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_user(request, user_id):
    """删除用户"""
    try:
        user = User.objects.get(id=user_id)
        
        # 删除用户的所有文件
        files = FileUpload.objects.filter(user=user)
        for file_obj in files:
            if os.path.exists(file_obj.file_path):
                os.remove(file_obj.file_path)
        files.delete()
        
        # 删除用户
        user.delete()
        
        return JsonResponse({'success': True, 'message': '用户删除成功'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_files_list(request):
    """获取文件列表"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', 'all')
        
        # 构建查询
        files = FileUpload.objects.select_related('user').all()
        
        # 搜索
        if search:
            files = files.filter(
                Q(original_filename__icontains=search) |
                Q(share_code__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        # 状态筛选
        if status_filter == 'active':
            files = files.filter(is_active=True, expires_at__gt=timezone.now())
        elif status_filter == 'expired':
            files = files.filter(expires_at__lte=timezone.now())
        elif status_filter == 'max_downloads':
            files = files.filter(download_count__gte=F('max_downloads'))
        
        # 排序
        files = files.order_by('-created_at')
        
        # 分页
        paginator = Paginator(files, per_page)
        page_obj = paginator.get_page(page)
        
        # 序列化数据
        files_data = []
        for file_obj in page_obj:
            files_data.append({
                'id': file_obj.id,
                'file_id': file_obj.file_id,
                'original_filename': file_obj.original_filename,
                'file_size': file_obj.file_size,
                'share_code': file_obj.share_code,
                'download_count': file_obj.download_count,
                'max_downloads': file_obj.max_downloads,
                'is_active': file_obj.is_active,
                'created_at': file_obj.created_at.isoformat(),
                'expires_at': file_obj.expires_at.isoformat() if file_obj.expires_at else None,
                'user': {
                    'id': file_obj.user.id,
                    'username': file_obj.user.username,
                }
            })
        
        return JsonResponse({
            'success': True,
            'files': files_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_file(request, file_id):
    """删除文件"""
    try:
        file_obj = FileUpload.objects.get(file_id=file_id)
        
        # 删除物理文件
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
        
        # 删除数据库记录
        file_obj.delete()
        
        return JsonResponse({'success': True, 'message': '文件删除成功'})
    except FileUpload.DoesNotExist:
        return JsonResponse({'success': False, 'message': '文件不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@csrf_exempt
@require_http_methods(["POST"])
def api_cleanup_expired_files(request):
    """清理过期文件"""
    try:
        expired_files = FileUpload.objects.filter(expires_at__lte=timezone.now())
        deleted_count = 0
        freed_space = 0
        
        for file_obj in expired_files:
            if os.path.exists(file_obj.file_path):
                freed_space += file_obj.file_size
                os.remove(file_obj.file_path)
            deleted_count += 1
        
        expired_files.delete()
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'freed_space': freed_space,
            'message': f'已清理 {deleted_count} 个过期文件'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_system_settings(request):
    """获取系统设置"""
    try:
        settings_data = {
            'max_file_size': getattr(settings, 'MAX_FILE_SIZE', 2147483648),
            'default_expire_days': 7,
            'max_downloads': 100,
            'allow_registration': True,
            'require_email_verification': True,
            'system_announcement': '',
        }
        
        return JsonResponse({
            'success': True,
            'settings': settings_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(is_admin)
@csrf_exempt
@require_http_methods(["POST"])
def api_update_system_settings(request):
    """更新系统设置"""
    try:
        data = json.loads(request.body)
        # 这里可以实现系统设置的保存逻辑
        # 由于设置通常保存在配置文件或数据库中，这里只是示例
        
        return JsonResponse({
            'success': True,
            'message': '系统设置更新成功'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})