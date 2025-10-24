#!/bin/bash
# Git 提交和标签创建脚本

VERSION="cn-v1.0"
COMMIT_MSG="chore: release version ${VERSION}

🎉 正式版本发布

主要改进:
- 项目结构优化和代码清理
- 移动 21 个临时文档到归档目录
- 移动 14 个临时脚本到归档目录
- 清理 3152 个 Python 缓存目录
- 更新版本号和发布说明
- 完善文档归档体系

详细信息请查看: docs/releases/RELEASE_NOTES_${VERSION}.md"

echo "============================================================"
echo "🚀 Git 提交和标签创建"
echo "============================================================"
echo ""
echo "版本: ${VERSION}"
echo ""

# 1. 检查 Git 状态
echo "📋 检查 Git 状态..."
git status

echo ""
read -p "是否继续提交? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

# 2. 添加所有更改
echo ""
echo "📦 添加所有更改..."
git add .

# 3. 提交更改
echo ""
echo "💾 提交更改..."
git commit -m "${COMMIT_MSG}"

# 4. 创建标签
echo ""
echo "🏷️  创建标签..."
git tag -a "${VERSION}" -m "Release ${VERSION}

正式版本发布 - 项目结构优化和代码清理

主要特性:
- 完整的多智能体交易决策框架
- 支持 A股/港股/美股分析
- 4 大 LLM 提供商，60+ 模型
- 现代化 Web 界面
- Docker 容器化部署
- 完整的中文文档体系

详细发布说明: docs/releases/RELEASE_NOTES_${VERSION}.md"

# 5. 显示最近的提交和标签
echo ""
echo "✅ 提交和标签创建完成！"
echo ""
echo "📋 最近的提交:"
git log -1 --oneline

echo ""
echo "🏷️  最近的标签:"
git tag -l "${VERSION}" -n3

echo ""
echo "============================================================"
echo "📤 下一步操作:"
echo "============================================================"
echo ""
echo "1. 推送代码到远程仓库:"
echo "   git push origin main"
echo ""
echo "2. 推送标签到远程仓库:"
echo "   git push origin ${VERSION}"
echo ""
echo "3. 或者一次性推送所有:"
echo "   git push origin main --tags"
echo ""
echo "4. 在 GitHub 上创建 Release:"
echo "   https://github.com/hsliuping/TradingAgents-CN/releases/new"
echo "   - 选择标签: ${VERSION}"
echo "   - 复制发布说明: docs/releases/RELEASE_NOTES_${VERSION}.md"
echo ""
