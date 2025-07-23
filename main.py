#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 修复助手  (安全改进版)

✔ 解决缺失 import / 语法错误
✔ 使用 sudo -S + stdin 彻底消除 shell 注入
✔ 参数列表传递避免手动 quoting
✔ returncode-based 成功/失败判断
✔ 显示 stdout/stderr 详情
✔ 可选「恢复默认 Gatekeeper」按钮
✔ 简单进度指示避免重复点击
"""

import sys
import subprocess
from pathlib import Path
from functools import partial

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QMessageBox, QFileDialog, QInputDialog, QLineEdit, QProgressDialog
)


# ---------- 后台执行线程 ---------- #
class SudoWorker(QThread):
    """
    在后台线程里以 sudo 执行命令，避免阻塞 UI。
    """
    finished = pyqtSignal(bool, str, str, str)  # ok, title, stdout, stderr

    def __init__(self, title: str, argv: list[str], password: str):
        super().__init__()
        self.title = title
        self.argv = argv
        self.password = password

    def run(self):
        ok, out, err = run_sudo(self.argv, self.password)
        # 清理密码引用
        self.password = None
        self.finished.emit(ok, self.title, out, err)


# ---------- 核心 sudo 调用 ---------- #
def run_sudo(argv: list[str], password: str) -> tuple[bool, str, str]:
    """
    使用『sudo -S -p "" …』执行命令，屏蔽默认 Password: 提示。
    """
    proc = subprocess.run(
        ["sudo", "-S", "-p", ""] + argv,          # ← 这里加 -p ""
        input=f"{password}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode == 0, stdout, stderr


# ---------- 主窗口 ---------- #
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS 修复助手")
        self.setFixedWidth(360)

        layout = QVBoxLayout()

        # — 按钮：开启任何来源 —
        self.btn_enable_anywhere = QPushButton("开启『任何来源』")
        self.btn_enable_anywhere.clicked.connect(
            partial(self._ask_password_and_run,
                    "开启『任何来源』",
                    ["spctl", "--master-disable"])
        )
        layout.addWidget(self.btn_enable_anywhere)

        # — 按钮：恢复默认 Gatekeeper —
        self.btn_disable_anywhere = QPushButton("恢复默认 Gatekeeper")
        self.btn_disable_anywhere.clicked.connect(
            partial(self._ask_password_and_run,
                    "恢复默认 Gatekeeper",
                    ["spctl", "--master-enable"])
        )
        layout.addWidget(self.btn_disable_anywhere)

        # — 按钮：修复损坏应用 —
        self.btn_fix_app = QPushButton("修复已损坏应用")
        self.btn_fix_app.clicked.connect(self._fix_damaged_app_flow)
        layout.addWidget(self.btn_fix_app)

        # — 退出 —
        self.btn_quit = QPushButton("退出")
        self.btn_quit.clicked.connect(self.close)
        layout.addWidget(self.btn_quit)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 简单进度对话框
        self._progress: QProgressDialog | None = None

    # ---------- 通用密码提示 + 后台执行 ---------- #
    def _ask_password_and_run(self, title: str, argv: list[str]):
        password, ok = QInputDialog.getText(
            self, "输入系统密码", "请输入系统密码：", QLineEdit.Password
        )
        if not (ok and password):
            return

        self._run_in_thread(title, argv, password)

    # ---------- 修复损坏应用流程 ---------- #
    def _fix_damaged_app_flow(self):
        app_path, _ = QFileDialog.getOpenFileName(
            self, "选择应用", "/Applications", "应用程序 (*.app)"
        )
        if not app_path:
            return

        password, ok = QInputDialog.getText(
            self, "输入系统密码", "请输入系统密码：", QLineEdit.Password
        )
        if not (ok and password):
            return

        argv = ["xattr", "-r", "-d", "com.apple.quarantine", app_path]
        self._run_in_thread(f"修复 {Path(app_path).name}", argv, password)

    # ---------- 线程封装 ---------- #
    def _run_in_thread(self, title: str, argv: list[str], password: str):
        # 创建进度窗口
        self._progress = QProgressDialog(
            f"{title} 执行中…", None, 0, 0, self, flags=Qt.Dialog
        )
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.show()

        # 后台线程执行
        self.worker = SudoWorker(title, argv, password)
        self.worker.finished.connect(self._on_cmd_finished)
        self.worker.start()

    # ---------- 执行结果处理 ---------- #
    def _on_cmd_finished(self, ok: bool, title: str, stdout: str, stderr: str):
        if self._progress:
            self._progress.close()
            self._progress = None

        if ok:
            msg = f"{title} 成功完成。"
            if stdout.strip():
                msg += f"\n\n[输出]\n{stdout.strip()}"
            if stderr.strip():
                # 有时成功也会写 stderr
                msg += f"\n\n[警告]\n{stderr.strip()}"
            QMessageBox.information(self, "成功", msg)
        else:
            msg = (
                f"{title} 失败！\n\n"
                f"stderr:\n{stderr or '(无)'}\n\n"
                f"stdout:\n{stdout or '(无)'}"
            )
            QMessageBox.critical(self, "错误", msg)

        # 清理线程引用
        self.worker = None

    # macOS 13+ 新 API：支持状态恢复
    def applicationSupportsSecureRestorableState(self) -> bool:  # noqa: N802
        """指示应用支持状态恢复。"""
        return True


# ---------- main ---------- #
def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontUseNativeMenuBar, False)  # 兼容 PyInstaller 菜单条
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()