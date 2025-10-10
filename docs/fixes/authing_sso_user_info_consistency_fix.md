# Authing SSO 用户信息一致性修复报告

## 问题描述

在使用 Authing SSO 登录后，获取的用户信息每次都不一样，导致用户体验不稳定。

## 问题分析

### 根本原因
1. **缺失的 Authing 管理器**：`web/utils/authing_manager.py` 文件不存在，导致 SSO 登录功能无法正常工作
2. **用户信息提取逻辑不稳定**：在 `tradingagents_server.py` 中使用 `or` 操作符提取用户名，如果 Authing 返回的字段不稳定或为空，就会导致每次获取到不同的值
3. **Scope 配置不完整**：只请求了 `openid profile email`，没有请求完整的用户信息字段

### 技术细节
- 原始代码：`user_info.get("preferred_username") or user_info.get("username") or user_info.get("sub")`
- 问题：如果 `preferred_username` 和 `username` 字段不稳定，就会回退到 `sub`，导致用户名不一致
- Scope 限制：只请求了基本字段，缺少 `phone`, `username`, `roles`, `unionid`, `external_id`, `extended_fields` 等

## 解决方案

### 1. 创建 Authing 管理器
创建了 `web/utils/authing_manager.py` 文件，包含：
- 完整的 Authing SSO 登录流程
- 标准化的用户信息提取逻辑
- 错误处理和日志记录
- 配置验证功能

### 2. 标准化用户信息提取
实现了 `_standardize_user_info` 方法：
```python
def _standardize_user_info(self, user_info: Dict) -> Dict:
    # 使用 sub 作为唯一标识符，确保一致性
    sub = user_info.get("sub")
    
    # 用户名优先级：preferred_username > username > sub
    username = (
        user_info.get("preferred_username") or 
        user_info.get("username") or 
        sub
    )
    
    # 显示名称优先级：name > nickname > username
    display_name = (
        user_info.get("name") or 
        user_info.get("nickname") or 
        username
    )
    
    # 邮箱处理
    email = user_info.get("email")
    if not email:
        email = f"{username}@authing.demo"
```

### 3. 完善 Scope 配置
更新了所有登录页面的 scope 配置：
```javascript
const scope = 'openid profile email phone username roles unionid external_id extended_fields';
```

### 4. 修复后端用户信息处理
更新了 `tradingagents_server.py` 中的用户信息提取逻辑：
- 使用标准化的字段提取
- 添加了 `sub` 作为唯一标识符
- 增加了 `auth_type` 和 `auth_provider` 字段
- 保留了原始用户信息用于调试

## 修改的文件

1. **新增文件**：
   - `web/utils/authing_manager.py` - Authing SSO 管理器

2. **修改文件**：
   - `tradingagents_server.py` - 修复用户信息提取逻辑
   - `frontend/src/pages/Login/index.tsx` - 更新 scope 配置
   - `login_test.html` - 更新 scope 配置

## 环境变量配置

需要设置以下环境变量：
```bash
AUTHING_APP_ID=your_app_id
AUTHING_APP_SECRET=your_app_secret
AUTHING_APP_HOST=https://your-domain.authing.cn
AUTHING_REDIRECT_URI=http://localhost:3000/auth/callback
```

## 测试建议

1. **功能测试**：
   - 测试 SSO 登录流程
   - 验证用户信息一致性
   - 检查错误处理

2. **一致性测试**：
   - 多次登录同一用户，验证用户信息是否一致
   - 检查用户名、邮箱、显示名称等字段的稳定性

3. **Scope 测试**：
   - 验证是否获取到完整的用户信息
   - 检查角色、扩展字段等是否正确获取

## 预期效果

修复后，Authing SSO 登录应该能够：
1. 稳定获取用户信息，每次登录返回相同的用户数据
2. 支持完整的用户信息字段（角色、扩展字段等）
3. 提供更好的错误处理和日志记录
4. 确保用户体验的一致性

## 注意事项

1. 确保 Authing 应用配置正确，特别是回调地址
2. 检查 Authing 用户池中的用户信息是否完整
3. 如果仍有问题，可以查看日志中的 `raw_user_info` 字段进行调试
4. 建议在生产环境中使用真实的数据库存储用户信息，而不是模拟数据库

## 相关文档

- [Authing OIDC 文档](https://docs.authing.cn/v2/concepts/oidc/)
- [Authing Scope 配置](https://docs.authing.cn/v2/concepts/oidc/oidc-overview.html#scope)
- [项目认证系统文档](../architecture/authentication.md)
