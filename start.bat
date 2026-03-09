@echo off
chcp 65001 >nul
title 客户信息管理系统

echo ========================================
echo   客户信息管理系统
echo ========================================
echo.

cd /d "%~dp0"

echo 正在检查依赖...

python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo 发现缺失依赖，正在安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo.
echo 服务器启动中: http://127.0.0.1:5688
echo.

start /b python run.py >nul 2>&1

timeout /t 2 /nobreak >nul

start http://127.0.0.1:5688

echo 浏览器已打开，按 Ctrl+C 停止服务器
