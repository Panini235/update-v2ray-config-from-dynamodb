import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.update import update
from utils.logger import setup_logger
from readConfig.read import reader
from database.dynamodb import db_client
from config.settings import settings

logger = setup_logger(__name__)

def main():
    try:
        logger.info("=== 开始更新UUID ===")
        old_list = update.query_old_list()
        to_add_set, to_remove_set = update.compare(old_list=old_list)
        config=reader.read_json()
        if to_remove_set:
            logger.info(f"将删除一下UUID: {to_remove_set}")
            config = update.remove_invalid_clients(config=config, to_remove_set=to_remove_set)
        else:
            logger.info("没有要删除的 UUID")
        if to_add_set:
            logger.info(f"将添加一下新的 UUID: {to_add_set}")
            config = update.add_clients_config(id_list=to_add_set
                                               ,dynamodb_user=db_client.scan_dynamodb()
                                               ,config=config
                                               )
        else:
            logger.info("没有需要添加的UUID")

        reader.save_config(config=config)
        logger.info("配置同步完成")
        os.system("systemctl restart v2ray")
        logger.info("v2ray 已重启")
        logger.info(f"=== 日志位置: {settings.log_path} ===")
        return True
    except Exception as e:
        print(f"执行程序时发生错误，f{str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)