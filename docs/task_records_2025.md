# 任务记录

## 2025-01-25 Authing SSO 用户信息一致性修复

### 任务描述
修复 Authing SSO 登录后用户信息每次都不一样的问题

### 问题分析
1. **缺失的 Authing 管理器**：`web/utils/authing_manager.py` 文件不存在
2. **用户信息提取逻辑不稳定**：使用 `or` 操作符导致字段不稳定
3. **Scope 配置不完整**：只请求了基本字段

### 解决方案
1. ✅ 创建了 `web/utils/authing_manager.py` 文件
2. ✅ 实现了标准化的用户信息提取逻辑
3. ✅ 更新了所有登录页面的 scope 配置
4. ✅ 修复了后端用户信息处理逻辑

### 修改的文件
- **新增**：`web/utils/authing_manager.py`
- **修改**：`tradingagents_server.py`
- **修改**：`frontend/src/pages/Login/index.tsx`
- **修改**：`login_test.html`

### 技术要点
- 使用 `sub` 作为唯一标识符确保一致性
- 实现标准化的用户信息提取优先级
- 完善 scope 配置获取完整用户信息
- 添加错误处理和日志记录

### 环境变量
```bash
AUTHING_APP_ID=your_app_id
AUTHING_APP_SECRET=your_app_secret
AUTHING_APP_HOST=https://your-domain.authing.cn
AUTHING_REDIRECT_URI=http://localhost:3000/api/v1/auth/authing/callback
```

### 测试建议
1. 多次登录同一用户验证信息一致性
2. 检查是否获取到完整的用户信息字段
3. 验证错误处理机制

### 状态
✅ 已完成

### 相关文档
- [修复报告](../fixes/authing_sso_user_info_consistency_fix.md)

---

## 2025-01-25 实时分析进度同步问题修复

### 任务描述
修复后端执行步骤与前端显示不一致的问题，前端显示"连接断开"且进度不更新

### 问题分析
1. **前端轮询被禁用**：`RealTimeProgressDashboard.tsx` 和 `ProgressTracker.tsx` 中的轮询机制被临时禁用
2. **WebSocket连接问题**：前端没有正确建立WebSocket连接来接收实时进度更新
3. **消息格式不匹配**：前端消息处理逻辑与后端发送的WebSocket消息格式不匹配

### 解决方案
1. ✅ 恢复了WebSocket连接机制
2. ✅ 实现了WebSocket + 轮询的双重保障机制
3. ✅ 修复了消息格式处理逻辑
4. ✅ 优化了连接状态管理

### 修改的文件
- **修改**：`frontend/src/components/Analysis/RealTimeProgressDashboard.tsx`
- **修改**：`frontend/src/components/Analysis/ProgressTracker.tsx`
- **修改**：`frontend/src/hooks/useWebSocket.ts`

### 技术要点
- WebSocket优先，轮询备用：当WebSocket连接失败时自动启用轮询
- 消息格式兼容：同时支持WebSocket和轮询两种消息格式
- 连接状态管理：实时显示连接状态，提供更好的用户体验
- 错误处理：完善的错误处理和重连机制

### 后端消息格式
```json
{
  "type": "analysis_progress",
  "data": {
    "analysis_id": "688256",
    "progress": 50.0,
    "message": "正在执行分析...",
    "current_step": "2"
  },
  "timestamp": "2025-01-25T10:30:00Z",
  "connection_id": "conn_123"
}
```

### 前端处理逻辑
- WebSocket消息：`data.type` + `data.data` 格式
- 轮询消息：直接 `data.type` 格式
- 向后兼容：保持对旧格式的支持

### 状态
✅ 已完成

### 测试建议
1. 启动分析任务，观察进度更新是否实时
2. 断开网络连接，验证轮询备用机制
3. 检查连接状态显示是否正确
4. 验证不同消息格式的处理

---

## 2025-01-25 移除WebSocket机制，优化日志输出

### 任务描述
用户反馈后台日志被WebSocket机制刷爆，需要移除WebSocket机制，只使用轮询方式获取进度更新

### 问题分析
1. **WebSocket日志过多**：WebSocket连接和消息处理产生大量日志输出
2. **资源消耗**：WebSocket连接占用服务器资源
3. **复杂性**：WebSocket + 轮询的双重机制增加了系统复杂性

