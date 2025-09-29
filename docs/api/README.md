# API 接口文档

## 概述

本文档描述了股票分析平台的 RESTful API 接口。API 基于 FastAPI 框架构建，提供 JSON 格式的数据交换，支持 OpenAPI 3.0 规范。

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 获取访问令牌

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**响应示例:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 使用访问令牌

在所有需要认证的请求中，在 Header 中包含访问令牌：

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## API 接口

### 认证相关 API

#### 用户登录
```http
POST /api/v1/auth/login
```

**请求参数:**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "string"
}
```

#### 用户登出
```http
POST /api/v1/auth/logout
Authorization: Bearer {token}
```

**响应:**
```json
{
  "message": "Successfully logged out"
}
```

#### 获取用户信息
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

**响应:**
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "role": "admin|user|viewer",
  "permissions": ["string"],
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

#### 刷新令牌
```http
POST /api/v1/auth/refresh
```

**请求参数:**
```json
{
  "refresh_token": "string"
}
```

### 分析相关 API

#### 开始股票分析
```http
POST /api/v1/analysis/start
Authorization: Bearer {token}
Content-Type: application/json
```

**请求参数:**
```json
{
  "stock_code": "000001",
  "market_type": "A股",
  "analysis_date": "2024-01-01",
  "analysts": ["fundamentals", "technical", "news"],
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

**响应:**
```json
{
  "analysis_id": "string",
  "status": "pending",
  "message": "Analysis started successfully"
}
```

#### 获取分析状态
```http
GET /api/v1/analysis/{analysis_id}/status
Authorization: Bearer {token}
```

**响应:**
```json
{
  "id": "string",
  "status": "pending|running|completed|failed",
  "progress": 0.75,
  "current_step": "正在进行技术分析...",
  "created_at": "2024-01-01T00:00:00Z",
  "started_at": "2024-01-01T00:00:00Z",
  "estimated_completion": "2024-01-01T00:05:00Z"
}
```

#### 获取分析结果
```http
GET /api/v1/analysis/{analysis_id}/result
Authorization: Bearer {token}
```

**响应:**
```json
{
  "id": "string",
  "stock_code": "000001",
  "status": "completed",
  "result_data": {
    "fundamentals": {
      "score": 85,
      "analysis": "基本面分析结果...",
      "metrics": {
        "pe_ratio": 15.2,
        "pb_ratio": 1.8,
        "roe": 0.15
      }
    },
    "technical": {
      "score": 78,
      "analysis": "技术分析结果...",
      "indicators": {
        "ma5": 12.5,
        "ma20": 12.8,
        "rsi": 65.2
      }
    },
    "news": {
      "score": 72,
      "analysis": "新闻分析结果...",
      "sentiment": "positive"
    }
  },
  "completed_at": "2024-01-01T00:05:00Z"
}
```

#### 获取分析历史
```http
GET /api/v1/analysis/history?page=1&size=10&stock_code=000001
Authorization: Bearer {token}
```

**查询参数:**
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| size | integer | 否 | 每页数量，默认 10 |
| stock_code | string | 否 | 股票代码过滤 |
| status | string | 否 | 状态过滤 |

**响应:**
```json
{
  "items": [
    {
      "id": "string",
      "stock_code": "000001",
      "status": "completed",
      "progress": 1.0,
      "created_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:05:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

#### 删除分析记录
```http
DELETE /api/v1/analysis/{analysis_id}
Authorization: Bearer {token}
```

**响应:**
```json
{
  "message": "Analysis deleted successfully"
}
```

### 配置相关 API

#### 获取 LLM 配置
```http
GET /api/v1/config/llm
Authorization: Bearer {token}
```

**响应:**
```json
{
  "providers": {
    "openai": {
      "api_key": "sk-***",
      "base_url": "https://api.openai.com/v1",
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "default_model": "gpt-4"
    },
    "deepseek": {
      "api_key": "sk-***",
      "base_url": "https://api.deepseek.com/v1",
      "models": ["deepseek-chat", "deepseek-coder"],
      "default_model": "deepseek-chat"
    }
  },
  "default_provider": "openai"
}
```

#### 更新 LLM 配置
```http
PUT /api/v1/config/llm
Authorization: Bearer {token}
Content-Type: application/json
```

**请求参数:**
```json
{
  "provider": "openai",
  "api_key": "sk-new-api-key",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

#### 获取数据源配置
```http
GET /api/v1/config/data-sources
Authorization: Bearer {token}
```

**响应:**
```json
{
  "sources": {
    "tushare": {
      "enabled": true,
      "priority": 1,
      "api_key": "***",
      "rate_limit": 200
    },
    "akshare": {
      "enabled": true,
      "priority": 2,
      "rate_limit": 100
    },
    "finnhub": {
      "enabled": false,
      "priority": 3,
      "api_key": "***"
    }
  },
  "cache_settings": {
    "enabled": true,
    "ttl": 3600,
    "max_size": "1GB"
  }
}
```

#### 更新数据源配置
```http
PUT /api/v1/config/data-sources
Authorization: Bearer {token}
Content-Type: application/json
```

**请求参数:**
```json
{
  "source": "tushare",
  "enabled": true,
  "priority": 1,
  "api_key": "new-api-key",
  "rate_limit": 200
}
```

## WebSocket 接口

### 分析进度推送

连接到 WebSocket 端点以接收实时分析进度：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analysis/{analysis_id}?token={jwt_token}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Progress update:', data);
};
```

**消息格式:**
```json
{
  "type": "progress",
  "analysis_id": "string",
  "progress": 0.75,
  "status": "running",
  "current_step": "正在进行技术分析...",
  "message": "已完成 3/4 个分析师",
  "timestamp": "2024-01-01T00:03:00Z"
}
```

### 系统通知推送

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/notifications?token={jwt_token}');

ws.onmessage = function(event) {
  const notification = JSON.parse(event.data);
  console.log('Notification:', notification);
};
```

**消息格式:**
```json
{
  "type": "notification",
  "level": "info|warning|error",
  "title": "系统通知",
  "message": "您的分析已完成",
  "data": {
    "analysis_id": "string"
  },
  "timestamp": "2024-01-01T00:05:00Z"
}
```

## 错误处理

### HTTP 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 429 | 请求频率限制 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "error": "Validation Error",
  "message": "请求参数验证失败",
  "details": [
    {
      "field": "stock_code",
      "message": "股票代码格式不正确"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "string"
}
```

## 使用示例

### Python 客户端示例

```python
import requests
import json

class StockAnalysisClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        """用户登录"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            return True
        return False
    
    def get_headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def start_analysis(self, stock_code, analysts=None):
        """开始股票分析"""
        if analysts is None:
            analysts = ["fundamentals", "technical", "news"]
        
        data = {
            "stock_code": stock_code,
            "market_type": "A股",
            "analysts": analysts
        }
        
        response = requests.post(
            f"{self.base_url}/analysis/start",
            json=data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            return response.json()["analysis_id"]
        return None
    
    def get_analysis_result(self, analysis_id):
        """获取分析结果"""
        response = requests.get(
            f"{self.base_url}/analysis/{analysis_id}/result",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            return response.json()
        return None

# 使用示例
client = StockAnalysisClient()
if client.login("admin", "password"):
    analysis_id = client.start_analysis("000001")
    if analysis_id:
        result = client.get_analysis_result(analysis_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
```

### JavaScript 客户端示例

```javascript
class StockAnalysisAPI {
  constructor(baseURL = 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
      localStorage.setItem('access_token', this.token);
      return true;
    }
    return false;
  }

  getHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    };
  }

  async startAnalysis(stockCode, analysts = ['fundamentals', 'technical', 'news']) {
    const response = await fetch(`${this.baseURL}/analysis/start`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        stock_code: stockCode,
        market_type: 'A股',
        analysts: analysts,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      return data.analysis_id;
    }
    return null;
  }

  async getAnalysisStatus(analysisId) {
    const response = await fetch(`${this.baseURL}/analysis/${analysisId}/status`, {
      headers: this.getHeaders(),
    });

    if (response.ok) {
      return await response.json();
    }
    return null;
  }

  connectWebSocket(analysisId, onMessage) {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/analysis/${analysisId}?token=${this.token}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }
}

// 使用示例
const api = new StockAnalysisAPI();

async function analyzeStock() {
  if (await api.login('admin', 'password')) {
    const analysisId = await api.startAnalysis('000001');
    
    if (analysisId) {
      // 连接 WebSocket 监听进度
      const ws = api.connectWebSocket(analysisId, (data) => {
        console.log('Progress:', data.progress);
        console.log('Step:', data.current_step);
        
        if (data.status === 'completed') {
          ws.close();
          console.log('Analysis completed!');
        }
      });
    }
  }
}
```

## 速率限制

API 实施了速率限制以防止滥用：

- **认证接口**: 每分钟 10 次请求
- **分析接口**: 每分钟 5 次分析请求
- **查询接口**: 每分钟 100 次请求
- **配置接口**: 每分钟 20 次请求

超出限制时将返回 429 状态码。

## 版本控制

API 使用 URL 路径进行版本控制：
- 当前版本: `/api/v1/`
- 未来版本: `/api/v2/`

向后兼容性将在主要版本之间维护。