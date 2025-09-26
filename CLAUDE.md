# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

- 回答必须使用中文
- 在docker中禁止执行删除等操作
- 修改代码时，要考虑对于项目的破坏程度
- 每次修改代码等需要添加对应的注释，不要太详细也不要太简单
- 只有在测试情况下可以添加文件，其他情况下优先复用已有代码，如果需要创建新文件等，需要获取使用者的同意

## 项目概述

AutoAuthInstall 是一个经过重构的现代化 macOS 应用程序修复助手。项目采用解耦架构设计，专注于两个核心功能：开启任何来源和修复损坏应用，提供简洁美观的用户界面。

## 重构后的架构设计

### 模块化分层架构
```
project/
├── main.py              # 简化入口文件
├── config/              # 配置层
│   └── constants.py     # 应用常量和配置
├── core/                # 业务逻辑层  
│   └── executor.py      # 核心系统操作执行器
├── gui/                 # 用户界面层
│   ├── main_window.py   # 现代化主窗口
│   └── widgets.py       # 自定义UI组件
└── utils/               # 工具函数层
    └── helpers.py       # 通用辅助函数
```

### 关键设计改进
- **功能简化**: 从多功能界面简化为专注的双核心功能
- **解耦设计**: GUI、业务逻辑、配置完全分离
- **现代化UI**: 卡片式布局、响应式设计、现代配色方案
- **安全优化**: stdin密码传递、异步任务处理
- **macOS 15+兼容**: 自动检测和处理Sequoia系统设置确认流程

## 开发和构建命令

### 基本运行
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### 打包应用
```bash
# 安装打包工具
pip install pyinstaller
brew install create-dmg

# 使用 PyInstaller 打包 (需要 main.spec 文件)
pyinstaller main.spec

# 创建 DMG 文件
create-dmg 'dist/macOSInstallerAssistant'
```

## 依赖管理

- **PyQt6**: 主要 GUI 框架，版本 ~=6.9.1
- **pyinstaller**: 用于打包成独立应用
- **create-dmg**: 用于创建 macOS 安装包

## 代码结构说明

### 主要模块
- `MacRepairExecutor.run_sudo()`: 安全执行需要管理员权限的命令
- `MacRepairExecutor.requires_system_settings_confirmation()`: 检测 Sequoia 系统的确认需求
- `RepairAppWindow._run_async()`: 异步任务调度器
- `RepairAppWindow.taskFinished`: 跨线程结果传递信号

### 安全考虑
- 使用 subprocess 的 stdin 传递密码，避免命令行泄露
- 线程池限制为单工，避免并发操作冲突
- 正确处理异常和错误码，提供用户友好的错误提示

## 系统兼容性

- 仅支持 macOS (darwin) 平台
- 特别适配 macOS 15 (Sequoia) 的新安全策略
- 支持传统的 spctl 命令和新的系统设置确认流程