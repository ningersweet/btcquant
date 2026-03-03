"""
推理服务

提供模型推理接口
"""

import torch
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = None

from .tcn_model import TCNModel
from .data_loader import normalize_inference_data

logger = logging.getLogger(__name__)


class ModelInference:
    """模型推理器"""
    
    def __init__(
        self,
        model_path: Path,
        device: str = 'cpu',
        use_onnx: bool = True
    ):
        """
        初始化推理器
        
        Args:
            model_path: 模型路径（.pt或.onnx）
            device: 设备
            use_onnx: 是否使用ONNX Runtime（推荐，速度快3-5倍）
        """
        self.device = device
        self.use_onnx = use_onnx and ONNX_AVAILABLE
        
        if self.use_onnx and model_path.suffix == '.onnx':
            # 使用ONNX Runtime
            if not ONNX_AVAILABLE:
                logger.warning("ONNX Runtime not available, falling back to PyTorch")
                self.model = self._load_pytorch_model(model_path.with_suffix('.pt'))
                self.session = None
            else:
                self.session = ort.InferenceSession(
                    str(model_path),
                    providers=['CPUExecutionProvider']
                )
                self.model = None
                logger.info(f"ONNX model loaded from {model_path}")
        else:
            # 使用PyTorch
            self.model = self._load_pytorch_model(model_path)
            self.session = None
            logger.info(f"PyTorch model loaded from {model_path}")
    
    def _load_pytorch_model(self, model_path: Path) -> TCNModel:
        """加载PyTorch模型"""
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # 从checkpoint中获取模型配置（如果有）
        from .tcn_model import create_tcn_model
        model = create_tcn_model()
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        model.to(self.device)
        
        return model
    
    def predict(
        self,
        klines: pd.DataFrame,
        window_size: int = 288
    ) -> Dict:
        """
        预测
        
        Args:
            klines: 最近的K线数据（至少window_size根）
            window_size: 窗口大小
            
        Returns:
            预测结果字典
        """
        if len(klines) < window_size:
            raise ValueError(f"Need at least {window_size} K-lines, got {len(klines)}")
        
        # 提取最近的window_size根K线
        recent_klines = klines.iloc[-window_size:]
        
        # 准备输入数据
        feature_cols = ['open', 'high', 'low', 'close', 'volume']
        x = recent_klines[feature_cols].values
        
        # 标准化
        x_norm = normalize_inference_data(x)
        
        # 推理
        if self.use_onnx and self.session is not None:
            cls_out, reg_out = self._predict_onnx(x_norm)
        else:
            cls_out, reg_out = self._predict_pytorch(x_norm)
        
        # 解析结果
        probs = self._softmax(cls_out[0])
        pred_dir = int(np.argmax(probs))
        confidence = float(probs[pred_dir])
        
        offset, tp_dist, sl_dist = reg_out[0]
        
        result = {
            'direction': pred_dir,  # 0=Hold, 1=Long, 2=Short
            'confidence': confidence,
            'probabilities': {
                'hold': float(probs[0]),
                'long': float(probs[1]),
                'short': float(probs[2])
            },
            'regression': {
                'offset': float(offset),
                'tp_dist': float(tp_dist),
                'sl_dist': float(sl_dist)
            }
        }
        
        return result
    
    def _predict_onnx(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """使用ONNX Runtime推理"""
        x_input = x.astype(np.float32)[np.newaxis, ...]  # (1, window_size, features)
        
        outputs = self.session.run(
            None,
            {'input': x_input}
        )
        
        cls_out = outputs[0]  # (1, 3)
        reg_out = outputs[1]  # (1, 3)
        
        return cls_out, reg_out
    
    def _predict_pytorch(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """使用PyTorch推理"""
        x_tensor = torch.FloatTensor(x).unsqueeze(0).to(self.device)  # (1, window_size, features)
        
        with torch.no_grad():
            cls_out, reg_out = self.model(x_tensor)
        
        cls_out = cls_out.cpu().numpy()
        reg_out = reg_out.cpu().numpy()
        
        return cls_out, reg_out
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax函数"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    def calculate_order_prices(
        self,
        prediction: Dict,
        current_price: float
    ) -> Optional[Dict]:
        """
        根据预测结果计算订单价格
        
        Args:
            prediction: 预测结果
            current_price: 当前价格
            
        Returns:
            订单价格字典，如果不满足条件则返回None
        """
        direction = prediction['direction']
        confidence = prediction['confidence']
        reg = prediction['regression']
        
        # 过滤条件
        if direction == 0:  # Hold
            return None
        
        if confidence < 0.65:  # 置信度过低
            return None
        
        # 计算价格
        offset = reg['offset']
        tp_dist = reg['tp_dist']
        sl_dist = reg['sl_dist']
        
        entry_price = current_price * (1 + offset)
        
        if direction == 1:  # Long
            tp_price = entry_price * (1 + tp_dist)
            sl_price = entry_price * (1 - sl_dist)
            side = 'long'
        else:  # Short
            tp_price = entry_price * (1 - tp_dist)
            sl_price = entry_price * (1 + sl_dist)
            side = 'short'
        
        # 计算盈亏比
        risk = abs(entry_price - sl_price) / entry_price
        reward = abs(tp_price - entry_price) / entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        # 过滤低盈亏比
        if rr_ratio < 1.5:
            return None
        
        return {
            'side': side,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'confidence': confidence,
            'rr_ratio': rr_ratio,
            'estimated_space': reward
        }


def load_inference_model(
    model_dir: Path,
    use_onnx: bool = True,
    device: str = 'cpu'
) -> ModelInference:
    """
    加载推理模型
    
    Args:
        model_dir: 模型目录
        use_onnx: 是否使用ONNX
        device: 设备
        
    Returns:
        ModelInference实例
    """
    if use_onnx:
        onnx_path = model_dir / 'model.onnx'
        if onnx_path.exists():
            return ModelInference(onnx_path, device, use_onnx=True)
        else:
            logger.warning(f"ONNX model not found at {onnx_path}, falling back to PyTorch")
    
    # 使用PyTorch模型
    pt_path = model_dir / 'best_model.pt'
    if not pt_path.exists():
        pt_path = model_dir / 'final_model.pt'
    
    if not pt_path.exists():
        raise FileNotFoundError(f"No model found in {model_dir}")
    
    return ModelInference(pt_path, device, use_onnx=False)
