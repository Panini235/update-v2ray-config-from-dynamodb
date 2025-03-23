import boto3
import json
import re
import logging
import os
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/var/log/v2ray/config_sync_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_params_from_os_env():
    """
    从环境变量中读取参数，在Linux中可以使用以下命令实现
    export CONFIG_PATH="/usr/local/etc/v2ray/config.json"
    export REGION="us-east-1"
    export ACCESS_TOKEN="你的aws_access_key"
    export SECRET_ACCESS_KEY="你的secret_acess_key"
    export TABLE_NAME="<Dynamodb表名>"
    """
    try:
        config_path = os.environ.get("CONFIG_PATH")
        region = os.environ.get("REGION")
        # access_key = os.environ.get("ACCESS_TOKEN")
        # secret_access_key = os.environ.get("SECRET_ACCESS_KEY")
        table_name = os.environ.get("TABLE_NAME")
        env_params = {
            "config_path": config_path,
            "region": region,
            # "access_key": access_key,
            # "secret_access_key": secret_access_key,
            "table_name": table_name
        }
        return env_params
    except Exception as e:
        return f"读取环境变量时失败,错误信息: {e}"

def read_json(config_path):
    """读取json文件"""
    config = ""
    try:
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info("成功读取配置文件")
            f.close()
            return config
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"读取配置文件时发生错误: {str(e)}")
        raise

def query_json_id(config):
    """查询json文件中的id"""
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

        logger.info(f"从配置文件中找到 {len(id_list)} 个有效的 UUID")
        return id_list
    except Exception as e:
        logger.error(f"查询配置文件中的 UUID 时发生错误: {str(e)}")
        raise

def query_dynamodb_id(region_name,table_name):
    dynamodb = boto3.resource(
    'dynamodb',
    region_name=region_name
    # aws_access_key_id=access_key,
    # aws_secret_access_key=secret_key
    )
    table = dynamodb.Table(table_name)
    id_list = []
    dynamodb_user = {}
    data = table.scan()['Items']
    for item in data:
        id_list.append(item['uuid'])
        dynamodb_user[item['uuid']] = item['username']
    return id_list, dynamodb_user

# 对比json和dynamodb中的id
def compare_id(json_id_list, dynamodb_id_list):
    to_add_list = []    # 需要添加的 UUID
    to_remove_list = [] # 需要删除的 UUID

    # 找出需要添加的 UUID（在 DynamoDB 中有，但 JSON 中没有的）
    for dynamodb_id in dynamodb_id_list:
        if dynamodb_id not in json_id_list:
            to_add_list.append(dynamodb_id)

    # 找出需要删除的 UUID（在 JSON 中有，但 DynamoDB 中没有的）
    for json_id in json_id_list:
        if json_id not in dynamodb_id_list:
            to_remove_list.append(json_id)

    return to_add_list, to_remove_list

def remove_invalid_clients(config, to_remove_list):
    """删除无效的客户端配置"""
    if not to_remove_list:
        return config

    pattern = r"^node"
    for item in config['inbounds']:
        if re.match(pattern, item['tag']):
            # 过滤掉需要删除的客户端
            item['settings']['clients'] = [
                client for client in item['settings']['clients']
                if client['id'] not in to_remove_list
            ]
    return config

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

def save_config(config, config_path):
    """保存配置到文件"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("配置文件保存成功")
    except Exception as e:
        logger.error(f"保存配置文件时发生错误: {str(e)}")
        raise

def reload_v2ray():
    """重启v2ray"""
    os.system("systemctl restart v2ray")
    # os.system("systemctl status v2ray")

def main():
    try:
        # 读取配置文件
        env_params = read_params_from_os_env()
        config = read_json(config_path=env_params["config_path"])
        json_id_list = query_json_id(config)
        # 查询 DynamoDB
        dynamodb_id_list, dynamodb_user = query_dynamodb_id(region_name=env_params["region"],table_name=env_params["table_name"])
        # 获取需要添加和删除的 UUID 列表
        to_add_list, to_remove_list = compare_id(json_id_list, dynamodb_id_list)
        # 先删除无效的客户端
        if to_remove_list:
            logger.info(f"将删除以下无效的 UUID: {to_remove_list}")
            config = remove_invalid_clients(config, to_remove_list)
        else:
            logger.info("没有需要删除的 UUID")
        # 再添加新的客户端
        if to_add_list:
            logger.info(f"将添加以下新的 UUID: {to_add_list}")
            config = add_clients_config(to_add_list, dynamodb_user, config)
        else:
            logger.info("没有需要添加的 UUID")
        # 保存更新后的配置
        save_config(config, config_path=env_params["config_path"])
        logger.info("配置同步完成")
        reload_v2ray()
        logger.info("v2ray 已重启")
        logger.info("=== 日志位置：/var/log/v2ray/ ===")
        return True

    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
