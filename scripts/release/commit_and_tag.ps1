# Git 提交和标签创建脚本 (PowerShell)

$VERSION = "cn-v1.0"
$COMMIT_MSG = @"
chore: release version $VERSION

🎉 正式版本发布

主要改进:
- 项目结构优化和代码清理
- 移动 21 个临时文档到归档目录
- 移动 14 个临时脚本到归档目录
- 清理 3152 个 Python 缓存目录
- 更新版本号和发布说明
- 完善文档归档体系

详细信息请查看: docs/releases/RELEASE_NOTES_$VERSION.md
"@

$TAG_MSG = @"
Release $VERSION

正式版本发布 - 项目结构优化和代码清理

主要特性:
- 完整的多智能体交易决策框架
- 支持 A股/港股/美股分析
- 4 大 LLM 提供商，60+ 模型
- 现代化 Web 界面
- Docker 容器化部署
- 完整的中文文档体系

详细发布说明: docs/releases/RELEASE_NOTES_$VERSION.md
"@

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 Git 提交和标签创建" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "版本: $VERSION" -ForegroundColor Yellow
Write-Host ""

# 1. 检查 Git 状态
Write-Host "📋 检查 Git 状态..." -ForegroundColor Cyan
git status

Write-Host ""
$confirm = Read-Host "是否继续提交? (y/n)"
if ($confirm -ne "y") {
    Write-Host "❌ 已取消" -ForegroundColor Red
    exit 0
}

# 2. 添加所有更改
Write-Host ""
Write-Host "📦 添加所有更改..." -ForegroundColor Cyan
git add .

# 3. 提交更改
Write-Host ""
Write-Host "💾 提交更改..." -ForegroundColor Cyan
git commit -m $COMMIT_MSG

# 4. 创建标签
Write-Host ""
Write-Host "🏷️  创建标签..." -ForegroundColor Cyan
git tag -a $VERSION -m $TAG_MSG

# 5. 显示最近的提交和标签
Write-Host ""
Write-Host "✅ 提交和标签创建完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 最近的提交:" -ForegroundColor Cyan
git log -1 --oneline

Write-Host ""
Write-Host "🏷️  最近的标签:" -ForegroundColor Cyan
git tag -l $VERSION -n3

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📤 下一步操作:" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 推送代码到远程仓库:" -ForegroundColor White
Write-Host "   git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 推送标签到远程仓库:" -ForegroundColor White
Write-Host "   git push origin $VERSION" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 或者一次性推送所有:" -ForegroundColor White
Write-Host "   git push origin main --tags" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 在 GitHub 上创建 Release:" -ForegroundColor White
Write-Host "   https://github.com/hsliuping/TradingAgents-CN/releases/new" -ForegroundColor Gray
Write-Host "   - 选择标签: $VERSION" -ForegroundColor Gray
Write-Host "   - 复制发布说明: docs/releases/RELEASE_NOTES_$VERSION.md" -ForegroundColor Gray
Write-Host ""
