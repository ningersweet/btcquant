#!/usr/bin/env python3
"""
训练完成后的自动化脚本

功能：
1. 将训练好的模型从GPU服务器传输到CPU服务器
2. 发送邮件通知用户训练完成
"""

import os
import sys
import json
import smtplib
import subprocess
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


def get_latest_model_dir(models_dir: Path) -> Path:
    """获取最新的模型目录"""
    model_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name.startswith('tcn_')]
    if not model_dirs:
        raise FileNotFoundError("未找到训练好的模型")
    
    # 按修改时间排序，返回最新的
    latest_dir = max(model_dirs, key=lambda d: d.stat().st_mtime)
    return latest_dir


def get_training_summary(model_dir: Path) -> dict:
    """读取训练摘要信息"""
    summary = {
        'model_dir': model_dir.name,
        'model_size': 0,
        'training_time': 'Unknown',
        'best_epoch': 'Unknown',
        'val_loss': 'Unknown',
        'val_accuracy': 'Unknown'
    }
    
    # 读取模型大小
    best_model = model_dir / 'best_model.pt'
    if best_model.exists():
        summary['model_size'] = f"{best_model.stat().st_size / 1024 / 1024:.2f} MB"
    
    # 读取训练历史
    history_file = model_dir / 'training_history.json'
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
            if history and 'val_loss' in history:
                # history是字典，包含val_loss列表
                val_losses = history['val_loss']
                if val_losses:
                    best_epoch_idx = val_losses.index(min(val_losses))
                    summary['best_epoch'] = best_epoch_idx + 1
                    summary['val_loss'] = f"{val_losses[best_epoch_idx]:.4f}"
                    if 'val_accuracy' in history and history['val_accuracy']:
                        summary['val_accuracy'] = f"{history['val_accuracy'][best_epoch_idx]:.2%}"
    
    return summary


def transfer_model_to_cpu_server(model_dir: Path, cpu_server: str, remote_path: str) -> bool:
    """将模型传输到CPU服务器"""
    print(f"开始传输模型到CPU服务器: {cpu_server}")
    print(f"本地路径: {model_dir}")
    print(f"远程路径: {remote_path}")
    
    try:
        # 使用rsync传输（更高效，支持断点续传）
        cmd = [
            'rsync',
            '-avz',
            '--progress',
            str(model_dir) + '/',
            f'{cpu_server}:{remote_path}/{model_dir.name}/'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ 模型传输成功")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 模型传输失败: {e}")
        print(e.stderr)
        return False
    except FileNotFoundError:
        # rsync不可用，尝试使用scp
        print("rsync不可用，使用scp传输...")
        try:
            cmd = [
                'scp',
                '-r',
                str(model_dir),
                f'{cpu_server}:{remote_path}/'
            ]
            subprocess.run(cmd, check=True)
            print("✓ 模型传输成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 模型传输失败: {e}")
            return False


