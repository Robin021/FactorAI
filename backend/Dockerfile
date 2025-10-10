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

# 配置阿里云镜像源
RUN echo 'deb http://mirrors.aliyun.com/debian/ bookworm main' > /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian/ bookworm main' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian/ bookworm-updates main' >> /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian/ bookworm-updates main' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian-security bookworm-security main' >> /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian-security bookworm-security main' >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件（从项目根目录）
COPY requirements.txt pyproject.toml ./

# 多源轮询安装Python依赖
RUN set -e; \
    for src in \
        https://mirrors.aliyun.com/pypi/simple \
        https://pypi.tuna.tsinghua.edu.cn/simple \
        https://pypi.doubanio.com/simple \
        https://pypi.org/simple; do \
      echo "Try installing from $src"; \
      uv pip install --system --no-cache -e . -i $src && break; \
      echo "Failed at $src, try next"; \
    done

# 复制tradingagents模块（共享模块）
COPY tradingagents/ ./tradingagents/

# 复制backend代码
COPY backend/ ./backend/

# 复制配置文件
COPY .env* ./

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["python", "backend/tradingagents_server.py"]
