#!/bin/bash

# macOS修复助手 安装脚本
# 将应用程序复制到应用程序文件夹

echo "📦 正在安装 macOS修复助手..."

# 检查应用程序是否存在
if [ ! -d "dist/macOS修复助手.app" ]; then
    echo "❌ 错误：找不到 macOS修复助手.app"
    echo "请先运行打包命令：pyinstaller build_app.spec --clean"
    exit 1
fi

# 复制到应用程序文件夹
echo "📂 正在复制到 /Applications/..."
cp -R "dist/macOS修复助手.app" "/Applications/"

if [ $? -eq 0 ]; then
    echo "✅ 安装成功！"
    echo ""
    echo "🎉 macOS修复助手 已安装到应用程序文件夹"
    echo "您现在可以："
    echo "1. 在启动台中找到并打开应用程序"
    echo "2. 在应用程序文件夹中双击启动"
    echo "3. 使用 Spotlight 搜索'macOS修复助手'"
    echo ""
    echo "💡 提示：首次运行时，系统可能会要求您确认打开来自未知开发者的应用程序"
else
    echo "❌ 安装失败！请检查权限或手动复制应用程序"
fi