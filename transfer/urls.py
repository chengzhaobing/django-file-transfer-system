from django.urls import path
from . import views

app_name = 'transfer'

urlpatterns = [
    # 文件上传
    path('upload/', views.upload_page, name='upload_page'),
    path('api/upload/', views.FileUploadView.as_view(), name='file_upload'),
    
    # 文件下载
    path('download/', views.download_page, name='download_index'),  # 通用下载页面
    path('download/<str:share_code>/', views.download_page, name='download_page'),
    path('api/download/<str:share_code>/', views.download_file, name='download_file'),
    path('api/file-info/<str:share_code>/', views.file_info, name='file_info'),
    
    # 文件管理
    path('my-files/', views.my_files, name='my_files'),
    path('api/my-files/', views.api_my_files, name='api_my_files'),
    path('api/delete-file/<int:file_id>/', views.api_delete_file, name='api_delete_file_by_id'),
    path('api/delete-file/', views.api_delete_file, name='api_delete_file'),
    path('api/batch-delete/', views.api_batch_delete, name='api_batch_delete'),
    path('api/file-settings/<int:file_id>/', views.api_update_file_settings, name='api_file_settings'),
    path('api/update-file-settings/', views.api_update_file_settings, name='api_update_file_settings'),
    path('api/batch-download/', views.api_batch_download, name='api_batch_download'),
]