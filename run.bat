@echo off
REM ============================================
REM BestIP 启动脚本 (Windows)
REM 版本: 2.0
REM 描述: Cloudflare IP 优选工具启动脚本
REM ============================================

setlocal enabledelayedexpansion

REM ============================================
REM 全局变量
REM ============================================
set "SCRIPT_VERSION=2.0"
set "MIN_PYTHON_VERSION=3.7"
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "MAIN_SCRIPT=%PROJECT_ROOT%src\main.py"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%requirements.txt"

REM 颜色代码 (Windows 10+ 支持 ANSI 转义序列)
set "COLOR_RESET=[0m"
set "COLOR_RED=[91m"
set "COLOR_GREEN=[92m"
set "COLOR_YELLOW=[93m"
set "COLOR_BLUE=[94m"
set "COLOR_CYAN=[96m"

REM 启用 ANSI 颜色支持 (Windows 10+)
reg query "HKCU\Console" /v VirtualTerminalLevel >nul 2>&1
if %errorlevel% neq 0 (
    reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
)

REM 参数标志
set "SKIP_DEPS=0"
set "VERBOSE=0"
set "NO_PAUSE=0"
set "SHOW_HELP=0"
set "SHOW_VERSION=0"

REM ============================================
REM 解析命令行参数
REM ============================================
set "EXTRA_ARGS="
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="-h" set "SHOW_HELP=1" & shift & goto :parse_args
if /i "%~1"=="--help" set "SHOW_HELP=1" & shift & goto :parse_args
if /i "%~1"=="-v" set "SHOW_VERSION=1" & shift & goto :parse_args
if /i "%~1"=="--version" set "SHOW_VERSION=1" & shift & goto :parse_args
if /i "%~1"=="--skip-deps" set "SKIP_DEPS=1" & shift & goto :parse_args
if /i "%~1"=="--verbose" set "VERBOSE=1" & shift & goto :parse_args
if /i "%~1"=="--no-pause" set "NO_PAUSE=1" & shift & goto :parse_args
set "EXTRA_ARGS=!EXTRA_ARGS! %~1"
shift
goto :parse_args

:args_done

REM ============================================
REM 处理帮助和版本信息
REM ============================================
if "%SHOW_HELP%"=="1" (
    call :show_help
    exit /b 0
)

if "%SHOW_VERSION%"=="1" (
    call :show_version
    exit /b 0
)

REM ============================================
REM 主程序流程
REM ============================================
call :print_header

REM 检查 Python
call :check_python
if %errorlevel% neq 0 exit /b 1

REM 检查依赖
if "%SKIP_DEPS%"=="0" (
    call :check_dependencies
    if %errorlevel% neq 0 exit /b 1
) else (
    call :print_warning "已跳过依赖检查"
)

REM 检查主程序文件
call :check_main_script
if %errorlevel% neq 0 exit /b 1

REM 运行主程序
echo.
call :print_info "启动程序..."
echo.

REM 切换到项目根目录
cd /d "%PROJECT_ROOT%" 2>nul
if %errorlevel% neq 0 (
    call :error_exit "无法切换到项目目录: %PROJECT_ROOT%" 1
)

REM 启用详细模式
if "%VERBOSE%"=="1" (
    echo %COLOR_CYAN%[详细模式] 执行命令: python "%MAIN_SCRIPT%" %EXTRA_ARGS%%COLOR_RESET%
    echo.
)

REM 执行主程序
python "%MAIN_SCRIPT%" %EXTRA_ARGS%
set "EXIT_CODE=%errorlevel%"

REM 处理退出
echo.
if %EXIT_CODE% equ 0 (
    call :print_success "程序执行完成"
) else (
    call :print_error "程序执行失败 (退出码: %EXIT_CODE%)"
)

if "%NO_PAUSE%"=="0" pause
exit /b %EXIT_CODE%

REM ============================================
REM 工具函数
REM ============================================

:print_message
REM 参数: %1=颜色, %2=消息
echo %~1%~2%COLOR_RESET%
exit /b 0

