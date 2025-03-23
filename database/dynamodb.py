import boto3
from boto3.dynamodb.conditions import Key, Attr
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)

class Dynamodb:

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',region_name= settings.region)
        self.table = self.dynamodb.Table(settings.table)

    def scan_dynamodb(self) -> dict:
        try:
            dynamodb_user = {}
            items = self.table.scan()["Items"]
            for item in items:
                dynamodb_user[item["uuid"]] = item['username']
            return dynamodb_user
        except Exception as e:
            logger.error(f"扫描dynamodb表{settings.table}时出现错误：{str(e)}")

db_client = Dynamodb()