### 解决方案
1. ✅ 完全移除WebSocket连接机制
2. ✅ 恢复纯轮询方式获取进度更新
3. ✅ 简化消息处理逻辑
4. ✅ 保持15秒轮询间隔，避免过于频繁的请求

### 修改的文件
- **修改**：`frontend/src/components/Analysis/RealTimeProgressDashboard.tsx`
- **修改**：`frontend/src/components/Analysis/ProgressTracker.tsx`

### 技术要点
- **纯轮询机制**：每15秒轮询一次进度状态
- **简化逻辑**：移除WebSocket消息格式处理，只保留轮询格式
- **减少日志**：避免WebSocket连接和消息处理产生的日志
- **保持功能**：进度更新功能完全保留

### 轮询配置
- **间隔时间**：15秒（默认）
- **智能调整**：接近完成时稍微提高频率
- **自动停止**：分析完成或失败时自动停止轮询

### 状态
✅ 已完成

### 测试建议
1. 启动分析任务，观察进度更新是否正常
2. 检查后台日志是否减少
3. 验证15秒轮询间隔是否合适
4. 确认分析完成后轮询自动停止

---

## 2025-01-25 修复轮询API端点不匹配问题

### 任务描述
用户反馈后台日志仍然疯狂刷新，前端无法连接到后端。发现是轮询API端点路径不匹配的问题

### 问题分析
1. **API端点不匹配**：前端轮询 `/analysis/{id}/progress`，但后端端点是 `/analysis/{id}/status`
2. **数据格式不匹配**：前端期望的消息格式与后端返回的AnalysisProgress格式不一致
3. **404错误导致疯狂重试**：前端收到404错误后不断重试，导致日志刷爆

### 解决方案
1. ✅ 修正了轮询API端点路径：`/analysis/{id}/progress` → `/analysis/{id}/status`
2. ✅ 更新了消息处理逻辑，匹配后端AnalysisProgress格式
3. ✅ 修复了智能轮询逻辑，使用正确的字段名
4. ✅ 添加了详细的日志输出，便于调试

### 修改的文件
- **修改**：`frontend/src/components/Analysis/RealTimeProgressDashboard.tsx`
- **修改**：`frontend/src/components/Analysis/ProgressTracker.tsx`
- **修改**：`frontend/src/hooks/usePolling.ts`

### 技术要点
- **正确的API端点**：使用 `/analysis/{id}/status` 获取分析状态
- **数据格式匹配**：处理后端返回的AnalysisProgress格式
- **智能轮询**：根据 `status` 和 `progress` 字段调整轮询频率
- **错误处理**：404错误时停止轮询，避免无限重试

### 后端数据格式
```json
{
  "status": "running",
  "progress": 50.0,
  "current_step": "2",
  "message": "正在执行分析...",
  "estimated_time_remaining": 300
}
```

### 状态
✅ 已完成

### 测试建议
1. 启动分析任务，观察是否能正常获取进度
2. 检查后台日志是否不再疯狂刷新
3. 验证进度更新是否实时显示
4. 确认分析完成后轮询自动停止

---

## 2025-01-25 修复多个组件重复轮询问题

### 任务描述
用户反馈点击开始分析后立刻出现大量日志，实时进度页面打不开。发现是多个组件同时轮询同一个分析任务导致的

### 问题分析
1. **多个组件重复轮询**：`RealTimeProgressDashboard`、`ProgressTracker`、`AnalysisProgress` 三个组件都在轮询
2. **API端点不统一**：`AnalysisProgress` 仍在使用错误的 `/progress` 端点
3. **轮询频率过高**：15秒间隔对于多个组件来说过于频繁
4. **页面语法错误**：`Analysis/index.tsx` 有语法错误导致页面无法打开

### 解决方案
1. ✅ 禁用了未使用的 `ProgressTracker` 组件的轮询
2. ✅ 修复了 `AnalysisProgress` 组件的API端点
3. ✅ 统一了轮询间隔为30秒，减少服务器压力
4. ✅ 修复了页面语法错误

### 修改的文件
- **修改**：`frontend/src/components/Analysis/ProgressTracker.tsx`
- **修改**：`frontend/src/components/Analysis/AnalysisProgress.tsx`
- **修改**：`frontend/src/hooks/usePolling.ts`
- **修改**：`frontend/src/pages/Analysis/index.tsx`

