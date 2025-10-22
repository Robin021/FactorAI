#!/bin/bash

# 项目清理脚本 - 删除测试和临时文件

echo "=== 项目清理工具 ==="
echo ""
echo "将要删除以下文件："
echo ""

# 根目录的测试文件
TEST_FILES=(
    "check_analysis.py"
    "check_data_simple.py"
    "fix_analysis_data.py"
    "fix_duplicate_analysis.py"
    "fix_server_duplicate.py"
    "fixed_analysis_function.py"
    "monitor_analysis.py"
    "test_analysis_fix.py"
    "test_analysis_mongodb.py"
    "test_frontend_redirect.html"
    "test_mongodb_connection.py"
    "test_progress_fix.py"
    "test_progress_update.py"
)

# 根目录的临时文档
TEMP_DOCS=(
    "ANALYSIS_FIX_SUMMARY.md"
    "FINAL_FIX_VERIFICATION.md"
    "fix_analysis_issue.md"
    "FIXES_APPLIED.md"
    "FIXES_SUMMARY.md"
    "Hooks错误修复.md"
    "PROGRESS_CALLBACK_FIX.md"
    "PROGRESS_FIX_SUMMARY.md"
    "SimpleProgress组件分析.md"
    "STREAMLIT_CLEANUP_SUMMARY.md"
    "time_progress_fix_summary.md"
    "代码清理总结.md"
    "时间统计修复总结.md"
    "股票分析流程图.md"
)

# 多余的 docker-compose 文件
EXTRA_COMPOSE=(
    "docker-compose.https.yml"
)

# 其他临时文件
OTHER_TEMP=(
    "hk_stock_cache.json"
)

echo "测试文件:"
for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
echo "临时文档:"
for file in "${TEMP_DOCS[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
echo "多余的配置文件:"
for file in "${EXTRA_COMPOSE[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
echo "其他临时文件:"
for file in "${OTHER_TEMP[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
read -p "确认删除这些文件? (y/N): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    echo ""
    echo "开始清理..."
    
    count=0
    
    for file in "${TEST_FILES[@]}" "${TEMP_DOCS[@]}" "${EXTRA_COMPOSE[@]}" "${OTHER_TEMP[@]}"; do
        if [ -f "$file" ]; then
            rm "$file"
            echo "✓ 已删除: $file"
            ((count++))
        fi
    done
    
    echo ""
    echo "✅ 清理完成！共删除 $count 个文件"
    echo ""
    echo "保留的重要文件:"
    echo "  - docker-compose.yml (基础配置)"
    echo "  - docker-compose.prod.yml (生产环境配置)"
    echo "  - docker-compose.dev.yml (开发环境配置)"
    echo "  - docker-compose.certbot.yml (SSL 证书自动续期)"
else
    echo ""
    echo "取消清理"
fi
