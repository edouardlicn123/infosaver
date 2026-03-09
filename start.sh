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

# 启动服务器
echo "服务器启动中: http://127.0.0.1:5000"
python3 run.py
