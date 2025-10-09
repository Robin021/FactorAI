#!/usr/bin/env python3
"""
环境变量工具模块
提供统一的环境变量解析功能
"""

import os
from typing import Union


def parse_bool_env(env_var: str, default: bool = False) -> bool:
    """
    解析布尔类型的环境变量
    
    Args:
        env_var: 环境变量名
        default: 默认值
        
    Returns:
        bool: 解析后的布尔值
        
    支持的真值: true, True, TRUE, 1, yes, Yes, YES, on, On, ON
    支持的假值: false, False, FALSE, 0, no, No, NO, off, Off, OFF
    """
    value = os.getenv(env_var)
    if value is None:
        return default
    
    # 转换为字符串并去除空白
    value_str = str(value).strip().lower()
    
    # 真值
    if value_str in ('true', '1', 'yes', 'on'):
        return True
    
    # 假值
    if value_str in ('false', '0', 'no', 'off', ''):
        return False
    
    # 默认返回 False（保守策略）
    return default


def get_mongodb_url() -> str:
    """
    获取统一的MongoDB连接字符串
    
    Returns:
        str: MongoDB连接字符串
        
    Raises:
        ValueError: 当配置不完整时
    """
    # 优先使用 MONGODB_URL
    mongodb_url = os.getenv('MONGODB_URL')
    if mongodb_url:
        return mongodb_url
    
    # 兼容旧版本配置
    mongodb_connection_string = os.getenv('MONGODB_CONNECTION_STRING')
    if mongodb_connection_string:
        return mongodb_connection_string
    
    # 从分离的配置构建连接字符串
    host = os.getenv('MONGODB_HOST', 'localhost')
    port = os.getenv('MONGODB_PORT', '27017')
    username = os.getenv('MONGODB_USERNAME')
    password = os.getenv('MONGODB_PASSWORD')
    database = os.getenv('MONGODB_DATABASE', 'tradingagents')
    auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
    
    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource={auth_source}"
    else:
        return f"mongodb://{host}:{port}/{database}"


def get_mongodb_database_name() -> str:
    """
    获取MongoDB数据库名称
    
    Returns:
        str: 数据库名称
    """
    # 优先使用新的配置
    db_name = os.getenv('MONGODB_DB_NAME')
    if db_name:
        return db_name
    
    # 兼容旧版本配置
    return os.getenv('MONGODB_DATABASE', os.getenv('DATABASE_NAME', 'tradingagents'))