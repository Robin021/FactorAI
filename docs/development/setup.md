# 开发环境搭建指南

## 概述

本指南帮助开发者快速搭建股票分析平台的本地开发环境。

## 系统要求

### 必需软件

- **Python**: 3.9+ (推荐 3.11)
- **Node.js**: 18+ (推荐 18.17+)
- **Git**: 2.30+
- **Docker**: 20.10+ (可选，用于数据库)
- **PostgreSQL**: 13+ (或使用 Docker)
- **Redis**: 6.0+ (或使用 Docker)

### 推荐工具

- **IDE**: VS Code / PyCharm / WebStorm
- **终端**: iTerm2 (macOS) / Windows Terminal
- **API 测试**: Postman / Insomnia
- **数据库管理**: pgAdmin / DBeaver

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-org/stock-analysis-platform.git
cd stock-analysis-platform
```

### 2. 使用 Docker 启动依赖服务

```bash
# 启动数据库和缓存服务
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 等待服务启动
sleep 10
```

### 3. 后端环境搭建

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements/dev.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要参数

# 运行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

### 4. 前端环境搭建

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 文件

# 启动开发服务器
npm start
```

### 5. 验证安装

- 后端 API: http://localhost:8000
- 前端应用: http://localhost:3000
- API 文档: http://localhost:8000/docs
- 管理界面: http://localhost:8000/admin

## 详细配置

### Python 环境配置

#### 使用 pyenv 管理 Python 版本

```bash
# 安装 pyenv (macOS)
brew install pyenv

# 安装 Python 3.11
pyenv install 3.11.0
pyenv global 3.11.0

# 验证版本
python --version
```

#### 虚拟环境管理

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate

# 或使用 conda
conda create -n stock-analysis python=3.11
conda activate stock-analysis

# 或使用 poetry
poetry install
poetry shell
```

### Node.js 环境配置

#### 使用 nvm 管理 Node.js 版本

```bash
# 安装 nvm (macOS/Linux)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 安装 Node.js 18
nvm install 18
nvm use 18

# 验证版本
node --version
npm --version
```

#### 包管理器选择

```bash
# 使用 npm (默认)
npm install

# 或使用 yarn
npm install -g yarn
yarn install

# 或使用 pnpm
npm install -g pnpm
pnpm install
```

### 数据库配置

#### 本地 PostgreSQL 安装

**macOS:**
```bash
brew install postgresql
brew services start postgresql
createdb stock_analysis
```

**Ubuntu:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb stock_analysis
```

**Windows:**
下载并安装 PostgreSQL 官方安装包

#### 使用 Docker (推荐)

```bash
# 启动 PostgreSQL 容器
docker run -d \
  --name postgres-dev \
  -e POSTGRES_DB=stock_analysis \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:13

# 启动 Redis 容器
docker run -d \
  --name redis-dev \
  -p 6379:6379 \
  redis:6-alpine
```

### 环境变量配置

#### 后端环境变量 (.env)

```bash
# 应用配置
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_analysis
REDIS_URL=redis://localhost:6379/0

# LLM 配置
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# 数据源配置
TUSHARE_TOKEN=your-tushare-token
FINNHUB_API_KEY=your-finnhub-key

# 开发配置
LOG_LEVEL=DEBUG
CORS_ALLOW_ALL_ORIGINS=True
```

#### 前端环境变量 (.env.local)

```bash
# API 配置
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/api/v1/ws

# 开发配置
REACT_APP_ENV=development
GENERATE_SOURCEMAP=true
FAST_REFRESH=true

# 功能开关
REACT_APP_ENABLE_MOCK=false
REACT_APP_ENABLE_DEBUG=true
```

## 开发工具配置

### VS Code 配置

#### 推荐扩展

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.isort",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-eslint"
  ]
}
```

#### 工作区配置 (.vscode/settings.json)

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.workingDirectories": ["frontend"],
  "prettier.configPath": "./frontend/.prettierrc"
}
```