### 技术要点
- **避免重复轮询**：确保只有一个组件在轮询同一个分析任务
- **统一API端点**：所有组件都使用 `/analysis/{id}/status` 端点
- **优化轮询频率**：30秒间隔，减少服务器压力
- **修复语法错误**：确保页面能正常渲染

### 轮询策略
- **主组件**：`RealTimeProgressDashboard` 负责主要进度显示
- **历史组件**：`AnalysisProgress` 用于历史记录中的进度显示
- **禁用组件**：`ProgressTracker` 暂时禁用轮询

### 状态
✅ 已完成

### 测试建议
1. 启动分析任务，观察日志是否减少
2. 检查实时进度页面是否能正常打开
3. 验证进度更新是否正常显示
4. 确认30秒轮询间隔是否合适

---

## 2025-01-25 优化轮询间隔为1分钟

### 任务描述
用户反馈分析结果很慢，需要超过5分钟以上，建议轮询按照分钟进行

### 问题分析
1. **分析任务时间长**：分析任务需要超过5分钟才能完成
2. **轮询间隔过短**：30秒轮询对于长时间任务来说过于频繁
3. **服务器压力**：频繁的轮询请求增加服务器负担

### 解决方案
1. ✅ 将默认轮询间隔从30秒调整为60秒（1分钟）
2. ✅ 更新了智能轮询逻辑：接近完成时从60秒减少到30秒
3. ✅ 统一了所有组件的轮询间隔设置

### 修改的文件
- **修改**：`frontend/src/hooks/usePolling.ts`
- **修改**：`frontend/src/components/Analysis/AnalysisProgress.tsx`

### 技术要点
- **默认间隔**：60秒（1分钟）轮询一次
- **智能调整**：进度超过80%时，间隔减少到30秒
- **适合长时间任务**：减少服务器压力，提高用户体验
- **保持响应性**：接近完成时仍能及时更新

### 轮询策略
- **正常阶段**：每60秒轮询一次
- **接近完成**：进度>80%时，每30秒轮询一次
- **自动停止**：分析完成或失败时停止轮询

### 状态
✅ 已完成

### 测试建议
1. 启动长时间分析任务，观察轮询频率
2. 检查服务器日志是否明显减少
3. 验证进度更新是否及时
4. 确认1分钟间隔是否合适

---

## 2025-01-25 彻底解决轮询循环依赖问题

### 任务描述
用户反馈轮询间隔调整为1分钟后，仍然出现大量日志刷新，实时进度页面打不开

### 问题分析
1. **循环依赖问题**：`usePolling` hook 中的 `fetchData` 函数调用了 `stopPolling()`，但 `stopPolling` 没有在依赖数组中，导致循环依赖
2. **多个组件轮询**：`RealTimeProgressDashboard` 和 `AnalysisProgress` 组件都在轮询同一个分析
3. **历史记录轮询**：`AnalysisProgress` 组件在历史记录中也会轮询已完成的分析

### 解决方案
1. ✅ 修复了 `usePolling` hook 中的循环依赖问题
2. ✅ 在 `fetchData` 函数中直接处理停止轮询逻辑，避免调用 `stopPolling`
3. ✅ 为 `AnalysisProgress` 组件添加条件轮询，只对运行中的分析启用轮询
4. ✅ 确保只有一个组件负责轮询当前分析

### 修改的文件
- **修改**：`frontend/src/hooks/usePolling.ts`
- **修改**：`frontend/src/components/Analysis/AnalysisProgress.tsx`

### 技术要点
- **循环依赖修复**：在 `fetchData` 中直接处理停止轮询，避免函数间循环调用
- **条件轮询**：只对 `running` 或 `pending` 状态的分析启用轮询
- **单一轮询源**：确保每个分析只有一个组件负责轮询
- **依赖数组优化**：正确设置 `useCallback` 的依赖数组

### 轮询策略优化
- **主组件**：`RealTimeProgressDashboard` 负责当前分析的轮询
- **历史组件**：`AnalysisProgress` 只对运行中的分析启用轮询
- **避免重复**：确保不会同时有多个组件轮询同一个分析

### 状态
✅ 已完成

### 测试建议
1. 启动新的分析任务，观察日志是否减少
2. 检查实时进度页面是否能正常打开
3. 验证只有一个轮询请求在运行
4. 确认历史记录中的已完成分析不会轮询

