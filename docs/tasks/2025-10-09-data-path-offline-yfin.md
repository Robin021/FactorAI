## 任务：修复离线 YFin 数据读取相对路径导致的 FileNotFoundError

- **时间**: 2025-10-09
- **上下文**: 将运行入口移动至 `backend/tradingagents_server.py` 后，日志报错：
  - `[Errno 2] No such file or directory: './data/market_data/price_data/600580.SS-YFin-data-2015-01-01-2025-03-25.csv'`
- **定位**:
  - 离线工具 `get_YFin_data` 在 `tradingagents/dataflows/interface.py` 读取：
    - 路径由 `DATA_DIR` + `market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv` 组成
  - `DATA_DIR` 默认值来自配置，未设置环境变量时是相对路径 `./data`，依赖当前工作目录 (CWD)
  - 当从 `backend` 目录启动时，`./data` 解析为 `backend/data`，导致找不到项目根部的 `data/`

### 影响
- 仅影响离线工具路径 (`get_YFin_data`、`get_stockstats_indicators_report` 的离线分支)。
- 在线工具 `get_YFin_data_online` 不受影响。

### 修复方案（三选一，推荐优先级从上到下）
1) 配置绝对路径（推荐，零代码改动）
   - 在项目 `.env` 或运行环境中设置：
     - `TRADINGAGENTS_DATA_DIR=/Users/robin/VSCode/BigA/TradingAgents-CN/data`
     - 可选：`TRADINGAGENTS_CACHE_DIR=/Users/robin/VSCode/BigA/TradingAgents-CN/data/cache`
   - 重启服务后，`DATA_DIR` 将不再依赖 CWD。

2) 调整工具选择逻辑（快速规避）
   - 让市场数据默认优先使用在线工具 `get_YFin_data_online`（已有兜底逻辑），离线作为最后备选。
   - 适合无离线 CSV 的环境；但不解决根因。

3) 改进默认配置（代码层面）
   - 在 `tradingagents/dataflows/config.py` 将默认 `DATA_DIR` 从相对路径改为基于仓库根目录的绝对路径（例如通过 `Path(__file__).resolve().parents[2] / 'data'` 计算）。
   - 保持对 `TRADINGAGENTS_DATA_DIR` 环境变量的优先级。

### 需要同步的检查
- 确认实际符号命名：文件名会包含 `symbol`（例如 `600580.SS`），确保离线 CSV 文件存在于：
  - `${TRADINGAGENTS_DATA_DIR}/market_data/price_data/`
  - 文件名形如：`{symbol}-YFin-data-2015-01-01-2025-03-25.csv`

### 建议执行
- 立刻采用方案 (1)：设置绝对路径环境变量并重启。
- 若仍需：后续再做方案 (3) 的代码强化，彻底消除 CWD 依赖。

### 状态
- 记录创建，等待执行方案 (1) 并验证日志无报错。


