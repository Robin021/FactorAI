<div align="center">
  <img src="assets/logo-v3.svg" alt="Factor AI Logo" width="200"/>
  
  # Factor AI (因子智投)
  
  ### 🤖 基于多智能体的智能金融分析平台
  
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
  [![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue.svg)](https://www.typescriptlang.org/)
  [![React](https://img.shields.io/badge/React-18.0%2B-blue.svg)](https://reactjs.org/)
  
  [English](./README_EN.md) | 简体中文
  
</div>

---

## 📖 项目简介

**Factor AI（因子智投）** 是一个基于大语言模型（LLM）的多智能体金融分析平台，通过模拟专业投资团队的协作流程，为投资者提供全面、深度的股票分析报告。

### 🎯 核心特性

- 🤖 **多智能体协作** - 模拟真实投资团队，包含分析师、研究员、交易员等多个角色
- 📊 **全市场覆盖** - 支持美股、A股、港股三大市场的实时分析
- 🧠 **多模型支持** - 集成DeepSeek、通义千问、Gemini等多个主流LLM
- 🎨 **现代化界面** - 基于React + Ant Design的响应式Web应用
- 🔐 **企业级认证** - 支持SSO单点登录和多级权限管理
- 📈 **实时分析** - 可视化分析进度，智能时间预估
- 📄 **专业报告** - 支持Markdown/Word/PDF多格式导出
- 🐳 **容器化部署** - Docker一键部署，快速上手

---

## 🏗️ 技术架构

### 前端技术栈

```
React 18 + TypeScript + Vite
├── UI框架: Ant Design 5.x
├── 状态管理: Zustand
├── 路由: React Router v6
├── 图表: ECharts
├── HTTP客户端: Axios
└── 样式: CSS Modules + CSS Variables
```

### 后端技术栈

```
Python 3.10+ + FastAPI
├── AI框架: LangChain + LangGraph
├── 数据库: MongoDB + Redis
├── 数据源: Tushare, AkShare, FinnHub, Yahoo Finance
├── LLM集成: OpenAI, DeepSeek, DashScope, Google AI
└── 任务队列: Celery (可选)
```

---

## 🚀 快速开始

### 方式一：Docker部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Robin021/FactorAI.git
cd FactorAI

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
```

### 方式二：本地开发

#### 后端启动

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -e .

# 3. 配置环境变量
cp .env.example .env

# 4. 启动后端服务
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev

# 3. 访问 http://localhost:3000
```

---

## 🎮 使用指南

### 1. 登录系统

- **本地账号**: 使用默认账号 `admin/admin123` 或 `user/user123`
- **企业SSO**: 支持Authing等第三方认证平台

### 2. 开始分析

1. 在仪表板点击"新建分析"
2. 输入股票代码（如：`AAPL`、`000001`、`0700.HK`）
3. 选择分析深度（1-5级）
4. 选择要启用的智能体
5. 点击"开始分析"

### 3. 查看结果

- 实时查看分析进度
- 查看详细的投资建议和风险评估
- 导出专业格式报告

---

## 🤖 智能体团队

### 分析师团队

| 智能体 | 职责 | 分析内容 |
|--------|------|----------|
| 📈 **市场技术分析师** | 技术面分析 | K线形态、技术指标、趋势判断 |
| 💰 **基本面分析师** | 基本面分析 | 财务数据、估值分析、行业地位 |
| 📰 **新闻分析师** | 新闻情绪分析 | 新闻事件、市场情绪、舆情监控 |
| 💬 **社交媒体分析师** | 社交情绪分析 | 社交媒体讨论、投资者情绪 |

### 研究团队

| 智能体 | 职责 | 工作方式 |
|--------|------|----------|
| 🐂 **看涨研究员** | 寻找买入理由 | 挖掘积极因素，构建看涨论据 |
| 🐻 **看跌研究员** | 寻找风险点 | 识别风险因素，构建看跌论据 |
| 🎯 **交易决策员** | 最终决策 | 综合双方观点，给出投资建议 |

### 管理层

| 智能体 | 职责 |
|--------|------|
| 🛡️ **风险管理员** | 风险评估与控制 |
| 👔 **研究主管** | 协调与质量把控 |

---

## 📊 支持的市场与数据源

### 市场覆盖

| 市场 | 代码格式 | 示例 | 数据源 |
|------|----------|------|--------|
| 🇺🇸 **美股** | 股票代码 | `AAPL`, `TSLA`, `NVDA` | FinnHub, Yahoo Finance |
| 🇨🇳 **A股** | 6位数字 | `000001`, `600519`, `300750` | Tushare, AkShare, 通达信 |
| 🇭🇰 **港股** | 代码.HK | `0700.HK`, `9988.HK`, `3690.HK` | AkShare, Yahoo Finance |

### 数据类型

- ✅ 实时行情数据
- ✅ 历史价格数据
- ✅ 财务报表数据
- ✅ 技术指标数据
- ✅ 新闻资讯数据
- ✅ 社交媒体数据

---

## 🧠 支持的LLM模型

### 国产模型（推荐）

| 提供商 | 模型 | 特点 | 成本 |
|--------|------|------|------|
| 🇨🇳 **DeepSeek** | deepseek-chat | 性价比极高，工具调用强 | ⭐⭐⭐⭐⭐ |
| 🇨🇳 **阿里百炼** | qwen-turbo/plus/max | 中文优化，响应快速 | ⭐⭐⭐⭐ |
| 🇨🇳 **百度千帆** | ERNIE系列 | 企业级支持 | ⭐⭐⭐ |

### 国际模型

| 提供商 | 模型 | 特点 |
|--------|------|------|
| 🌍 **Google AI** | Gemini 2.0/2.5 | 最新旗舰，多模态 |
| 🌍 **OpenAI** | GPT-4o | 经典强大 |
| 🌍 **Anthropic** | Claude 4 | 推理能力强 |

---

## 🔐 环境变量配置

### 必需配置

```bash
# LLM API密钥（至少配置一个）
DEEPSEEK_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
GOOGLE_API_KEY=your_google_api_key

# 数据源API密钥
FINNHUB_API_KEY=your_finnhub_api_key
TUSHARE_TOKEN=your_tushare_token  # 推荐配置
```

### 可选配置

```bash
# 数据库配置
MONGODB_ENABLED=true
MONGODB_HOST=localhost
MONGODB_PORT=27017

REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# SSO认证配置
AUTHING_APP_ID=your_authing_app_id
AUTHING_APP_HOST=your_authing_host
```

---

## 📁 项目结构

```
FactorAI/
├── frontend/                 # 前端应用
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── stores/         # 状态管理
│   │   ├── services/       # API服务
│   │   └── utils/          # 工具函数
│   └── public/             # 静态资源
│
├── backend/                 # 后端应用
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── services/      # 业务逻辑
│   │   ├── models/        # 数据模型
│   │   └── core/          # 核心配置
│   └── tests/             # 测试文件
│
├── tradingagents/          # AI智能体核心
│   ├── agents/            # 智能体定义
│   ├── graph/             # LangGraph工作流
│   ├── dataflows/         # 数据处理
│   └── tools/             # 工具函数
│
├── assets/                # 资源文件
│   └── logo-v3.svg       # 项目Logo
│
├── docs/                  # 文档
├── scripts/               # 脚本工具
├── docker-compose.yml     # Docker编排
└── README.md             # 本文件
```

---

## � 界多面预览

### 登录页面
<img src="docs/images/login.png" alt="登录页面" width="600"/>

### 分析仪表板
<img src="docs/images/dashboard.png" alt="仪表板" width="600"/>

### 分析结果
<img src="docs/images/analysis-result.png" alt="分析结果" width="600"/>

---

## 🛠️ 开发指南

### 代码规范

- **前端**: ESLint + Prettier
- **后端**: Black + isort + flake8
- **提交**: Conventional Commits

### 运行测试

```bash
# 前端测试
cd frontend
npm run test

# 后端测试
cd backend
pytest
```

### 构建生产版本

```bash
# 前端构建
cd frontend
npm run build

# Docker构建
docker-compose -f docker-compose.yml build
```

---

## 📚 文档

- [安装指南](docs/installation.md)
- [使用教程](docs/usage.md)
- [API文档](docs/api.md)
- [架构设计](docs/architecture.md)
- [开发指南](docs/development.md)
- [常见问题](docs/faq.md)

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献类型

- 🐛 Bug修复
- ✨ 新功能开发
- 📝 文档改进
- 🎨 UI/UX优化
- ⚡ 性能优化
- 🌐 国际化支持

---

## 📄 开源协议

本项目基于 [Apache License 2.0](LICENSE) 开源协议。

---

## 🙏 致谢

### 基于项目

本项目基于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 进行深度定制和增强开发。

### 技术栈

感谢以下开源项目：

- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用框架
- [React](https://reactjs.org/) - 前端框架
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
- [Ant Design](https://ant.design/) - UI组件库

---

## � 联系我们

- **项目主页**: https://github.com/Robin021/FactorAI
- **问题反馈**: https://github.com/Robin021/FactorAI/issues
- **讨论区**: https://github.com/Robin021/FactorAI/discussions

---

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐️

[![Star History Chart](https://api.star-history.com/svg?repos=Robin021/FactorAI&type=Date)](https://star-history.com/#Robin021/FactorAI&Date)

---

<div align="center">
  
  **Built with ❤️ by Factor AI Team**
  
  © 2024 Factor AI. All rights reserved.
  
</div>
