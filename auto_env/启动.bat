@echo off
chcp 65001 >nul 2>nul
title AutoEnv - 万能开源项目环境一键配置
cd /d "%~dp0"

:menu
cls
echo ============================================================
echo    🚀  AutoEnv — 万能开源项目环境一键配置
echo ============================================================
echo.
echo    [1] 输入 GitHub 仓库 URL（自动下载 + 检测 + 安装）
echo    [2] 输入本地项目路径（检测 + 安装）
echo    [3] 检测当前目录（auto_env 所在目录）
echo    [4] 全自动模式（跳过确认，直接安装全部）
echo    [5] 只看报告，不安装
echo    [6] 生成 Dockerfile / Dev Container
echo    [0] 退出
echo.
echo ============================================================
set /p choice="   请选择 [0-6]: "

if "%choice%"=="0" goto end
if "%choice%"=="1" goto url_mode
if "%choice%"=="2" goto local_mode
if "%choice%"=="3" goto current_mode
if "%choice%"=="4" goto auto_mode
if "%choice%"=="5" goto report_mode
if "%choice%"=="6" goto generate_mode
goto menu

:url_mode
cls
echo.
echo   请输入 GitHub 仓库 URL（支持 git clone 和 ZIP 下载）:
echo.
echo   例: https://github.com/psf/requests
echo   例: https://github.com/tiangolo/fastapi
echo   例: git@github.com:user/repo.git
echo.
set /p url="   👉 URL: "
if "%url%"=="" goto menu
echo.
python -m auto_env "%url%"
goto done

:local_mode
cls
echo.
echo   请输入项目本地路径:
echo.
echo   例: C:\projects\my-app
echo   例: .\my-project
echo.
set /p path="   👉 路径: "
if "%path%"=="" goto menu
echo.
python -m auto_env "%path%"
goto done

:current_mode
echo.
python -m auto_env .
goto done

:auto_mode
cls
echo.
echo   请输入项目路径或 GitHub URL（全自动安装，跳过确认）:
echo.
set /p target="   👉: "
if "%target%"=="" goto menu
echo.
python -m auto_env "%target%" -y
goto done

:report_mode
cls
echo.
echo   请输入项目路径或 GitHub URL（仅检测报告）:
echo.
set /p target="   👉: "
if "%target%"=="" goto menu
echo.
python -m auto_env "%target%" --no-install
goto done

:generate_mode
cls
echo.
echo   请输入项目路径或 GitHub URL（生成 Dockerfile）:
echo.
set /p target="   👉: "
if "%target%"=="" goto menu
echo.
python -m auto_env "%target%" --generate
goto done

:done
echo.
echo   按任意键返回菜单...
pause >nul
goto menu

:end
exit
