from configparser import ConfigParser
from pathlib import Path


class Settings:

    def __init__(self):
        self.config = ConfigParser()
        self.load_config()
        self.init_settings()

    def load_config(self):
        """加载配置文件"""
        # 获取配置文件路径
        config_path = Path(__file__).parents[1] / "config.ini"
        if not config_path.exists():
            raise FileNotFoundError("配置文件config.ini不存在，请检查文件！")

        self.config.read(config_path, encoding="utf-8")

    def init_settings(self):
        """初始化配置"""
        # v2ray
        self.config_path = self.config.get("v2ray", "config_path")

        # dynamodb
        self.region = self.config.get("dynamodb", "region")
        self.table = self.config.get("dynamodb", "table")

        # logging
        self.log_path = self.config.get("logging", "log_path")
        self.log_level = self.config.get("logging", "log_level")


settings = Settings()