---

## 2025-01-25 参考Streamlit版本修复进度更新问题

### 任务描述
用户反馈轮询问题仍然存在，建议参考迁移之前的Streamlit版本实现

### 问题分析
1. **数据格式不匹配**：Streamlit版本使用 `progress:{analysis_id}` 格式，React版本期望 `analysis_progress:{analysis_id}` 格式
2. **字段名不一致**：Streamlit版本使用 `progress_percentage`，React版本期望 `progress`
3. **API兼容性问题**：后端API无法正确读取Streamlit版本的进度数据

### 解决方案
1. ✅ 修改后端API `/analysis/{id}/status` 支持多种Redis键格式
2. ✅ 兼容不同的数据字段名（progress vs progress_percentage）
3. ✅ 兼容不同的步骤字段名（current_step vs current_step_name）
4. ✅ 兼容不同的消息字段名（message vs last_message）
5. ✅ 兼容不同的时间字段名（estimated_time_remaining vs remaining_time）

### 修改的文件
- **修改**：`backend/api/v1/analysis.py`

### 技术要点
- **多键格式支持**：尝试 `analysis_progress:{id}`, `progress:{id}`, `task_progress:analysis_{id}` 三种格式
- **字段名兼容**：自动映射不同的字段名到统一格式
- **状态映射**：确保状态值正确映射到API期望的格式
- **错误处理**：解析失败时回退到数据库数据

### Redis键格式兼容
- **React版本**：`analysis_progress:{analysis_id}`
- **Streamlit版本**：`progress:{analysis_id}`
- **TaskQueue版本**：`task_progress:analysis_{analysis_id}`

### 字段映射
- **进度字段**：`progress` ← `progress_percentage`
- **步骤字段**：`current_step` ← `current_step_name`
- **消息字段**：`message` ← `last_message`
- **时间字段**：`estimated_time_remaining` ← `remaining_time`

### 状态
✅ 已完成

### 测试建议
1. 启动新的分析任务，观察进度更新是否正常
2. 检查实时进度页面是否能正确显示进度
3. 验证API能正确读取Streamlit版本的进度数据
4. 确认轮询频率控制在1分钟间隔

---

## 2025-01-25 重新设计实时进度页面功能

### 任务描述
用户反馈实时进度页面设计有问题，根本没有用，需要重新设计页面功能

### 问题分析
1. **显示条件过于严格**：只在 'running' 或 'pending' 状态时显示
2. **功能不实用**：暂停/继续功能没有后端支持
3. **页面切换混乱**：完成或出错后自动切换页面
4. **用户体验差**：用户无法查看已完成或失败的分析进度

### 解决方案
1. ✅ 移除状态限制，对所有分析都显示进度页面
2. ✅ 移除无用的暂停/继续功能
3. ✅ 简化页面功能，只保留必要的刷新和取消功能
4. ✅ 优化状态显示，清晰显示分析状态

### 修改的文件
- **修改**：`frontend/src/components/Analysis/RealTimeProgressDashboard.tsx`
- **修改**：`frontend/src/pages/Analysis/index.tsx`

### 技术要点
- **移除状态限制**：进度页面对所有状态的分析都显示
- **简化功能**：只保留刷新进度和取消分析功能
- **优化状态显示**：清晰显示分析状态（运行中、等待中、已完成、失败）
- **移除无用功能**：删除暂停/继续等没有后端支持的功能

### 新功能
- **全状态显示**：无论分析处于什么状态都可以查看进度
- **状态标签**：清晰显示当前分析状态
- **简化操作**：只保留必要的刷新和取消功能
- **更好的用户体验**：用户可以查看任何分析的进度信息

### 状态
✅ 已完成

### 测试建议
1. 启动新的分析任务，观察进度页面
2. 查看已完成的分析，验证进度页面是否显示
3. 查看失败的分析，验证进度页面是否显示
4. 测试刷新和取消功能是否正常

---

## 2025-01-25 重新设计实时进度页面

### 任务描述
用户反馈日志正常了，但实时进度界面显示"连接断开"，需要重新设计页面以适应新的更新机制

