import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Reader:

    @staticmethod
    def read_json() -> dict:
        """读取json文件"""
        config = ""
        try:
            with open(settings.config_path, 'r') as f:
                logger.info(f"配置文件路径:{settings.config_path}")
                config = f.read()
                config = json.loads(config)
                logger.info("成功读取配置文件")
                f.close()
                return config
        except Exception as e:
            logger.error(f"读取配置文件时发生错误: {str(e)}")
            raise

    @staticmethod
    def save_config(config: dict):
        """保存配置到文件"""
        try:
            with open(settings.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"保存配置文件时发生错误：{str(e)}")
            raise

reader = Reader()