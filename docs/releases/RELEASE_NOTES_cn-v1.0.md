# TradingAgents-CN cn-v1.0 发布说明

## 📅 发布信息

- **版本号**: cn-v1.0
- **发布日期**: 2025-10-24
- **发布类型**: 🎉 正式稳定版本
- **上一版本**: cn-0.1.16

## 🎉 重大里程碑

这是 TradingAgents-CN 的第一个正式稳定版本！经过 16 个迭代版本的持续优化和改进，我们很高兴地宣布项目已经达到生产就绪状态。

## 🎯 本次发布重点

### ✨ 项目结构优化

- **代码清理**: 移除 21 个临时文档和 14 个测试脚本到归档目录
- **目录整理**: 优化项目结构，提升代码可维护性
- **缓存清理**: 清理 3152 个 Python 缓存目录，减少项目体积
- **临时数据清理**: 移除开发过程中的临时数据文件

### 🔧 技术改进

- **依赖管理**: 更新 pyproject.toml 版本信息
- **版本控制**: 统一版本号管理机制
- **发布流程**: 新增自动化发布准备脚本
- **文档归档**: 建立完善的文档归档体系

### 📚 文档更新

- **归档系统**: 创建 docs/archive 和 scripts/archive 目录
- **发布说明**: 生成标准化的发布说明文档
- **README 更新**: 更新版本徽章和最新版本说明
- **历史文档**: 整理所有历史开发文档到归档目录

### 🎯 累积功能特性（v0.1.0 - v1.0）

#### 🤖 LLM 生态系统
- 支持 4 大 LLM 提供商（阿里百炼、DeepSeek、Google AI、OpenRouter）
- 60+ 模型选择，包括最新的 Gemini 2.5 系列
- 原生 OpenAI 端点支持，兼容任意 OpenAI 格式 API
- 智能模型选择和配置持久化

#### 📊 数据分析能力
- 完整的 A股/港股/美股数据支持
- 智能新闻分析和过滤系统
- 多层次数据缓存优化
- MongoDB + Redis 数据库集成

#### 🖥️ Web 界面
- 现代化 Streamlit 界面
- 5 级研究深度选择（2-25 分钟）
- 实时进度跟踪和可视化
- 专业报告导出（Markdown/Word/PDF）

#### 👥 用户管理
- 完整的用户认证系统
- 角色权限管理
- 会话安全管理
- 用户活动日志

#### 🐳 部署支持
- Docker 容器化部署
- Docker Compose 一键启动
- 数据库服务自动配置
- 智能启动脚本

## 📦 安装和升级

### 新安装

```bash
# 克隆项目
git clone https://github.com/hsliuping/TradingAgents-CN.git
cd TradingAgents-CN

# Docker 部署（推荐）
docker-compose up -d --build

# 或本地部署
pip install -e .
python start_web.py
```

### 从旧版本升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建（Docker）
docker-compose down
docker-compose up -d --build

# 或更新依赖（本地）
pip install -e . --upgrade
```

## 🔗 相关链接

- **项目主页**: https://github.com/hsliuping/TradingAgents-CN
- **完整文档**: https://github.com/hsliuping/TradingAgents-CN/tree/main/docs
- **问题反馈**: https://github.com/hsliuping/TradingAgents-CN/issues

## 🙏 致谢

感谢所有贡献者和用户的支持！

---

**完整更新日志**: [CHANGELOG.md](docs/releases/CHANGELOG.md)
