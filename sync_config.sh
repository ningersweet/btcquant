#!/bin/bash
# 配置文件同步脚本
# 用于将本地配置文件同步到服务器

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 服务器配置
CPU_SERVER="${CPU_SERVER:-cpu_server}"
GPU_SERVER="${GPU_SERVER:-gpu_server}"
CPU_PROJECT_DIR="/root/workspace/btcquant"
GPU_PROJECT_DIR="~/workspace/btcquant"

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 检查配置文件是否存在
check_config_files() {
    local missing=0
    
    if [ ! -f "config.yaml" ]; then
        print_warning "config.yaml 不存在，将使用示例配置"
        if [ -f "config.yaml.example" ]; then
            cp config.yaml.example config.yaml
            print_success "已从 config.yaml.example 创建 config.yaml"
            print_warning "请编辑 config.yaml 填入真实配置"
            missing=1
        fi
    fi
    
    if [ ! -f "predict/config.yaml" ]; then
        print_warning "predict/config.yaml 不存在，将使用示例配置"
        if [ -f "predict/config.yaml.example" ]; then
            cp predict/config.yaml.example predict/config.yaml
            print_success "已从 predict/config.yaml.example 创建 predict/config.yaml"
            print_warning "请编辑 predict/config.yaml 填入真实配置"
            missing=1
        fi
    fi
    
    return $missing
}

# 同步到CPU服务器
sync_to_cpu() {
    print_header "同步配置到CPU服务器"
    
    echo "同步 config.yaml..."
    scp config.yaml $CPU_SERVER:$CPU_PROJECT_DIR/
    print_success "config.yaml 已同步"
    
    echo "同步 predict/config.yaml..."
    scp predict/config.yaml $CPU_SERVER:$CPU_PROJECT_DIR/predict/
    print_success "predict/config.yaml 已同步"
    
    print_success "CPU服务器配置同步完成"
}

# 同步到GPU服务器
sync_to_gpu() {
    print_header "同步配置到GPU服务器"
    
    echo "同步 config.yaml..."
    scp config.yaml $GPU_SERVER:$GPU_PROJECT_DIR/
    print_success "config.yaml 已同步"
    
    echo "同步 predict/config.yaml..."
    scp predict/config.yaml $GPU_SERVER:$GPU_PROJECT_DIR/predict/
    print_success "predict/config.yaml 已同步"
    
    # 同步邮件配置（如果存在）
    if [ -f "predict/.env.email" ]; then
        echo "同步 predict/.env.email..."
        scp predict/.env.email $GPU_SERVER:$GPU_PROJECT_DIR/predict/
        print_success "predict/.env.email 已同步"
    else
        print_warning "predict/.env.email 不存在，跳过"
    fi
    
    print_success "GPU服务器配置同步完成"
}

# 备份配置文件
backup_config() {
    print_header "备份配置文件"
    
    local backup_dir="$HOME/backup/btcquant_config"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    mkdir -p "$backup_dir"
    
    # 从CPU服务器备份
    echo "从CPU服务器备份配置..."
    scp $CPU_SERVER:$CPU_PROJECT_DIR/config.yaml "$backup_dir/config_cpu_$timestamp.yaml"
    scp $CPU_SERVER:$CPU_PROJECT_DIR/predict/config.yaml "$backup_dir/predict_config_cpu_$timestamp.yaml"
    
    # 从GPU服务器备份
    echo "从GPU服务器备份配置..."
    scp $GPU_SERVER:$GPU_PROJECT_DIR/config.yaml "$backup_dir/config_gpu_$timestamp.yaml"
    scp $GPU_SERVER:$GPU_PROJECT_DIR/predict/config.yaml "$backup_dir/predict_config_gpu_$timestamp.yaml"
    
    print_success "配置文件已备份到: $backup_dir"
    ls -lh "$backup_dir" | tail -5
}

# 显示帮助
show_help() {
    cat << EOF
配置文件同步脚本

用法: $0 <命令>

命令:
  cpu       同步配置到CPU服务器
  gpu       同步配置到GPU服务器
  all       同步配置到所有服务器
  backup    备份服务器上的配置文件
  check     检查本地配置文件
  help      显示此帮助信息

示例:
  $0 cpu        # 同步到CPU服务器
  $0 gpu        # 同步到GPU服务器
  $0 all        # 同步到所有服务器
  $0 backup     # 备份配置文件

注意:
  - 配置文件包含敏感信息，不会提交到Git
  - 修改配置后必须手动同步到服务器
  - 建议定期备份配置文件

EOF
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    local command=$1
    
    case $command in
        cpu)
            check_config_files
            sync_to_cpu
            ;;
        gpu)
            check_config_files
            sync_to_gpu
            ;;
        all)
            check_config_files
            sync_to_cpu
            echo ""
            sync_to_gpu
            ;;
        backup)
            backup_config
            ;;
        check)
            print_header "检查配置文件"
            if check_config_files; then
                print_success "所有配置文件已就绪"
            else
                print_warning "请编辑配置文件后再同步"
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"
