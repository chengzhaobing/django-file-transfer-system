from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # 管理员页面
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.users, name='users'),
    path('files/', views.files, name='files'),
    path('system/', views.system, name='system'),
    
    # API路由
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/users/', views.api_users_list, name='api_users_list'),
    path('api/users/<int:user_id>/', views.api_user_detail, name='api_user_detail'),
    path('api/users/<int:user_id>/update/', views.api_update_user, name='api_update_user'),
    path('api/users/<int:user_id>/delete/', views.api_delete_user, name='api_delete_user'),
    path('api/files/', views.api_files_list, name='api_files_list'),
    path('api/files/<str:file_id>/delete/', views.api_delete_file, name='api_delete_file'),
    path('api/files/cleanup/', views.api_cleanup_expired_files, name='api_cleanup_expired_files'),
    path('api/system/settings/', views.api_system_settings, name='api_system_settings'),
    path('api/system/settings/update/', views.api_update_system_settings, name='api_update_system_settings'),
]