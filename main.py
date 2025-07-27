#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 修复助手  (PyQt 6 版 · 适配 Sequoia · 安全改进)

更新要点：
- 识别 macOS 15 (Sequoia) 上 spctl 的“需到系统设置确认”提示，视为“待确认”而非失败
- 一键打开「系统设置 → 隐私与安全性」页面
- 新增“查看 Gatekeeper 状态”“打开系统设置”按钮
- 仍提供“恢复默认 Gatekeeper”“修复已损坏应用（移除隔离属性）”
- 后台线程执行，避免 UI 阻塞；并详尽展示 stdout / stderr

安全实践：
- 使用 sudo -S + stdin 传递密码，避免 shell 注入
- 参数以列表传递，避免手工 quoting
- returncode 判断 + 特定文案识别
"""

import sys
import subprocess
from pathlib import Path
from functools import partial

# -----------------------  PyQt 6  ------------------------ #
from PyQt6.QtCore import Qt, QThread, pyqtSignal
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

# ---------- 常量 ---------- #

# Sequoia 及后续版本在 spctl 全局关闭时常见的提示（英文为主）
CONFIRM_STRINGS = (
    "Globally disabling the assessment system needs to be confirmed in System Settings.",
    "This operation is no longer supported",  # 某些测试版/不同区域文案
)

# 打开「系统设置 → 隐私与安全性」的 URL（Sonoma/Sequoia 适用）
PRIVACY_SECURITY_URL = "x-apple.systempreferences:com.apple.settings.PrivacySecurity"

APP_TITLE = "macOS 修复助手"


# ---------- 基础执行函数 ---------- #
def run_plain(argv: list[str]) -> tuple[int, str, str]:
    """无 sudo 执行命令。"""
    proc = subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, stdout, stderr


def run_sudo(argv: list[str], password: str) -> tuple[int, str, str]:
    """以 sudo 执行命令（静默密码提示）。"""
    proc = subprocess.run(
        ["sudo", "-S", "-p", ""] + argv,
        input=f"{password}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, stdout, stderr


# ---------- 后台线程 ---------- #
class SudoWorker(QThread):
    """
    后台线程里以 sudo 执行单条命令，避免阻塞 UI。
    """
    finished = pyqtSignal(str, int, str, str)  # title, returncode, stdout, stderr

    def __init__(self, title: str, argv: list[str], password: str):
        super().__init__()
        self.title = title
        self.argv = argv
        self.password = password

    def run(self):
        code, out, err = run_sudo(self.argv, self.password)
        # 清理密码引用
        self.password = None
        self.finished.emit(self.title, code, out, err)


class PlainWorker(QThread):
    """
    后台线程里无 sudo 执行单条命令。
    """
    finished = pyqtSignal(str, int, str, str)  # title, returncode, stdout, stderr

    def __init__(self, title: str, argv: list[str]):
        super().__init__()
        self.title = title
        self.argv = argv

    def run(self):
        code, out, err = run_plain(self.argv)
        self.finished.emit(self.title, code, out, err)


# ---------- 主窗口 ---------- #
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setFixedWidth(420)

        root = QWidget()
        layout = QVBoxLayout(root)

        # 顶部说明
        tip = QLabel(
            "说明：在 macOS 15（Sequoia）及更新版本，关闭 Gatekeeper 需要在「系统设置」里手动确认。\n"
            "本工具会在检测到该情况时，引导并自动打开对应设置页。"
        )
        tip.setWordWrap(True)
        layout.addWidget(tip)

        # 第一排：开启 / 恢复
        row1 = QHBoxLayout()
        self.btn_enable_anywhere = QPushButton("开启『任何来源』")
        self.btn_enable_anywhere.clicked.connect(
            partial(self._ask_password_and_run, "开启『任何来源』", ["spctl", "--global-disable"])
        )
        row1.addWidget(self.btn_enable_anywhere)

        self.btn_disable_anywhere = QPushButton("恢复默认 Gatekeeper")
        self.btn_disable_anywhere.clicked.connect(
            partial(self._ask_password_and_run, "恢复默认 Gatekeeper", ["spctl", "--global-enable"])
        )
        row1.addWidget(self.btn_disable_anywhere)
        layout.addLayout(row1)

        # 第二排：状态 / 打开设置
        row2 = QHBoxLayout()
        self.btn_status = QPushButton("查看 Gatekeeper 状态")
        self.btn_status.clicked.connect(
            partial(self._run_plain_in_thread, "查看 Gatekeeper 状态", ["spctl", "--status"])
        )
        row2.addWidget(self.btn_status)

        self.btn_open_settings = QPushButton("打开系统设置")
        self.btn_open_settings.clicked.connect(self._open_privacy_security)
        row2.addWidget(self.btn_open_settings)
        layout.addLayout(row2)

        # 修复“已损坏应用”（移除隔离）
        self.btn_fix_app = QPushButton("修复已损坏应用（移除隔离属性）")
        self.btn_fix_app.clicked.connect(self._fix_damaged_app_flow)
        layout.addWidget(self.btn_fix_app)

        # 备用命令（老系统）
        self.btn_legacy = QPushButton("备用命令（master-disable/enable）")
        self.btn_legacy.clicked.connect(self._show_legacy_options)
        layout.addWidget(self.btn_legacy)

        # 退出
        self.btn_quit = QPushButton("退出")
        self.btn_quit.clicked.connect(self.close)
        layout.addWidget(self.btn_quit)

        self.setCentralWidget(root)

        # 简单进度对话框
        self._progress: QProgressDialog | None = None

        # 线程引用
        self.worker = None

    # ---------- UI 辅助 ----------
    def _progress_show(self, title: str):
        self._progress = QProgressDialog(f"{title} 执行中…", None, 0, 0, self, flags=Qt.WindowType.Dialog)
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.show()

    def _progress_close(self):
        if self._progress:
            self._progress.close()
            self._progress = None

    # ---------- 动作：开启 / 恢复（sudo） ----------
    def _ask_password_and_run(self, title: str, argv: list[str]):
        password, ok = QInputDialog.getText(
            self, "输入系统密码", "请输入系统密码：", QLineEdit.EchoMode.Password
        )
        if not (ok and password):
            return
        self._run_sudo_in_thread(title, argv, password)

    def _run_sudo_in_thread(self, title: str, argv: list[str], password: str):
        self._progress_show(title)
        self.worker = SudoWorker(title, argv, password)
        self.worker.finished.connect(self._on_cmd_finished)
        self.worker.start()

    # ---------- 动作：无 sudo 命令 ----------
    def _run_plain_in_thread(self, title: str, argv: list[str]):
        self._progress_show(title)
        self.worker = PlainWorker(title, argv)
        self.worker.finished.connect(self._on_cmd_finished)
        self.worker.start()

    # ---------- 打开系统设置 ----------
    def _open_privacy_security(self):
        # 无阻塞打开设置页
        subprocess.Popen(["open", PRIVACY_SECURITY_URL])
        QMessageBox.information(
            self,
            "已打开系统设置",
            "请在「系统设置 → 隐私与安全性」页面底部，将“允许从以下位置下载的 App”改为「任何来源」。"
        )

    # ---------- 修复“已损坏应用” ----------
    def _fix_damaged_app_flow(self):
        app_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "/Applications", "应用程序 (*.app)"
        )
        if not app_path:
            return

        password, ok = QInputDialog.getText(
            self, "输入系统密码", "请输入系统密码：", QLineEdit.EchoMode.Password
        )
        if not (ok and password):
            return

        argv = ["xattr", "-r", "-d", "com.apple.quarantine", app_path]
        self._run_sudo_in_thread(f"修复 {Path(app_path).name}", argv, password)

    # ---------- 备用命令 ----------
    def _show_legacy_options(self):
        msg = (
            "以下命令与当前按钮等效，主要面向旧系统或习惯旧参数的用户：\n\n"
            "开启任何来源：sudo spctl --master-disable\n"
            "恢复默认：    sudo spctl --master-enable\n\n"
            "是否直接尝试“master-disable”？"
        )
        ret = QMessageBox.question(self, "备用命令", msg)
        if ret == QMessageBox.StandardButton.Yes:
            self._ask_password_and_run("开启『任何来源』（master-disable）", ["spctl", "--master-disable"])

    # ---------- 统一结果处理 ----------
    def _on_cmd_finished(self, title: str, returncode: int, stdout: str, stderr: str):
        self._progress_close()
        self.worker = None

        # 归一化文本，便于检测提示语
        combined = (stdout or "") + "\n" + (stderr or "")
        combined_lower = combined.lower()

        def contains_confirm_string() -> bool:
            for s in CONFIRM_STRINGS:
                if s.lower() in combined_lower:
                    return True
            return False

        if title.startswith("查看 Gatekeeper 状态"):
            # 纯展示
            msg = f"[返回码] {returncode}\n\n[stdout]\n{stdout or '(无)'}"
            if stderr.strip():
                msg += f"\n\n[stderr]\n{stderr}"
            QMessageBox.information(self, "Gatekeeper 状态", msg)
            return

        # 针对 spctl 关闭（global/master disable）：非 0 但出现“需要系统设置确认”的文案
        if ("disable" in " ".join(title.split()).lower()) and returncode != 0 and contains_confirm_string():
            # 视为“待确认”
            guide = (
                "已请求关闭 Gatekeeper，但需要你在系统设置里手动确认：\n\n"
                "1) 我已为你打开「系统设置 → 隐私与安全性」。\n"
                "2) 滚动到页面底部，在“允许从以下位置下载的 App”选择「任何来源」。\n"
                "3) 如未看到该项，请切换到其它设置页再切回来，或重启系统设置。\n\n"
                "完成后可点击“查看 Gatekeeper 状态”确认是否已生效（应显示：assessments disabled）。"
            )
            QMessageBox.information(self, "需要在系统设置中确认", guide)
            # 打开设置
            subprocess.Popen(["open", PRIVACY_SECURITY_URL])
            return

        # 正常成功
        if returncode == 0:
            msg = f"{title} 成功完成。"
            if stdout.strip():
                msg += f"\n\n[输出]\n{stdout.strip()}"
            if stderr.strip():
                msg += f"\n\n[警告]\n{stderr.strip()}"
            QMessageBox.information(self, "成功", msg)
            return

        # 其它失败（未命中“需要确认”的情形）
        msg = (
            f"{title} 失败！\n\n"
            f"[返回码] {returncode}\n\n"
            f"stderr:\n{stderr or '(无)'}\n\n"
            f"stdout:\n{stdout or '(无)'}\n\n"
            "提示：若你在 macOS 15 及更新版本上尝试关闭 Gatekeeper，请优先使用“开启『任何来源』”按钮，"
            "并在提示后于系统设置中完成确认。若受 MDM 策略限制，该选项可能不可用。"
        )
        QMessageBox.critical(self, "错误", msg)

    # macOS 13+ 新 API：支持状态恢复
    def applicationSupportsSecureRestorableState(self) -> bool:  # noqa: N802
        return True


# ---------- main ---------- #
def main():
    if sys.platform != "darwin":
        QMessageBox.critical(None, APP_TITLE, "当前系统非 macOS，无法运行本工具。")
        sys.exit(1)

    app = QApplication(sys.argv)
    # 在 PyQt6 中枚举放在 Qt.ApplicationAttribute
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)
    window = MainApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()