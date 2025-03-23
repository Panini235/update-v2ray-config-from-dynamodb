import re
import sys, os
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from utils.logger import setup_logger
from database.dynamodb import db_client
from readConfig.read import reader

logger = setup_logger(__name__)

class Update:

    @staticmethod
    def query_old_list():
        config = reader.read_json()
        try:
            id_list = []
            pattern = r"^node"
            inbound_list = config.get('inbounds', [])
            if not inbound_list:
                logger.warning("配置文件中没有找到 inbounds 配置")
                return []
            for item in inbound_list:
                tag = item.get('tag', '')
                if re.match(pattern, tag):
                    clients = item.get("settings", {}).get("clients", [])
                    for client in clients:
                        if 'id' in client and client['id'] not in id_list:
                            id_list.append(client['id'])
            logger.info(f"从配置文件中找到 {len(id_list)} 个有效的 UUID ")
            return id_list
        except Exception as e:
            logger.error(f"查询配置文件中的 UUID 时发生错误: {str(e)}")
            raise


    @staticmethod
    def compare(old_list: list) -> tuple[set[str], set[str]]:
        try:
            dynamodb_user = db_client.scan_dynamodb()
            to_add_set = set(dynamodb_user.keys()) - set(old_list)
            to_remove_set = set(old_list) - set(dynamodb_user.keys())
            return to_add_set, to_remove_set

        except Exception as e:
            print(f"Error in compare function: {e}")
            return set(), set()

    @staticmethod
    def remove_invalid_clients(config: str, to_remove_set: set):
        """删除无效的客户端配置"""
        if not to_remove_set:
            return config

        pattern = r"^node"
        for item in config['inbounds']:
            if re.match(pattern, item['tag']):
                # 过滤掉需要删除的客户端
                item['settings']['clients'] = [
                    client for client in item['settings']['clients']
                    if client['id'] not in to_remove_set
                ]
        return config

    @staticmethod
    def add_clients_config(id_list, dynamodb_user, config):
        """更新配置中的客户端"""
        for id in id_list:
            # 为每个客户端创建新的字典对象
            client = {
                "id": id,
                "email": dynamodb_user[id],
                "alterId": 0,
                "level": 0
            }
            # 遍历所有入站配置
            for item in config['inbounds']:
                if re.match(r"^node", item['tag']):
                    item['settings']['clients'].append(client)
        return config

update = Update



