#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 修复助手（PyQt 6 · 适配 Sequoia · 安全改进 · 两类结构 · 无 QtConcurrent 版）
修复：异步回调不再用 QTimer.singleShot，而改用 pyqtSignal，把工作线程结果安全送回 UI 线程。
"""

from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Callable, cast, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal, pyqtBoundSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QProgressDialog,
    QHBoxLayout,
    QLabel,
)

# ---------- 常量 ----------
APP_TITLE = "macOS 修复助手"

CONFIRM_STRINGS = (
    "Globally disabling the assessment system needs to be confirmed in System Settings.",
    "This operation is no longer supported",
)

PRIVACY_SECURITY_URL = "x-apple.systempreferences:com.apple.settings.PrivacySecurity"


# ======================================================================================
# 主要执行类
# ======================================================================================
class MacRepairExecutor:
    """
    主要执行类：封装系统操作（运行命令、识别 Sequoia 提示、打开系统设置等）。
    """

    def run_plain(self, argv: list[str]) -> Dict[str, object]:
        """同步执行无需 sudo 的命令，返回统一结果字典。"""
        proc = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", errors="replace"),
            "stderr": proc.stderr.decode("utf-8", errors="replace"),
        }

    def run_sudo(self, argv: list[str], password: str) -> Dict[str, object]:
        """同步执行需要 sudo 的命令，使用 stdin 传递密码避免泄露。"""
        proc = subprocess.run(
            ["sudo", "-S", "-p", ""] + argv,
            input=f"{password}\n".encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", errors="replace"),
            "stderr": proc.stderr.decode("utf-8", errors="replace"),
        }

    def requires_system_settings_confirmation(self, stdout: str, stderr: str) -> bool:
        """检测 spctl 关闭 Gatekeeper 时是否出现“需到系统设置确认”的提示。"""
        combined_lower = ((stdout or "") + "\n" + (stderr or "")).lower()
        return any(s.lower() in combined_lower for s in CONFIRM_STRINGS)

    def open_privacy_security_settings(self) -> None:
        """打开「系统设置 → 隐私与安全性」页面。"""
        subprocess.Popen(["open", PRIVACY_SECURITY_URL])

    # 语义化封装
    def spctl_global_disable(self, password: str) -> Dict[str, object]:
        return self.run_sudo(["spctl", "--global-disable"], password)

    def spctl_global_enable(self, password: str) -> Dict[str, object]:
        return self.run_sudo(["spctl", "--global-enable"], password)

    def spctl_status(self) -> Dict[str, object]:
        return self.run_plain(["spctl", "--status"])

    def remove_quarantine(self, app_path: str, password: str) -> Dict[str, object]:
        return self.run_sudo(["xattr", "-r", "-d", "com.apple.quarantine", app_path], password)

    def spctl_master_disable(self, password: str) -> Dict[str, object]:
        return self.run_sudo(["spctl", "--master-disable"], password)

    def spctl_master_enable(self, password: str) -> Dict[str, object]:
        return self.run_sudo(["spctl", "--master-enable"], password)


# ======================================================================================
# GUI 类
# ======================================================================================
class RepairAppWindow(QMainWindow):
    """
    GUI 主窗口：负责界面、交互与异步任务调度（ThreadPoolExecutor）。
    通过 taskFinished 信号把后台结果送回 UI 线程，避免 QTimer.singleShot 跨线程问题。
    """

    # (title, result_dict)
    taskFinished = pyqtSignal(str, dict)

    def __init__(self, executor: MacRepairExecutor):
        super().__init__()
        self.executor = executor
        self.setWindowTitle(APP_TITLE)
        self.setFixedWidth(420)

        # 线程池（单工即可，避免并发叠加）
        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="macfix")
        self._future: Optional[Future] = None

        root = QWidget()
        layout = QVBoxLayout(root)

        tip = QLabel(
            "说明：在 macOS 15（Sequoia）及更新版本，关闭 Gatekeeper 需要在「系统设置」里手动确认。\n"
            "本工具在检测到该情况时，会自动打开对应设置页并给出引导。"
        )
        tip.setWordWrap(True)
        layout.addWidget(tip)

        # 第一排：开启 / 恢复
        row1 = QHBoxLayout()
        self.btn_enable_anywhere = QPushButton("开启『任何来源』")
        self._connect_click(self.btn_enable_anywhere, self._on_enable_anywhere_clicked)
        row1.addWidget(self.btn_enable_anywhere)

        self.btn_disable_anywhere = QPushButton("恢复默认 Gatekeeper")
        self._connect_click(self.btn_disable_anywhere, self._on_disable_anywhere_clicked)
        row1.addWidget(self.btn_disable_anywhere)
        layout.addLayout(row1)

        # 第二排：状态 / 打开设置
        row2 = QHBoxLayout()
        self.btn_status = QPushButton("查看 Gatekeeper 状态")
        self._connect_click(self.btn_status, self._on_status_clicked)
        row2.addWidget(self.btn_status)

        self.btn_open_settings = QPushButton("打开系统设置")
        self._connect_click(self.btn_open_settings, self._on_open_settings_clicked)
        row2.addWidget(self.btn_open_settings)
        layout.addLayout(row2)

        # 修复“已损坏应用”（移除隔离）
        self.btn_fix_app = QPushButton("修复已损坏应用（移除隔离属性）")
        self._connect_click(self.btn_fix_app, self._on_fix_damaged_app_clicked)
        layout.addWidget(self.btn_fix_app)

        # 备用命令
        self.btn_legacy = QPushButton("备用命令（master-disable/enable）")
        self._connect_click(self.btn_legacy, self._on_legacy_clicked)
        layout.addWidget(self.btn_legacy)

        # 退出
        self.btn_quit = QPushButton("退出")
        self._connect_click(self.btn_quit, self.close)
        layout.addWidget(self.btn_quit)

        self.setCentralWidget(root)

        # 进度对话框
        self._progress: Optional[QProgressDialog] = None

        # 连接信号
        self.taskFinished.connect(self._on_async_finished)

    # -------------------- UI 辅助 --------------------
    def _progress_show(self, title: str) -> None:
        self._progress = QProgressDialog(f"{title} 执行中…", None, 0, 0, self, flags=Qt.WindowType.Dialog)
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.show()

    def _progress_close(self) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None

    def _ask_password(self) -> Optional[str]:
        password, ok = QInputDialog.getText(
            self, "输入系统密码", "请输入系统密码：", QLineEdit.EchoMode.Password
        )
        return password if (ok and password) else None

    def _connect_click(self, btn: QPushButton, handler: Callable[[], None]) -> None:
        """把按钮的 clicked 信号与无参 handler 连接；兼顾类型检查与运行时签名。"""
        sig = cast(pyqtBoundSignal, btn.clicked)
        sig.connect(lambda checked=False: handler())

    # -------------------- 异步调度（线程池） --------------------
    def _run_async(self, title: str, func, *args) -> None:
        """
        把耗时操作提交到线程池，完成后通过 taskFinished 信号把结果发回主线程。
        """
        self._progress_show(title)

        def done_callback(fut: Future) -> None:
            try:
                result = fut.result()
            except Exception as e:
                # 用特殊 returncode 标识异常路径
                result = {"returncode": -999, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}
            # 跨线程发回 UI（QueuedConnection）
            self.taskFinished.emit(title, result)

        self._future = self._pool.submit(func, *args)
        self._future.add_done_callback(done_callback)

    def _on_async_finished(self, title: str, result: Dict[str, object]) -> None:
        """统一结果处理：根据 returncode / 输出做成功、需确认或失败提示。"""
        self._progress_close()

        returncode = int(result.get("returncode", -1))
        stdout = str(result.get("stdout", "") or "")
        stderr = str(result.get("stderr", "") or "")

        if returncode == -999:
            QMessageBox.critical(self, "错误", f"{title} 失败（异常）：\n{stderr}")
            return

        if title.startswith("查看 Gatekeeper 状态"):
            msg = f"[返回码] {returncode}\n\n[stdout]\n{stdout or '(无)'}"
            if stderr.strip():
                msg += f"\n\n[stderr]\n{stderr}"
            QMessageBox.information(self, "Gatekeeper 状态", msg)
            return

        # 关闭 Gatekeeper 时遇到 Sequoia 的“需系统设置确认”
        if ("disable" in title.lower() or "任何来源" in title) and returncode != 0:
            if self.executor.requires_system_settings_confirmation(stdout, stderr):
                guide = (
                    "已请求关闭 Gatekeeper，但需要你在系统设置里手动确认：\n\n"
                    "1) 我已为你打开「系统设置 → 隐私与安全性」。\n"
                    "2) 滚动到页面底部，在“允许从以下位置下载的 App”选择「任何来源」。\n"
                    "3) 如未看到该项，请切换到其它设置页再切回来，或重启系统设置。\n\n"
                    "完成后可点击“查看 Gatekeeper 状态”确认是否已生效（应显示：assessments disabled）。"
                )
                QMessageBox.information(self, "需要在系统设置中确认", guide)
                self.executor.open_privacy_security_settings()
                return

        if returncode == 0:
            msg = f"{title} 成功完成。"
            if stdout.strip():
                msg += f"\n\n[输出]\n{stdout.strip()}"
            if stderr.strip():
                msg += f"\n\n[警告]\n{stderr.strip()}"
            QMessageBox.information(self, "成功", msg)
            return

        msg = (
            f"{title} 失败！\n\n"
            f"[返回码] {returncode}\n\n"
            f"stderr:\n{stderr or '(无)'}\n\n"
            f"stdout:\n{stdout or '(无)'}\n\n"
            "提示：若你在 macOS 15 及更新版本上尝试关闭 Gatekeeper，请优先使用“开启『任何来源』”按钮，"
            "并在提示后于系统设置中完成确认。若受 MDM 策略限制，该选项可能不可用。"
        )
        QMessageBox.critical(self, "错误", msg)

    # -------------------- 交互槽 --------------------
    def _on_enable_anywhere_clicked(self) -> None:
        password = self._ask_password()
        if password is None:
            return
        self._run_async("开启『任何来源』", self.executor.spctl_global_disable, password)

    def _on_disable_anywhere_clicked(self) -> None:
        password = self._ask_password()
        if password is None:
            return
        self._run_async("恢复默认 Gatekeeper", self.executor.spctl_global_enable, password)

    def _on_status_clicked(self) -> None:
        self._run_async("查看 Gatekeeper 状态", self.executor.spctl_status)

    def _on_open_settings_clicked(self) -> None:
        self.executor.open_privacy_security_settings()
        QMessageBox.information(
            self,
            "已打开系统设置",
            "请在「系统设置 → 隐私与安全性」页面底部，将“允许从以下位置下载的 App”改为「任何来源」。"
        )

    def _on_fix_damaged_app_clicked(self) -> None:
        app_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "/Applications", "应用程序 (*.app)"
        )
        if not app_path:
            return
        password = self._ask_password()
        if password is None:
            return
        title = f"修复 {Path(app_path).name}"
        self._run_async(title, self.executor.remove_quarantine, app_path, password)

    def _on_legacy_clicked(self) -> None:
        msg = (
            "以下命令与当前按钮等效，主要面向旧系统或习惯旧参数的用户：\n\n"
            "开启任何来源：sudo spctl --master-disable\n"
            "恢复默认：    sudo spctl --master-enable\n\n"
            "是否直接尝试“master-disable”？"
        )
        ret = QMessageBox.question(self, "备用命令", msg)
        if ret == QMessageBox.StandardButton.Yes:
            password = self._ask_password()
            if password is None:
                return
            self._run_async("开启『任何来源』（master-disable）", self.executor.spctl_master_disable, password)

    # -------------------- 清理 --------------------
    def closeEvent(self, event) -> None:  # noqa: N802
        """关闭窗口时关停线程池，避免后台线程存活。"""
        try:
            self._pool.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        super().closeEvent(event)


# ======================================================================================
# 入口
# ======================================================================================
def main() -> None:
    if sys.platform != "darwin":
        print("当前系统非 macOS，无法运行本工具。", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)

    executor = MacRepairExecutor()
    window = RepairAppWindow(executor)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()