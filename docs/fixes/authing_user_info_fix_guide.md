# Authing 用户信息获取问题修复指南

## 🎯 问题描述

Authing 登录后获取的用户信息是随机的，无法获取到真实的用户手机号或邮箱。

## 🔍 问题根本原因

经过分析，问题的根本原因是：

1. **环境变量未正确设置**：`AUTHING_APP_SECRET` 还是占位符 `"your_app_secret_here"`
2. **Authing API 调用失败**：由于密钥不正确，导致无法从 Authing 获取真实用户信息
3. **代码逻辑正确**：`tradingagents_server.py` 中的代码逻辑是正确的，失败时会返回错误页面

## 🛠️ 修复步骤

### 步骤 1: 获取 Authing 应用密钥

1. **登录 Authing 控制台**
   ```
   https://console.authing.cn
   ```

2. **进入应用管理**
   - 找到应用 ID：`68d3879e03d9b1907f220731`
   - 点击进入应用详情

3. **获取应用密钥**
   - 在应用详情页面找到"应用密钥"或"App Secret"
   - 复制密钥值（通常是一串字母数字组合）

### 步骤 2: 设置环境变量

使用新的环境变量设置脚本：

```bash
# 给脚本执行权限
chmod +x setup_authing_env_fixed.sh

# 设置环境变量（替换为你的实际密钥）
./setup_authing_env_fixed.sh your_actual_app_secret_here
```

### 步骤 3: 检查 Authing 用户池

1. **进入用户管理**
   - 在 Authing 控制台点击"用户管理"

2. **创建测试用户**（如果没有用户）
   - 点击"添加用户"
   - 填写用户信息：
     - 用户名：`testuser`
     - 邮箱：`test@example.com`
     - 手机号：`13800138000`
     - 密码：`Test123456`
   - 确保用户状态为"已激活"

3. **检查用户信息完整性**
   - 确保用户填写了邮箱和手机号
   - 检查用户角色和权限配置

### 步骤 4: 测试修复结果

1. **启动服务**
   ```bash
   python tradingagents_server.py
   ```

2. **测试 SSO 登录**
   - 访问 http://localhost:3000/login
   - 点击 "Authing SSO 登录" 按钮
   - 使用创建的测试用户登录

3. **验证用户信息**
   - 登录成功后应该显示真实的用户信息
   - 检查用户名、邮箱、手机号是否正确

## 🔧 代码修复说明

### 主要修复点

1. **环境变量设置脚本**：创建了 `setup_authing_env_fixed.sh`，支持传入实际的应用密钥

2. **错误处理优化**：确保 Authing API 调用失败时返回明确的错误信息，而不是模拟数据

3. **用户信息标准化**：使用 `web/utils/authing_manager.py` 中的标准化逻辑确保用户信息一致性

### 关键代码逻辑

```python
# 在 tradingagents_server.py 中
try:
    # 调用 Authing API 获取真实用户信息
    token_info = self._exchange_code_for_token(code)
    user_info = self._get_user_info(access_token)
    
    # 标准化用户信息
    standardized_user_info = self._standardize_user_info(user_info)
    
except Exception as e:
    # 返回错误页面，不使用模拟数据
    logger.error(f"Authing API调用失败: {e}")
    return HTMLResponse(content=error_html)
```

## 📋 测试清单

- [ ] Authing 应用密钥已正确设置
- [ ] 环境变量已加载
- [ ] Authing 用户池中有测试用户
- [ ] 测试用户信息完整（邮箱、手机号）
- [ ] 回调地址配置正确
- [ ] 能够成功登录 Authing
- [ ] 获取到真实的用户信息
- [ ] 前端显示正确的用户信息

## 🚨 常见问题解决

### 1. 应用密钥错误
**症状**：`invalid_client` 错误
**解决**：检查 Authing 控制台中的应用密钥是否正确

### 2. 用户不存在
**症状**：登录时提示用户不存在
**解决**：在 Authing 控制台创建用户

### 3. 用户信息不完整
**症状**：获取到的邮箱或手机号为空
**解决**：确保 Authing 用户信息完整填写

### 4. 回调地址不匹配
**症状**：`redirect_uri_mismatch` 错误
**解决**：确保 Authing 控制台中的回调地址与代码中完全一致

## 🎯 预期结果

修复后，Authing SSO 登录应该能够：

1. ✅ 成功跳转到 Authing 登录页面
2. ✅ 使用真实用户登录成功
3. ✅ 获取到真实的用户信息（用户名、邮箱、手机号）
4. ✅ 在前端显示正确的用户信息
5. ✅ 用户信息保持一致，不会随机变化

### 🔧 用户信息处理改进

针对用户信息不完整的情况（如只有手机号，其他字段为空），系统现在会：

- **用户名**：优先使用 `preferred_username` > `username` > `phone_number` > `sub`
- **显示名称**：优先使用 `name` > `nickname` > `phone_number` > `username`
- **邮箱**：如果为空，使用手机号生成 `{phone_number}@authing.demo`

**示例**：
- 原始信息：`phone_number: "13391398973"`, `email: null`, `username: null`
- 处理后：`username: "13391398973"`, `email: "13391398973@authing.demo"`

## 📝 相关文件

- `setup_authing_env_fixed.sh` - 修复版环境变量设置脚本
- `web/utils/authing_manager.py` - Authing SSO 管理器
- `tradingagents_server.py` - 主服务器文件
- `frontend/src/pages/Login/index.tsx` - 前端登录页面

## 🔗 相关文档

- [Authing OIDC 文档](https://docs.authing.cn/v2/concepts/oidc/)
- [Authing Scope 配置](https://docs.authing.cn/v2/concepts/oidc/oidc-overview.html#scope)
- [项目认证系统文档](../architecture/authentication.md)
