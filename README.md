# Django 文件传输系统

一个基于Django的现代化文件传输系统，提供安全的文件上传、下载和管理功能。

## 功能特性

### 用户管理
- 用户注册与登录
- 邮箱验证码验证
- 图片验证码防护
- 用户个人资料管理
- 登录状态中间件保护

### 文件传输
- 安全的文件上传
- 文件下载功能
- 我的文件管理
- 文件预览支持
- 文件大小和类型限制

### 管理功能
- 管理员面板
- 用户管理
- 文件管理
- 系统监控

### 安全特性
- CSRF保护
- 登录验证中间件
- 文件类型验证
- 邮箱验证
- 密码安全策略

## 技术栈

- **后端**: Django 4.2.7
- **数据库**: SQLite (可配置为PostgreSQL/MySQL)
- **前端**: Bootstrap 5, jQuery, Font Awesome
- **邮件服务**: SMTP (支持QQ邮箱等)
- **验证码**: django-simple-captcha
- **文件存储**: 本地存储 (可扩展为云存储)

## 快速开始

### 环境要求

- Python 3.8+
- Django 4.2+
- 其他依赖见 `requirements.txt`

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/chengzhaobing/django-file-transfer-system.git
cd django-file-transfer-system
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、邮件等设置
```

5. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

6. 创建超级用户
```bash
python manage.py createsuperuser
```

7. 启动开发服务器
```bash
python manage.py runserver
```

8. 访问应用
- 主页: http://localhost:8000/
- 管理后台: http://localhost:8000/admin/

## 配置说明

### 邮件配置

在 `.env` 文件中配置邮件服务:

```env
# QQ邮箱配置示例
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@qq.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@qq.com
```

### 文件上传配置

在 `settings.py` 中可以配置:
- 文件大小限制
- 允许的文件类型
- 存储路径

## 项目结构

```
django-file-transfer-system/
├── filetransfer/          # 项目配置
├── user/                  # 用户管理应用
├── transfer/              # 文件传输应用
├── admin_panel/           # 管理面板应用
├── templates/             # 模板文件
├── static/                # 静态文件
├── media/                 # 媒体文件
├── requirements.txt       # 依赖包
├── .env.example          # 环境变量示例
└── manage.py             # Django管理脚本
```

## 主要功能模块

### 用户模块 (user/)
- 用户注册、登录、登出
- 邮箱验证码发送和验证
- 用户个人资料管理
- 登录状态中间件

### 文件传输模块 (transfer/)
- 文件上传功能
- 文件下载功能
- 文件列表管理
- 文件预览

### 管理模块 (admin_panel/)
- 用户管理
- 文件管理
- 系统统计
- 系统设置

## 开发指南

### 添加新功能

1. 在相应的应用中创建视图
2. 配置URL路由
3. 创建模板文件
4. 添加静态资源
5. 编写测试用例

### 代码规范

- 遵循PEP 8代码规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 编写单元测试

## 部署

### 生产环境部署

1. 设置环境变量
2. 配置数据库
3. 收集静态文件
4. 配置Web服务器 (Nginx/Apache)
5. 配置WSGI服务器 (Gunicorn/uWSGI)

### Docker部署

```bash
# 构建镜像
docker build -t django-file-transfer .

# 运行容器
docker run -p 8000:8000 django-file-transfer
```

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

如有问题或建议，请通过以下方式联系:

- GitHub Issues: [提交问题](https://github.com/chengzhaobing/django-file-transfer-system/issues)
- Email: your-email@example.com

## 更新日志

### v1.0.0 (2025-07-29)
- 初始版本发布
- 实现用户注册登录功能
- 实现文件上传下载功能
- 实现管理员面板
- 实现邮箱验证功能
- 实现登录验证中间件