def send_email_notification(
    summary: dict,
    transfer_success: bool,
    smtp_config: dict
) -> bool:
    """发送邮件通知"""
    print("发送邮件通知...")
    
    try:
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[BTC Quant] 模型训练完成 - {summary['model_dir']}"
        msg['From'] = smtp_config['from_email']
        msg['To'] = smtp_config['to_email']
        
        # 邮件内容
        status_icon = "✅" if transfer_success else "⚠️"
        transfer_status = "成功" if transfer_success else "失败"
        
        text_content = f"""
BTC量化交易模型训练完成

模型信息：
- 模型目录: {summary['model_dir']}
- 模型大小: {summary['model_size']}
- 最佳Epoch: {summary['best_epoch']}
- 验证损失: {summary['val_loss']}
- 验证准确率: {summary['val_accuracy']}

模型传输状态: {status_icon} {transfer_status}

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'现在可以释放GPU服务器了。' if transfer_success else '请手动检查模型传输问题。'}
"""
        
        html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
        .info-box {{ background: white; padding: 15px; margin: 10px 0; 
                     border-left: 4px solid #667eea; border-radius: 4px; }}
        .status-success {{ color: #10b981; font-weight: bold; }}
        .status-failed {{ color: #ef4444; font-weight: bold; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; 
                   font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎉 BTC量化交易模型训练完成</h2>
        </div>
        <div class="content">
            <div class="info-box">
                <h3>📊 模型信息</h3>
                <ul>
                    <li><strong>模型目录:</strong> {summary['model_dir']}</li>
                    <li><strong>模型大小:</strong> {summary['model_size']}</li>
                    <li><strong>最佳Epoch:</strong> {summary['best_epoch']}</li>
                    <li><strong>验证损失:</strong> {summary['val_loss']}</li>
                    <li><strong>验证准确率:</strong> {summary['val_accuracy']}</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>🚀 模型传输状态</h3>
                <p class="{'status-success' if transfer_success else 'status-failed'}">
                    {status_icon} {transfer_status}
                </p>
            </div>
            
            <div class="info-box">
                <h3>⏰ 完成时间</h3>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="info-box">
                <h3>💡 下一步</h3>
                <p>{'✅ 现在可以释放GPU服务器了。' if transfer_success else '⚠️ 请手动检查模型传输问题。'}</p>
            </div>
        </div>
        <div class="footer">
            <p>此邮件由BTC Quant自动发送，请勿回复。</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 添加文本和HTML版本
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # 发送邮件
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            if smtp_config.get('use_tls', True):
                server.starttls()
            if smtp_config.get('smtp_user') and smtp_config.get('smtp_password'):
                server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
            server.send_message(msg)
        
        print("✓ 邮件发送成功")
        return True
        
    except Exception as e:
        print(f"✗ 邮件发送失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='训练完成后的自动化处理')
    parser.add_argument('--model-dir', type=str, help='模型目录路径（留空则自动检测最新）')
    parser.add_argument('--cpu-server', type=str, default='cpu_server', help='CPU服务器SSH别名')
    parser.add_argument('--remote-path', type=str, default='/root/workspace/btcquant/storage/models', 
                        help='CPU服务器上的模型存储路径')
    parser.add_argument('--skip-transfer', action='store_true', help='跳过模型传输')
    parser.add_argument('--skip-email', action='store_true', help='跳过邮件通知')
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config()
    
    # 获取模型目录
    if args.model_dir:
        model_dir = Path(args.model_dir)
    else:
        # 使用统一的models目录
        models_dir = config.models_directory
        model_dir = get_latest_model_dir(models_dir)
    
    print(f"处理模型: {model_dir}")
    
    # 获取训练摘要
    summary = get_training_summary(model_dir)
    print("\n训练摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 传输模型
    transfer_success = True
    if not args.skip_transfer:
        print("\n" + "="*50)
        transfer_success = transfer_model_to_cpu_server(
            model_dir, 
            args.cpu_server, 
            args.remote_path
        )
    else:
        print("\n跳过模型传输")
    
    # 发送邮件通知
    if not args.skip_email:
        print("\n" + "="*50)
        
        # 从config.yaml读取SMTP配置（优先环境变量）
        smtp_config = {
            'smtp_server': config.smtp_server,
            'smtp_port': config.smtp_port,
            'smtp_user': config.smtp_user,
            'smtp_password': config.smtp_password,
            'from_email': config.from_email,
            'to_email': config.to_email,
            'use_tls': config.smtp_use_tls
        }
        
        # 检查必需的配置
        if not smtp_config['smtp_user'] or not smtp_config['smtp_password']:
            print("⚠️ 未配置SMTP信息，跳过邮件发送")
            print("请在 config.yaml 中配置邮件信息，或设置环境变量:")
            print("  SMTP_USER, SMTP_PASSWORD, TO_EMAIL")
        else:
            print(f"邮件配置: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
            print(f"发送至: {smtp_config['to_email']}")
            send_email_notification(summary, transfer_success, smtp_config)
    else:
        print("\n跳过邮件通知")
    
    print("\n" + "="*50)
    print("✓ 处理完成")
    
    return 0 if transfer_success else 1


if __name__ == '__main__':
    sys.exit(main())
