#!/usr/bin/env bash
# BestIP 启动脚本 (Linux/Mac)
# 版本: 2.0
# 描述: Cloudflare IP 优选工具启动脚本

set -euo pipefail  # 严格错误处理: -e 遇错退出, -u 未定义变量报错, -o pipefail 管道错误传播

# ============================================
# 全局变量
# ============================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="${SCRIPT_DIR}"
readonly MAIN_SCRIPT="${PROJECT_ROOT}/src/main.py"
readonly REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
readonly MIN_PYTHON_VERSION="3.7"

# 颜色定义
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'

# ============================================
# 工具函数
# ============================================

# 打印带颜色的消息
print_message() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${COLOR_RESET}"
}

# 打印标题
print_header() {
    echo
    print_message "${COLOR_CYAN}" "============================================"
    print_message "${COLOR_CYAN}" "  BestIP - Cloudflare 优选IP工具"
    print_message "${COLOR_CYAN}" "============================================"
    echo
}

# 打印错误并退出
error_exit() {
    print_message "${COLOR_RED}" "❌ 错误: $1" >&2
    exit "${2:-1}"
}

# 打印警告
print_warning() {
    print_message "${COLOR_YELLOW}" "⚠️  警告: $1"
}

# 打印成功消息
print_success() {
    print_message "${COLOR_GREEN}" "✅ $1"
}

# 打印信息
print_info() {
    print_message "${COLOR_BLUE}" "ℹ️  $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
    -h, --help          显示此帮助信息
    -v, --version       显示版本信息
    --skip-deps         跳过依赖检查
    --verbose           显示详细输出

示例:
    $0                  # 正常启动
    $0 --skip-deps      # 跳过依赖检查启动
    $0 --verbose        # 详细模式启动

所有其他参数将传递给主程序。
EOF
}

# 显示版本信息
show_version() {
    echo "BestIP v2.0"
    echo "Cloudflare IP 优选工具"
}

# ============================================
# 检查函数
# ============================================

# 检查命令是否存在
command_exists() {
    command -v "$1" &> /dev/null
}

# 比较版本号
version_compare() {
    local version1="$1"
    local version2="$2"

    if [[ "$(printf '%s\n' "$version1" "$version2" | sort -V | head -n1)" == "$version2" ]]; then
        return 0  # version1 >= version2
    else
        return 1  # version1 < version2
    fi
}

# 检查 Python 版本
check_python() {
    print_info "检查 Python 环境..."

    local python_cmd=""

    # 尝试查找可用的 Python 命令
    for cmd in python3 python; do
        if command_exists "$cmd"; then
            python_cmd="$cmd"
            break
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        error_exit "未检测到 Python，请先安装 Python ${MIN_PYTHON_VERSION}+" 1
    fi

    # 检查 Python 版本
    local python_version
    python_version=$("$python_cmd" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "0.0")

    if ! version_compare "$python_version" "$MIN_PYTHON_VERSION"; then
        error_exit "Python 版本过低 (当前: ${python_version}, 需要: ${MIN_PYTHON_VERSION}+)" 1
    fi

    print_success "Python 版本: ${python_version}"
    echo "$python_cmd"
}

# 检查并安装依赖
check_dependencies() {
    local python_cmd="$1"

    print_info "检查 Python 依赖..."

    # 检查 requirements.txt 是否存在
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_warning "未找到 requirements.txt，跳过依赖检查"
        return 0
    fi

    # 检查关键依赖
    if ! "$python_cmd" -c "import requests" &> /dev/null; then
        print_info "检测到缺失依赖，正在安装..."

        # 尝试使用 pip3 或 pip
        local pip_cmd=""
        for cmd in pip3 pip; do
            if command_exists "$cmd"; then
                pip_cmd="$cmd"
                break
            fi
        done

        if [[ -z "$pip_cmd" ]]; then
            error_exit "未找到 pip，请先安装 pip" 1
        fi

        # 安装依赖
        if ! "$pip_cmd" install -r "$REQUIREMENTS_FILE"; then
            error_exit "依赖安装失败，请检查网络连接或手动安装" 1
        fi

        print_success "依赖安装完成"
    else
        print_success "依赖检查通过"
    fi
}

# 检查主程序文件
check_main_script() {
    if [[ ! -f "$MAIN_SCRIPT" ]]; then
        error_exit "未找到主程序文件: ${MAIN_SCRIPT}" 1
    fi
}

# ============================================
# 主函数
# ============================================

main() {
    local skip_deps=false
    local verbose=false
    local args=()

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            --skip-deps)
                skip_deps=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done

    # 启用详细模式
    if [[ "$verbose" == true ]]; then
        set -x
    fi

    # 打印标题
    print_header

    # 检查 Python
    local python_cmd
    python_cmd=$(check_python)

    # 检查依赖
    if [[ "$skip_deps" == false ]]; then
        check_dependencies "$python_cmd"
    else
        print_warning "已跳过依赖检查"
    fi

    # 检查主程序
    check_main_script

    # 运行主程序
    echo
    print_info "启动程序..."
    echo

    # 切换到项目根目录
    cd "$PROJECT_ROOT" || error_exit "无法切换到项目目录: ${PROJECT_ROOT}" 1

    # 执行主程序，传递所有参数
    exec "$python_cmd" "$MAIN_SCRIPT" "${args[@]}"
}

# ============================================
# 脚本入口
# ============================================

# 捕获 Ctrl+C
trap 'echo; print_warning "程序被用户中断"; exit 130' INT

# 执行主函数
main "$@"
