import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
from database import EncryptedDatabase
import logging

logger = logging.getLogger(__name__)

class PrivacyService:
    def __init__(self):
        self.db = EncryptedDatabase()

    def search(self, keyword):
        """执行搜索（返回匹配的文件元数据）"""
        return self.db.search(keyword)

    def retrieve_block(self, block_id):
        """获取整个块的加密数据（用于PIR计算）"""
        return self.db.get_block_data(block_id)

    def get_block_key(self, block_id):
        """获取加密的块密钥（用于客户端解密）"""
        return self.db.get_block_key(block_id)

    def get_file_size(self, block_id, filename):
        """获取文件大小（用于客户端预估）"""
        block_path = os.path.join(self.db.blocks_dir, block_id)
        file_path = os.path.join(block_path, filename)
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0