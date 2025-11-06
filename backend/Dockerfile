# TradingAgents Backend Service
FROM python:3.10-slim-bookworm

# 安装 uv（多镜像源回退，避免某些镜像未同步导致失败）
RUN set -eux; \
    for src in \
        https://pypi.tuna.tsinghua.edu.cn/simple \
        https://pypi.org/simple \
        https://mirrors.aliyun.com/pypi/simple; do \
      echo "Installing uv from $src"; \
      python -m pip install --no-cache-dir -i "$src" uv && break || echo "uv not available on $src"; \
    done

WORKDIR /app

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/cache /app/results

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 删除自定义APT镜像配置与系统包安装，避免GPG签名问题；
# Python依赖使用预编译轮子，无需额外系统库。

# 复制依赖文件与锁文件（优先使用锁文件确保版本一致）
COPY pyproject.toml ./
COPY uv.lock ./
COPY backend/requirements.txt ./backend/requirements.txt

# 优先使用 uv sync --frozen（按锁文件安装）。若失败则回退到 requirements 多源安装。
RUN set -e; \
    echo "Attempting uv sync --frozen using mirrors..."; \
    synced=false; \
    for idx in \
        https://mirrors.aliyun.com/pypi/simple \
        https://pypi.tuna.tsinghua.edu.cn/simple \
        https://pypi.org/simple; do \
      echo "Trying uv sync with index: $idx"; \
      if UV_INDEX_URL=$idx uv sync --frozen --system --no-dev; then \
        echo "uv sync succeeded with $idx"; \
        synced=true; \
        break; \
      else \
        echo "uv sync failed with $idx, trying next"; \
      fi; \
    done; \
    if [ "$synced" = "false" ]; then \
      echo "Falling back to uv pip install -r backend/requirements.txt"; \
      installed=false; \
      for src in \
          https://mirrors.aliyun.com/pypi/simple \
          https://pypi.tuna.tsinghua.edu.cn/simple \
          https://pypi.doubanio.com/simple \
          https://pypi.org/simple; do \
        echo "Try installing from $src"; \
        if uv pip install --system --no-cache -r backend/requirements.txt -i $src; then \
          echo "Backend requirements installed from $src"; \
          installed=true; \
          break; \
        fi; \
        echo "Failed at $src, try next"; \
      done; \
      if [ "$installed" = "false" ]; then \
        echo "Failed to install dependencies from all sources"; \
        exit 1; \
      fi; \
    fi

# 强制从 PyPI 官方源校正 LangGraph 相关包，避免镜像源残缺导致 _internal 缺失
RUN set -eux; \
    uv pip install --system --no-cache \
      'langgraph==0.4.8' \
      'langgraph-prebuilt==0.2.2' \
      'langgraph-checkpoint==2.0.26' \
      'langgraph-sdk==0.1.70' \
      -i https://pypi.org/simple

# 复制tradingagents模块（共享模块）
COPY tradingagents/ ./tradingagents/

# 复制backend代码
COPY backend/ ./backend/

# 复制配置文件
COPY .env* ./

# 暴露端口
EXPOSE 8000

# 健康检查（使用 Python 单行脚本，无需外部依赖）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://localhost:8000/health', timeout=8)"]

# 启动应用
CMD ["python", "backend/tradingagents_server.py"]