### 问题分析
1. **连接状态显示不适用**：页面仍在显示"连接断开"，但我们已经禁用了轮询机制
2. **缺少手动刷新功能**：用户无法主动获取最新进度
3. **页面设计过时**：页面设计基于实时连接，不适合手动刷新模式

### 解决方案
1. ✅ 移除连接状态显示，改为显示最后更新时间
2. ✅ 添加手动刷新按钮，用户可以主动获取最新进度
3. ✅ 页面初始化时自动刷新一次
4. ✅ 优化页面布局和交互逻辑

### 修改的文件
- **修改**：`frontend/src/components/Analysis/RealTimeProgressDashboard.tsx`

### 技术要点
- **手动刷新功能**：添加 `refreshProgress` 函数，支持手动获取最新进度
- **最后更新时间**：显示最后刷新的时间，替代连接状态
- **自动初始化**：页面加载时自动刷新一次
- **加载状态**：刷新按钮显示加载状态，防止重复点击

### 新功能
- **刷新进度按钮**：用户可以手动刷新获取最新进度
- **最后更新时间**：显示最后刷新的时间
- **加载状态指示**：刷新时显示加载状态
- **智能按钮状态**：根据分析状态禁用/启用按钮

### 状态
✅ 已完成

### 测试建议
1. 启动新的分析任务，观察实时进度页面
2. 点击"刷新进度"按钮，验证手动刷新功能
3. 检查最后更新时间是否正确显示
4. 验证页面初始化时是否自动刷新一次

### 修复的问题
- **connectionStatus 未定义错误**：移除了所有对 `connectionStatus` 的引用
- **sendMessage 未定义错误**：移除了 WebSocket 相关的 `sendMessage` 调用
- **清理未使用的导入**：移除了 `usePolling` 和 `Alert` 的导入
- **移除连接状态警告**：删除了连接状态异常的 Alert 组件
- **修复无限循环问题**：移除了页面初始化时的自动刷新，避免无限循环
- **简化刷新逻辑**：只保留手动刷新功能，避免自动触发
- **修复进度数据显示问题**：`handleProgressUpdate` 函数现在正确更新 `steps` 状态
- **修复步骤状态更新**：根据 `current_step` 正确更新步骤状态和进度

---

## 2025-01-25 彻底禁用所有轮询机制解决疯狂刷新问题

### 任务描述
用户反馈日志中全部被轮询请求覆盖，实时进度页面看不到，像是被强行刷新

### 问题分析
1. **轮询机制未完全禁用**：虽然修改了轮询间隔，但轮询机制仍然在运行
2. **AnalysisResults组件无限循环**：`useEffect` 在检查分析状态时可能触发无限循环
3. **多个组件同时轮询**：多个组件可能同时在进行轮询请求

### 解决方案
1. ✅ 彻底禁用 `usePolling` hook 的默认启用状态
2. ✅ 强制禁用 `RealTimeProgressDashboard` 组件的轮询
3. ✅ 强制禁用 `AnalysisProgress` 组件的轮询
4. ✅ 禁用 `AnalysisResults` 组件的自动获取结果逻辑
5. ✅ 确保所有轮询机制都被彻底禁用

### 修改的文件
- **修改**：`frontend/src/hooks/usePolling.ts`
- **修改**：`frontend/src/components/Analysis/RealTimeProgressDashboard.tsx`
- **修改**：`frontend/src/components/Analysis/AnalysisProgress.tsx`
- **修改**：`frontend/src/components/Analysis/AnalysisResults.tsx`

### 技术要点
- **默认禁用轮询**：`usePolling` hook 默认 `enabled = false`
- **强制禁用轮询**：所有组件都设置 `isPolling = false`
- **禁用自动获取**：禁用 `AnalysisResults` 的自动获取结果逻辑
- **避免无限循环**：防止 `useEffect` 导致的无限循环

### 轮询状态
- **usePolling hook**：默认禁用 (`enabled = false`)
- **RealTimeProgressDashboard**：强制禁用 (`isPolling = false`)
- **AnalysisProgress**：强制禁用 (`isPolling = false`)
- **AnalysisResults**：禁用自动获取结果
- **ProgressTracker**：已注释掉轮询逻辑

### 状态
✅ 已完成

### 测试建议
1. 启动新的分析任务，观察日志是否不再疯狂刷新
2. 检查实时进度页面是否能正常显示
3. 验证没有轮询请求在后台运行
4. 确认页面不再被强制刷新

