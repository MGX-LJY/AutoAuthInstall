#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
提供通用的辅助功能
"""

from pathlib import Path
from typing import Optional


def validate_app_path(path: str) -> bool:
    """
    验证应用程序路径是否有效
    
    Args:
        path: 应用程序路径
        
    Returns:
        路径是否有效
    """
    if not path:
        return False
    
    app_path = Path(path)
    return app_path.exists() and app_path.suffix.lower() == '.app'


def get_app_name(path: str) -> Optional[str]:
    """
    从应用程序路径提取应用名称
    
    Args:
        path: 应用程序路径
        
    Returns:
        应用名称，如果路径无效返回None
    """
    if not validate_app_path(path):
        return None
    
    return Path(path).stem


def is_password_valid(password: str) -> bool:
    """
    简单验证密码是否有效（非空）
    
    Args:
        password: 密码字符串
        
    Returns:
        密码是否有效
    """
    return bool(password and password.strip())