:print_header
echo.
echo %COLOR_CYAN%============================================%COLOR_RESET%
echo %COLOR_CYAN%  BestIP - Cloudflare 优选IP工具%COLOR_RESET%
echo %COLOR_CYAN%============================================%COLOR_RESET%
echo.
exit /b 0

:print_error
echo %COLOR_RED%[X] 错误: %~1%COLOR_RESET% 1>&2
exit /b 0

:print_warning
echo %COLOR_YELLOW%[!] 警告: %~1%COLOR_RESET%
exit /b 0

:print_success
echo %COLOR_GREEN%[√] %~1%COLOR_RESET%
exit /b 0

:print_info
echo %COLOR_BLUE%[i] %~1%COLOR_RESET%
exit /b 0

:error_exit
call :print_error "%~1"
if "%NO_PAUSE%"=="0" pause
exit /b %~2

:show_help
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo     -h, --help          显示此帮助信息
echo     -v, --version       显示版��信息
echo     --skip-deps         跳过依赖检查
echo     --verbose           显示详细输出
echo     --no-pause          执行完成后不暂停
echo.
echo 示例:
echo     %~nx0                  # 正常启动
echo     %~nx0 --skip-deps      # 跳过依赖检查启动
echo     %~nx0 --verbose        # 详细模式启动
echo     %~nx0 --no-pause       # 不暂停模式
echo.
echo 所有其他参数将传递给主程序。
exit /b 0

:show_version
echo BestIP v%SCRIPT_VERSION%
echo Cloudflare IP 优选工具
exit /b 0

REM ============================================
REM 检查函数
REM ============================================

:check_python
call :print_info "检查 Python 环境..."

REM 尝试查找 Python
set "PYTHON_CMD="
for %%p in (python python3 py) do (
    where %%p >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=%%p"
        goto :python_found
    )
)

:python_found
if "%PYTHON_CMD%"=="" (
    call :error_exit "未检测到 Python，请先安装 Python %MIN_PYTHON_VERSION%+" 1
    exit /b 1
)

REM 检查 Python 版本
for /f "tokens=2 delims= " %%v in ('%PYTHON_CMD% --version 2^>^&1') do set "PYTHON_VERSION=%%v"

REM 提取主版本号和次版本号
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

REM 简单版本检查 (3.7+)
if %PY_MAJOR% lss 3 (
    call :error_exit "Python 版本过低 (当前: %PYTHON_VERSION%, 需要: %MIN_PYTHON_VERSION%+)" 1
    exit /b 1
)
if %PY_MAJOR% equ 3 if %PY_MINOR% lss 7 (
    call :error_exit "Python 版本过低 (当前: %PYTHON_VERSION%, 需要: %MIN_PYTHON_VERSION%+)" 1
    exit /b 1
)

call :print_success "Python 版本: %PYTHON_VERSION%"
exit /b 0

:check_dependencies
call :print_info "检查 Python 依赖..."

REM 检查 requirements.txt 是否存在
if not exist "%REQUIREMENTS_FILE%" (
    call :print_warning "未找到 requirements.txt，跳过依赖检查"
    exit /b 0
)

REM 检查关键依赖 (requests)
%PYTHON_CMD% -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    call :print_info "检测到缺失依赖，正在安装..."

    REM 尝试查找 pip
    set "PIP_CMD="
    for %%p in (pip pip3 py -m pip) do (
        where %%p >nul 2>&1
        if !errorlevel! equ 0 (
            set "PIP_CMD=%%p"
            goto :pip_found
        )
    )

    :pip_found
    if "!PIP_CMD!"=="" (
        call :error_exit "未找到 pip，请先安装 pip" 1
        exit /b 1
    )

    REM 安装依赖
    !PIP_CMD! install -r "%REQUIREMENTS_FILE%"
    if !errorlevel! neq 0 (
        call :error_exit "依赖安装失败，请检查网络连接或手动安装" 1
        exit /b 1
    )

    call :print_success "依赖安装完成"
) else (
    call :print_success "依赖检查通过"
)
exit /b 0

:check_main_script
if not exist "%MAIN_SCRIPT%" (
    call :error_exit "未找到主程序文件: %MAIN_SCRIPT%" 1
    exit /b 1
)
exit /b 0

REM ============================================
REM 脚本结束
REM ============================================
