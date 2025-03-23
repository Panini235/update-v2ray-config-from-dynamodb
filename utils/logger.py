import logging
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

def setup_logger(name: str = __name__) -> logging.Logger:

    # 从配置文件中读取日志级别和路径
    log_level = settings.log_level
    log_path = settings.log_path

    # 日志文件名
    log_file = f"{log_path}/v2ray_config_sync_{datetime.now().strftime('%m%d')}.log"

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
