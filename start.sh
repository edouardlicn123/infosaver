#!/bin/bash

# 客户信息管理系统启动脚本

cd "$(dirname "$0")"

echo "正在启动客户信息管理系统..."

# 检查并安装依赖
check_package() {
    python3 -c "import $1" 2>/dev/null
}

MISSING=()

for pkg in flask pandas openpyxl; do
    if ! check_package "${pkg%==*}"; then
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "正在安装缺失的依赖: ${MISSING[*]}"
    pip install --break-system-packages -r requirements.txt
fi

# 启动服务器并自动打开浏览器
echo "服务器启动中: http://127.0.0.1:5000"
python3 run.py &
sleep 2

# 自动打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open http://127.0.0.1:5000
elif command -v gnome-open &> /dev/null; then
    gnome-open http://127.0.0.1:5000
elif command -v open &> /dev/null; then
    open http://127.0.0.1:5000
fi
