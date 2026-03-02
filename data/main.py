"""
数据服务主入口

启动 FastAPI 服务
"""

import logging
import uvicorn

from config import config
from api import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info(f"Starting data service on {config.host}:{config.port}")
    uvicorn.run(
        "api:app",
        host=config.host,
        port=config.port,
        reload=False
    )


if __name__ == "__main__":
    main()