#### 调试配置 (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/manage.py",
      "args": ["runserver"],
      "django": true,
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "React",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/frontend",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["start"]
    }
  ]
}
```

### Git 配置

#### Git Hooks

创建 `.githooks/pre-commit`:

```bash
#!/bin/bash

# 后端代码检查
cd backend
python -m black --check .
python -m flake8 .
python -m isort --check-only .

# 前端代码检查
cd ../frontend
npm run lint
npm run type-check

echo "Pre-commit checks passed!"
```

```bash
# 启用 Git Hooks
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

#### .gitignore 配置

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env
.env.local

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Database
*.db
*.sqlite3

# Build
build/
dist/
```

## 开发流程

### 1. 分支管理

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发完成后
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# 创建 Pull Request
```

### 2. 代码规范

#### Python 代码规范

```bash
# 格式化代码
black .

# 排序导入
isort .

# 代码检查
flake8 .

# 类型检查
mypy .
```

#### JavaScript/TypeScript 代码规范

```bash
# 格式化代码
npm run format

# 代码检查
npm run lint

# 类型检查
npm run type-check

# 修复可修复的问题
npm run lint:fix
```

### 3. 测试

#### 后端测试

```bash
# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test apps.analysis.tests

# 生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html
```

#### 前端测试

```bash
# 运行单元测试
npm test

# 运行 E2E 测试
npm run test:e2e

# 生成覆盖率报告
npm run test:coverage
```

### 4. 数据库操作

```bash
# 创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 回滚迁移
python manage.py migrate app_name 0001

# 查看迁移状态
python manage.py showmigrations
```

## 常见问题

### 1. 端口冲突

```bash
# 查看端口占用
lsof -i :8000
lsof -i :3000

# 杀死进程
kill -9 <PID>

# 使用不同端口
python manage.py runserver 8001
npm start -- --port 3001
```

### 2. 依赖安装失败

```bash
# 清理 npm 缓存
npm cache clean --force

# 删除 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install

# Python 依赖问题
pip cache purge
pip install --upgrade pip
pip install -r requirements/dev.txt --force-reinstall
```

### 3. 数据库连接问题

```bash
# 检查数据库状态
pg_isready -h localhost -p 5432

# 重启数据库服务
brew services restart postgresql
# 或
sudo systemctl restart postgresql

# 检查连接配置
python manage.py dbshell
```

### 4. 权限问题

```bash
# 修复文件权限
chmod +x scripts/*.sh

# 修复 Python 虚拟环境权限
chmod -R 755 venv/

# 修复 Node.js 权限问题
sudo chown -R $(whoami) ~/.npm
```

## 性能优化

### 1. 开发服务器优化

```bash
# Django 开发服务器优化
python manage.py runserver --settings=config.settings.dev

# React 开发服务器优化
FAST_REFRESH=true npm start
```

### 2. 数据库优化

```sql
-- 开发环境数据库配置
ALTER SYSTEM SET shared_buffers = '128MB';
ALTER SYSTEM SET effective_cache_size = '512MB';
SELECT pg_reload_conf();
```

### 3. 缓存配置

```python
# 开发环境缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 调试技巧

### 1. 后端调试

```python
# 使用 pdb 调试
import pdb; pdb.set_trace()

# 使用 Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# 日志调试
import logging
logger = logging.getLogger(__name__)
logger.debug('Debug message')
```

### 2. 前端调试

```javascript
// 使用 console 调试
console.log('Debug info:', data);
console.table(arrayData);

// 使用 React DevTools
// 安装浏览器扩展

// 使用断点调试
debugger;
```

### 3. API 调试

```bash
# 使用 curl 测试 API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 使用 httpie
http POST localhost:8000/api/v1/auth/login username=admin password=password
```

## 下一步

完成开发环境搭建后，建议：

1. 阅读 [API 文档](../api/README.md)
2. 查看 [组件库文档](../frontend/components.md)
3. 了解 [项目架构](../architecture/README.md)
4. 参与 [代码贡献](../contributing/README.md)

如有问题，请查看 [FAQ](../faq/README.md) 或联系开发团队。