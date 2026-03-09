@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   GitHub 备份脚本
echo ========================================
echo.

git status --porcelain > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "%STATUS%"=="" (
    echo 没有需要备份的更改
    pause
    exit /b 0
)

echo 发现以下更改:
git status --short
echo.

for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set date=%%a-%%b-%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set time=%%a:%%b
)
set "MSG=Backup %date% %time%"

echo 提交信息: %MSG%
echo.

set /p confirm="确认提交并推送到 GitHub? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo 正在提交...
git add -A
git commit -m "%MSG%"

echo.
echo 正在推送到 GitHub...
git push origin main

echo.
echo ========================================
echo   备份完成！
echo ========================================
pause
