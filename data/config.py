"""
数据服务配置模块

从 YAML 配置文件加载配置
"""

import os

try:
    from common.config_loader import get_config, get_section
except ImportError:
    # 如果无法导入，使用默认值
    def get_config(key, default=None):
        return default
    def get_section(section):
        return {}


class BinanceConfig:
    """Binance API 配置"""
    
    @property
    def api_key(self) -> str:
        return os.getenv("BINANCE_API_KEY", "")
    
    @property
    def api_secret(self) -> str:
        return os.getenv("BINANCE_API_SECRET", "")
    
    @property
    def base_url(self) -> str:
        return get_config("data.binance.base_url", "https://fapi.binance.com")
    
    @property
    def testnet_url(self) -> str:
        return get_config("data.binance.testnet_url", "https://testnet.binancefuture.com")
    
    @property
    def use_testnet(self) -> bool:
        return get_config("data.binance.use_testnet", False)
    
    @property
    def url(self) -> str:
        return self.testnet_url if self.use_testnet else self.base_url


class DatabaseConfig:
    """数据库配置"""
    
    @property
    def db_path(self) -> str:
        return os.getenv("DB_PATH", get_config("data.database.db_path", "/app/data_storage/btc_quant.db"))
    
    @property
    def echo(self) -> bool:
        return get_config("data.database.echo", False)


class DataServiceConfig:
    """数据服务主配置"""
    
    def __init__(self):
        self.binance = BinanceConfig()
        self.database = DatabaseConfig()
    
    @property
    def symbol(self) -> str:
        return get_config("data.symbol", "BTCUSDT")
    
    @property
    def interval(self) -> str:
        return get_config("data.interval", "1h")
    
    @property
    def host(self) -> str:
        return get_config("data.host", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return get_config("data.port", 8001)
    
    @property
    def max_klines_per_request(self) -> int:
        return get_config("data.binance.max_klines_per_request", 1500)
    
    @property
    def request_timeout(self) -> int:
        return get_config("data.binance.request_timeout", 30)
    
    @property
    def retry_count(self) -> int:
        return get_config("data.binance.retry_count", 3)
    
    @property
    def retry_delay(self) -> float:
        return get_config("data.binance.retry_delay", 1.0)


config = DataServiceConfig()