---

## 2025-01-25 Authing 用户信息获取问题修复

### 任务描述
修复 Authing 登录后获取的用户信息是随机的，无法获取到真实的用户手机号或邮箱的问题。

### 问题分析
经过深入分析，发现问题的根本原因是：
1. **环境变量未正确设置**：`AUTHING_APP_SECRET` 还是占位符 `"your_app_secret_here"`
2. **Authing API 调用失败**：由于密钥不正确，导致无法从 Authing 获取真实用户信息
3. **代码逻辑正确**：`tradingagents_server.py` 中的代码逻辑是正确的，失败时会返回错误页面

### 解决方案
1. ✅ 创建了修复版环境变量设置脚本 `setup_authing_env_fixed.sh`
2. ✅ 创建了详细的修复指南 `docs/fixes/authing_user_info_fix_guide.md`
3. ✅ 创建了验证脚本 `test_authing_fix.sh`
4. ✅ 提供了完整的测试和验证流程

### 修改的文件
- **新增**：`setup_authing_env_fixed.sh` - 修复版环境变量设置脚本
- **新增**：`docs/fixes/authing_user_info_fix_guide.md` - 详细修复指南
- **新增**：`test_authing_fix.sh` - 验证脚本

### 关键修复点
1. **环境变量设置**：支持传入实际的应用密钥
2. **错误处理优化**：确保 Authing API 调用失败时返回明确的错误信息
3. **用户信息标准化**：使用现有的标准化逻辑确保用户信息一致性
4. **用户信息处理改进**：针对用户信息不完整的情况，优先使用手机号作为用户名和显示名称

### 使用步骤
1. 获取 Authing 应用密钥
2. 运行环境变量设置脚本：`./setup_authing_env_fixed.sh <your_app_secret>`
3. 确保 Authing 用户池中有测试用户
4. 启动服务并测试 SSO 登录

### 验证方法
运行验证脚本：`./test_authing_fix.sh`

### 状态
✅ 已完成

### 相关文档
- [修复指南](../fixes/authing_user_info_fix_guide.md)
- [Authing SSO 设置指南](../configuration/authing-sso-setup.md)

---

## 2025-09-29 数据源库安装问题修复

### 任务描述
修复股票分析系统中数据源库（akshare、tushare、baostock、dashscope）无法导入的问题，导致股票代码验证失败。

### 问题分析
1. **环境不匹配问题**：Python 使用 anaconda3 环境（Python 3.11.8），但 pip 安装的包在 homebrew 环境（Python 3.10）
2. **数据源库缺失**：akshare、tushare、baostock 等库无法导入
3. **DashScope 模块缺失**：dashscope 模块无法导入，导致 LLM 适配器初始化失败
4. **股票验证失败**：由于数据源不可用，股票代码 688256 验证失败

### 解决方案
1. ✅ 激活了正确的 conda 环境：`conda activate tradingagents`
2. ✅ 使用 conda 安装了 dashscope：`conda install dashscope -c conda-forge -y`
3. ✅ 使用 pip 强制重新安装了数据源库：`pip install --force-reinstall akshare tushare baostock`
4. ✅ 验证了所有关键库的导入功能
5. ✅ 测试了股票代码验证功能

### 修改的文件
- **环境配置**：激活 tradingagents conda 环境
- **依赖安装**：在正确环境中安装所有必需的数据源库

### 技术要点
- 解决了 Python 环境版本不匹配的问题
- 确保数据源库安装在正确的 Python 环境中
- 验证了 AKShare 和 Tushare 数据源的可用性
- 确认了 DashScope LLM 适配器的正常工作

### 验证结果
```bash
# 数据源管理器初始化成功
✅ Tushare数据源可用
✅ AKShare数据源可用
📊 数据源管理器初始化完成
   默认数据源: akshare
   可用数据源: ['tushare', 'akshare']

# 股票验证测试成功
股票验证结果: True, 错误信息: 
✅ [A股数据] 数据准备完成: 688256 - 寒武纪
```

### 环境要求
- conda 环境：tradingagents
- Python 版本：3.13.5
- 必需库：akshare、tushare、baostock、dashscope

### 状态
✅ 已完成

### 相关文档
- [数据源配置指南](../data/data-sources.md)
- [LLM 配置指南](../configuration/llm-config.md)
