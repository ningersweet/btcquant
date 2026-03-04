"""
回测评估模块

评估模型在历史数据上的交易表现
"""

import numpy as np
import pandas as pd
import torch
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎
    
    模拟真实交易环境，评估策略表现
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        leverage: int = 20,
        maker_fee: float = 0.0002,  # 0.02%
        taker_fee: float = 0.0004,  # 0.04%
        slippage: float = 0.0001    # 0.01%
    ):
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage = slippage
        
        # 交易记录
        self.trades = []
        self.equity_curve = []
        
        logger.info(f"BacktestEngine initialized: Capital={initial_capital}, Leverage={leverage}x")
    
    def run_backtest(
        self,
        model: torch.nn.Module,
        test_data: pd.DataFrame,
        window_size: int = 288,
        min_confidence: float = 0.65,
        device: str = 'cpu'
    ) -> Dict:
        """
        运行回测
        
        Args:
            model: 训练好的模型
            test_data: 测试数据（包含OHLCV和标签）
            window_size: 输入窗口大小
            min_confidence: 最小置信度阈值
            device: 设备
            
        Returns:
            回测结果字典
        """
        model.eval()
        model.to(device)
        
        capital = self.initial_capital
        position = None  # 当前持仓
        
        feature_cols = ['open', 'high', 'low', 'close', 'volume']
        data_array = test_data[feature_cols].values
        
        logger.info(f"Starting backtest on {len(test_data)} samples...")
        
        with torch.no_grad():
            for i in range(window_size, len(test_data)):
                current_time = test_data.index[i]
                current_price = test_data.iloc[i]['close']
                
                # 检查是否有持仓需要平仓
                if position is not None:
                    exit_signal, exit_reason = self._check_exit(position, test_data.iloc[i], i)
                    
                    if exit_signal:
                        # 平仓
                        pnl = self._close_position(position, current_price, exit_reason)
                        capital += pnl
                        
                        self.equity_curve.append({
                            'timestamp': current_time,
                            'equity': capital,
                            'position': None
                        })
                        
                        position = None
                
                # 如果没有持仓，检查是否有开仓信号
                if position is None:
                    # 准备输入数据
                    x = data_array[i-window_size:i].copy()
                    x = self._normalize(x)
                    x_tensor = torch.FloatTensor(x).unsqueeze(0).to(device)
                    
                    # 模型推理
                    cls_out, reg_out = model(x_tensor)
                    
                    # 获取预测
                    probs = torch.softmax(cls_out, dim=1)[0].cpu().numpy()
                    pred_dir = np.argmax(probs)
                    confidence = probs[pred_dir]
                    
                    reg_values = reg_out[0].cpu().numpy()
                    
                    # 检查是否满足开仓条件
                    if pred_dir != 0 and confidence >= min_confidence:
                        # 计算入场价格和止损止盈
                        entry_price, tp_price, sl_price = self._calculate_prices(
                            current_price, pred_dir, reg_values
                        )
                        
                        # 计算仓位大小
                        position_size = self._calculate_position_size(
                            capital, entry_price, sl_price, pred_dir
                        )
                        
                        if position_size > 0:
                            # 开仓
                            position = {
                                'entry_time': current_time,
                                'entry_index': i,
                                'direction': 'long' if pred_dir == 1 else 'short',
                                'entry_price': entry_price,
                                'tp_price': tp_price,
                                'sl_price': sl_price,
                                'size': position_size,
                                'confidence': confidence,
                                'max_hold_bars': 12  # 最多持有12根K线
                            }
                            
                            logger.debug(f"Open {position['direction']} at {entry_price:.2f}, "
                                       f"TP={tp_price:.2f}, SL={sl_price:.2f}, "
                                       f"Conf={confidence:.3f}")
                
                # 记录权益曲线
                if position is None:
                    self.equity_curve.append({
                        'timestamp': current_time,
                        'equity': capital,
                        'position': None
                    })
        
        # 如果最后还有持仓，强制平仓
        if position is not None:
            final_price = test_data.iloc[-1]['close']
            pnl = self._close_position(position, final_price, 'end_of_data')
            capital += pnl
        
        # 计算回测指标
        metrics = self._calculate_metrics(capital)
        
        logger.info(f"Backtest completed: {len(self.trades)} trades")
        logger.info(f"Final capital: ${capital:.2f} ({(capital/self.initial_capital-1)*100:.2f}%)")
        
        return metrics
    
    def _check_exit(self, position: Dict, current_bar: pd.Series, bar_index: int) -> Tuple[bool, str]:
        """检查是否需要平仓"""
        current_high = current_bar['high']
        current_low = current_bar['low']
        
        # 检查止盈
        if position['direction'] == 'long':
            if current_high >= position['tp_price']:
                return True, 'take_profit'
            if current_low <= position['sl_price']:
                return True, 'stop_loss'
        else:  # short
            if current_low <= position['tp_price']:
                return True, 'take_profit'
            if current_high >= position['sl_price']:
                return True, 'stop_loss'
        
        # 检查时间止损
        bars_held = bar_index - position['entry_index']
        if bars_held >= position['max_hold_bars']:
            return True, 'time_stop'
        
        return False, ''
    
    def _close_position(self, position: Dict, exit_price: float, exit_reason: str) -> float:
        """平仓并计算盈亏"""
        entry_price = position['entry_price']
        size = position['size']
        
        # 计算价格变动
        if position['direction'] == 'long':
            price_change = (exit_price - entry_price) / entry_price
        else:  # short
            price_change = (entry_price - exit_price) / entry_price
        
        # 计算盈亏（考虑杠杆）
        gross_pnl = size * price_change * self.leverage
        
        # 扣除手续费
        entry_fee = size * self.maker_fee  # 假设入场用限价单
        exit_fee = size * self.taker_fee   # 假设出场用市价单
        net_pnl = gross_pnl - entry_fee - exit_fee
        
        # 记录交易
        trade = {
            'entry_time': position['entry_time'],
            'exit_time': datetime.now(),
            'direction': position['direction'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'size': size,
            'pnl': net_pnl,
            'return': net_pnl / size,
            'exit_reason': exit_reason,
            'confidence': position['confidence']
        }
        self.trades.append(trade)
        
        logger.debug(f"Close {position['direction']} at {exit_price:.2f}, "
                    f"PnL=${net_pnl:.2f}, Reason={exit_reason}")
        
        return net_pnl
    
    def _calculate_prices(
        self, 
        current_price: float, 
        direction: int, 
        reg_values: np.ndarray
    ) -> Tuple[float, float, float]:
        """计算入场价、止盈价、止损价"""
        offset, tp_dist, sl_dist = reg_values
        
        # 入场价
        entry_price = current_price * (1 + offset)
        
        if direction == 1:  # long
            tp_price = entry_price * (1 + tp_dist)
            sl_price = entry_price * (1 - sl_dist)
        else:  # short
            tp_price = entry_price * (1 - tp_dist)
            sl_price = entry_price * (1 + sl_dist)
        
        return entry_price, tp_price, sl_price
    
    def _calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        sl_price: float,
        direction: int
    ) -> float:
        """计算仓位大小（基于固定风险）"""
        # 固定风险金额（1%的资金）
        risk_amount = capital * 0.01
        
        # 计算止损距离
        if direction == 1:  # long
            sl_distance = abs(entry_price - sl_price) / entry_price
        else:  # short
            sl_distance = abs(sl_price - entry_price) / entry_price
        
        # 计算仓位大小
        if sl_distance > 0:
            position_size = risk_amount / (sl_distance * self.leverage)
            # 限制最大仓位为资金的50%
            max_size = capital * 0.5
            position_size = min(position_size, max_size)
        else:
            position_size = 0
        
        return position_size
    
    def _normalize(self, x: np.ndarray) -> np.ndarray:
        """Z-Score标准化"""
        mean = x.mean(axis=0, keepdims=True)
        std = x.std(axis=0, keepdims=True) + 1e-8
        return (x - mean) / std
    
    def _calculate_metrics(self, final_capital: float) -> Dict:
        """计算回测指标"""
        if len(self.trades) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'cagr': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0
            }
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        # 基本统计
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 收益率
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # 最大回撤
        equity_series = equity_df['equity'].values
        running_max = np.maximum.accumulate(equity_series)
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # 夏普比率（假设252个交易日）
        returns = trades_df['return'].values
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # 盈利因子
        total_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 平均盈亏
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # 时间止损触发率
        time_stops = len(trades_df[trades_df['exit_reason'] == 'time_stop'])
        time_stop_rate = time_stops / total_trades if total_trades > 0 else 0
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'time_stop_rate': time_stop_rate,
            'final_capital': final_capital
        }
        
        return metrics
    
    def print_metrics(self, metrics: Dict):
        """打印回测指标"""
        print("\n" + "="*60)
        print("回测结果")
        print("="*60)
        print(f"总交易次数: {metrics['total_trades']}")
        
        if metrics['total_trades'] > 0:
            print(f"盈利交易: {metrics['winning_trades']}")
            print(f"亏损交易: {metrics['losing_trades']}")
            print(f"胜率: {metrics['win_rate']*100:.2f}%")
            print(f"总收益率: {metrics['total_return']*100:.2f}%")
            print(f"最大回撤: {metrics['max_drawdown']*100:.2f}%")
            print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
            print(f"盈利因子: {metrics['profit_factor']:.2f}")
            print(f"平均盈利: ${metrics['avg_win']:.2f}")
            print(f"平均亏损: ${metrics['avg_loss']:.2f}")
            print(f"时间止损率: {metrics['time_stop_rate']*100:.2f}%")
            print(f"最终资金: ${metrics['final_capital']:.2f}")
        else:
            print("无交易记录")
            print(f"最终资金: ${metrics.get('final_capital', 0):.2f}")
        
        print("="*60)
