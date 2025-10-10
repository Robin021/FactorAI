# Authing SSO 配置问题解决方案

## 当前问题分析

1. **环境变量未设置**：导致 Authing 配置为空
2. **Authing 应用配置问题**：当前使用的域名可能不正确
3. **回调地址不匹配**：需要确保 Authing 控制台配置正确

## 解决方案

### 方案一：使用正确的 Authing 配置

如果你有 Authing 账号，请按以下步骤配置：

1. **登录 Authing 控制台**
   - 访问：https://console.authing.cn
   - 使用你的账号登录

2. **创建或配置应用**
   - 进入"应用管理"
   - 创建新应用或使用现有应用
   - 选择"单点登录 SSO" 类型

3. **获取配置信息**
   ```bash
   # 应用 ID（App ID）
   AUTHING_APP_ID=你的应用ID
   
   # 应用密钥（App Secret）
   AUTHING_APP_SECRET=你的应用密钥
   
   # 应用域名（App Host）
   AUTHING_APP_HOST=https://你的域名.authing.cn
   
   # 回调地址
   AUTHING_REDIRECT_URI=http://localhost:3000/auth/callback
   ```

4. **配置回调地址**
   - 在 Authing 控制台中添加回调地址：
   - `http://localhost:3000/auth/callback`

### 方案二：使用模拟 SSO（用于测试）

如果暂时无法配置真实的 Authing，可以使用模拟 SSO 进行测试：

```python
# 在 tradingagents_server.py 中添加模拟模式
MOCK_AUTHING = True  # 设置为 True 启用模拟模式

if MOCK_AUTHING:
    # 使用模拟的 Authing 响应
    mock_user_info = {
        "sub": f"mock_user_{code[:8]}",
        "username": f"mock_user_{code[:8]}",
        "display_name": "模拟用户",
        "email": f"mock_{code[:8]}@example.com",
        "phone": "",
        "avatar": "",
        "roles": ["user"],
        "extended_fields": {}
    }
```

### 方案三：修复当前配置

基于当前代码中的配置，让我创建一个修复版本：

```bash
# 更新环境变量
export AUTHING_APP_ID="68d3879e03d9b1907f220731"
export AUTHING_APP_SECRET="请填写正确的密钥"
export AUTHING_APP_HOST="https://sxkc6t59wbj9-demo.authing.cn"
export AUTHING_REDIRECT_URI="http://localhost:3000/auth/callback"
```

## 测试步骤

### 1. 验证 Authing 配置
```bash
# 检查配置端点
curl "https://sxkc6t59wbj9-demo.authing.cn/.well-known/openid_configuration"

# 如果返回 404，说明域名不正确
```

### 2. 测试回调地址
```bash
# 启动服务
python tradingagents_server.py

# 在另一个终端测试回调地址
curl "http://localhost:3000/auth/callback?code=test&state=test"
```

### 3. 检查日志
查看服务器日志中的 Authing 相关错误信息。

## 常见问题解决

### 1. redirect_uri_mismatch
- **原因**：回调地址不匹配
- **解决**：确保 Authing 控制台中的回调地址与代码中完全一致

### 2. invalid_client
- **原因**：应用 ID 或密钥错误
- **解决**：检查 Authing 控制台中的应用配置

### 3. 环境变量未加载
- **原因**：.env 文件未正确加载
- **解决**：使用 `source .env` 或安装 `python-dotenv`

## 推荐做法

1. **使用真实的 Authing 应用**：注册 Authing 账号，创建应用
2. **正确配置回调地址**：确保与 Authing 控制台配置一致
3. **使用环境变量**：不要硬编码敏感信息
4. **添加错误处理**：处理各种 Authing API 错误

## 下一步

请选择以下方案之一：

1. **配置真实的 Authing 应用**：提供正确的应用配置信息
2. **使用模拟 SSO**：修改代码使用模拟数据
3. **调试当前配置**：检查现有配置的问题

你希望采用哪种方案？
