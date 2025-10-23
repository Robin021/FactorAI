#!/usr/bin/env python3
"""
测试模型配置 API
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def test_default_model_config():
    """测试默认模型配置"""
    from tradingagents.default_config import DEFAULT_CONFIG
    
    print("=" * 60)
    print("当前默认配置:")
    print("=" * 60)
    print(f"LLM Provider: {DEFAULT_CONFIG.get('llm_provider')}")
    print(f"Deep Think LLM: {DEFAULT_CONFIG.get('deep_think_llm')}")
    print(f"Quick Think LLM: {DEFAULT_CONFIG.get('quick_think_llm')}")
    print()
    
    print("=" * 60)
    print("检查可用的 API 密钥:")
    print("=" * 60)
    
    api_keys = {
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "QIANFAN_API_KEY": os.getenv("QIANFAN_API_KEY"),
    }
    
    for key, value in api_keys.items():
        status = "✅ 已配置" if value else "❌ 未配置"
        masked_value = f"{value[:10]}..." if value and len(value) > 10 else "N/A"
        print(f"{key:25s}: {status:10s} ({masked_value})")
    
    print()
    print("=" * 60)
    print("可用的模型提供商:")
    print("=" * 60)
    
    available_providers = []
    
    if os.getenv("DASHSCOPE_API_KEY"):
        available_providers.append("dashscope (阿里百炼)")
        print("✅ DashScope (阿里百炼)")
        print("   - qwen-turbo")
        print("   - qwen-plus")
        print("   - qwen-max")
    
    if os.getenv("DEEPSEEK_API_KEY") and os.getenv("DEEPSEEK_ENABLED", "false").lower() == "true":
        available_providers.append("deepseek")
        print("✅ DeepSeek")
        print("   - deepseek-chat")
        print("   - deepseek-coder")
    
    if os.getenv("OPENAI_API_KEY"):
        available_providers.append("openai")
        print("✅ OpenAI")
        print("   - gpt-4")
        print("   - gpt-4-turbo")
        print("   - gpt-3.5-turbo")
        print("   - gpt-4o-mini")
    
    if os.getenv("OPENROUTER_API_KEY"):
        available_providers.append("openrouter")
        print("✅ OpenRouter")
        print("   - anthropic/claude-3.5-sonnet")
        print("   - google/gemini-2.0-flash-exp:free")
    
    if os.getenv("GOOGLE_API_KEY"):
        available_providers.append("google")
        print("✅ Google Gemini")
        print("   - gemini-pro")
        print("   - gemini-2.0-flash")
    
    if os.getenv("QIANFAN_API_KEY"):
        available_providers.append("qianfan")
        print("✅ 百度千帆")
        print("   - ernie-bot")
        print("   - ernie-bot-turbo")
    
    if not available_providers:
        print("❌ 没有配置任何模型提供商的 API 密钥")
        print("   请在 .env 文件中配置至少一个 API 密钥")
    
    print()
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_default_model_config()
