#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心业务逻辑模块
简化版的系统命令执行器，专注于两个核心功能
"""

import subprocess
import sys
from typing import Dict, Any
from pathlib import Path

from config.constants import CONFIRM_STRINGS, PRIVACY_SECURITY_URL


class RepairExecutor:
    """
    系统修复执行器
    简化设计，只包含两个核心功能：开启任何来源和修复损坏应用
    """

    def __init__(self):
        """初始化执行器，检查系统兼容性"""
        if sys.platform != "darwin":
            raise RuntimeError("此工具仅支持 macOS 系统")

    def _run_command(self, cmd: list[str], use_sudo: bool = False, password: str = None) -> Dict[str, Any]:
        """
        统一的命令执行方法
        
        Args:
            cmd: 要执行的命令列表
            use_sudo: 是否使用sudo权限
            password: sudo密码（当use_sudo为True时必需）
            
        Returns:
            包含执行结果的字典
        """
        try:
            if use_sudo:
                if not password:
                    raise ValueError("执行sudo命令需要提供密码")
                
                # 使用stdin传递密码以提高安全性
                full_cmd = ["sudo", "-S", "-p", ""] + cmd
                proc = subprocess.run(
                    full_cmd,
                    input=f"{password}\n".encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
            else:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout.decode("utf-8", errors="replace"),
                "stderr": proc.stderr.decode("utf-8", errors="replace"),
            }

        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"命令执行异常: {str(e)}",
            }

    def _needs_system_settings_confirmation(self, result: Dict[str, Any]) -> bool:
        """
        检测是否需要在系统设置中手动确认
        用于处理 macOS 15+ 的新安全策略
        
        Args:
            result: 命令执行结果
            
        Returns:
            是否需要系统设置确认
        """
        if result["success"]:
            return False
            
        combined_output = (result["stdout"] + " " + result["stderr"]).lower()
        return any(confirm_str.lower() in combined_output for confirm_str in CONFIRM_STRINGS)

    def enable_anywhere_source(self, password: str) -> Dict[str, Any]:
        """
        开启任何来源功能
        关闭 Gatekeeper 以允许安装未签名应用
        
        Args:
            password: 系统密码
            
        Returns:
            操作结果字典
        """
        result = self._run_command(["spctl", "--global-disable"], use_sudo=True, password=password)
        
        # 检查是否需要系统设置确认 (macOS 15+)
        if not result["success"] and self._needs_system_settings_confirmation(result):
            # 自动打开系统设置页面
            self.open_system_settings()
            result["needs_manual_confirmation"] = True
            result["message"] = "已打开系统设置，请手动确认"
        else:
            result["needs_manual_confirmation"] = False
            if result["success"]:
                result["message"] = "任何来源已成功开启"
            else:
                result["message"] = f"操作失败: {result['stderr']}"
        
        return result

    def fix_damaged_app(self, app_path: str, password: str) -> Dict[str, Any]:
        """
        修复损坏的应用程序
        移除应用的隔离属性 (com.apple.quarantine)
        
        Args:
            app_path: 应用程序路径
            password: 系统密码
            
        Returns:
            操作结果字典
        """
        # 验证应用路径
        path = Path(app_path)
        if not path.exists():
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "应用程序路径不存在",
                "message": "指定的应用程序不存在"
            }

        # 执行移除隔离属性命令
        result = self._run_command(
            ["xattr", "-r", "-d", "com.apple.quarantine", app_path],
            use_sudo=True,
            password=password
        )
        
        if result["success"]:
            result["message"] = f"应用 {path.name} 修复成功"
        else:
            # 检查是否是因为属性不存在而失败（这实际上不是错误）
            if "No such xattr" in result["stderr"]:
                result["success"] = True
                result["message"] = f"应用 {path.name} 无需修复"
            else:
                result["message"] = f"修复失败: {result['stderr']}"
        
        return result

    def open_system_settings(self) -> None:
        """
        打开系统设置的隐私与安全性页面
        用于 macOS 15+ 系统的手动确认流程
        """
        try:
            subprocess.Popen(["open", PRIVACY_SECURITY_URL])
        except Exception:
            # 如果自动打开失败，静默处理
            pass