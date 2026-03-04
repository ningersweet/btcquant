#!/usr/bin/env python3
"""
带通知的训练脚本

在训练完成后自动执行：
1. 模型传输到CPU服务器
2. 发送邮件通知
"""

import sys
import subprocess
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser(description='训练模型并在完成后自动处理')
    parser.add_argument('--train-script', type=str, default='train_cached.py', 
                        help='训练脚本名称')
    parser.add_argument('--cpu-server', type=str, default='cpu_server', 
                        help='CPU服务器SSH别名')
    parser.add_argument('--skip-transfer', action='store_true', 
                        help='跳过模型传输')
    parser.add_argument('--skip-email', action='store_true', 
                        help='跳过邮件通知')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    train_script = script_dir / args.train_script
    
    if not train_script.exists():
        print(f"错误: 训练脚本不存在: {train_script}")
        return 1
    
    print("="*60)
    print("开始训练...")
    print("="*60)
    
    # 执行训练
    try:
        result = subprocess.run(
            [sys.executable, str(train_script)],
            cwd=script_dir,
            check=True
        )
        print("\n" + "="*60)
        print("✓ 训练完成")
        print("="*60)
        
    except subprocess.CalledProcessError as e:
        print("\n" + "="*60)
        print(f"✗ 训练失败: {e}")
        print("="*60)
        return 1
    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("训练被用户中断")
        print("="*60)
        return 1
    
    # 执行训练后处理
    print("\n" + "="*60)
    print("开始训练后处理...")
    print("="*60)
    
    post_script = script_dir / 'post_training.py'
    cmd = [sys.executable, str(post_script), '--cpu-server', args.cpu_server]
    
    if args.skip_transfer:
        cmd.append('--skip-transfer')
    if args.skip_email:
        cmd.append('--skip-email')
    
    try:
        subprocess.run(cmd, cwd=script_dir, check=True)
        print("\n" + "="*60)
        print("✓ 全部完成！")
        print("="*60)
        return 0
        
    except subprocess.CalledProcessError as e:
        print("\n" + "="*60)
        print(f"⚠️ 训练后处理失败: {e}")
        print("但训练已成功完成，请手动检查")
        print("="*60)
        return 0  # 训练成功，只是后处理失败


if __name__ == '__main__':
    sys.exit(main())
