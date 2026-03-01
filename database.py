# database.py
import os
import json
import logging
from config import DATA_DIR, BLOCK_SIZE, PIR_BLOCK_SIZE
from key_management import load_public_key

logger = logging.getLogger(__name__)


class EncryptedDatabase:
    def __init__(self):
        self.manifest_path = os.path.join(DATA_DIR, 'manifest.json')
        self.blocks_dir = os.path.join(DATA_DIR, 'blocks')
        self.manifest = self._load_manifest()
        self.se_index = self._load_se_index()  # 从客户端上传的加密索引
        self.public_key = load_public_key()
        self.block_sizes = self._calculate_block_sizes()

        # 验证数据完整性
        self._validate_data()

    def _load_manifest(self):
        """加载manifest.json"""
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            return manifest
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            raise

    def _load_se_index(self):
        """加载客户端上传的加密SE索引（服务器不构建索引）"""
        se_index_path = os.path.join(DATA_DIR, 'se_index.enc')
        if not os.path.exists(se_index_path):
            logger.warning("No SE index found, will be uploaded by client")
            return {}
        try:
            with open(se_index_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load SE index: {e}")
            return {}

    def _calculate_block_sizes(self):
        """计算每个块的文件数量"""
        block_sizes = {}
        for block in self.manifest['blocks']:
            block_sizes[block['block_id']] = len(block['files'])
        return block_sizes

    def _validate_data(self):
        """验证数据完整性"""
        for block in self.manifest['blocks']:
            block_id = block['block_id']
            block_path = os.path.join(self.blocks_dir, block_id)
            if not os.path.exists(block_path):
                raise FileNotFoundError(f"Block directory not found: {block_path}")

            # 验证文件数量
            expected_count = len(block['files'])
            actual_count = len(os.listdir(block_path))
            if actual_count != expected_count:
                logger.warning(f"Block {block_id} has {actual_count} files, expected {expected_count}")

    def get_block_for_file(self, filename):
        """获取文件所在的块ID（用于搜索结果）"""
        for block in self.manifest['blocks']:
            for file_info in block['files']:
                if file_info['original_name'] == filename:
                    return block['block_id']
        return None

    # 重要：不再构建SE索引，只提供搜索接口
    def search(self, keyword):
        """执行搜索（服务器端只返回匹配的文件元数据）"""
        # 服务器不处理关键词，只返回匹配结果
        # 实际搜索在客户端完成，这里只是返回索引中的匹配
        if keyword not in self.se_index:
            return []

        results = []
        for filename in self.se_index[keyword]:
            block_id = self.get_block_for_file(filename)
            if block_id:
                results.append({
                    'original_name': filename,
                    'block_id': block_id
                })
        return results

    def get_block_data(self, block_id):
        """获取指定块的加密数据（用于PIR）"""
        block_path = os.path.join(self.blocks_dir, block_id)
        block_files = []
        for filename in os.listdir(block_path):
            if filename.endswith('.enc'):
                file_path = os.path.join(block_path, filename)
                block_files.append({
                    'filename': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path)
                })
        return block_files

    def get_block_size(self, block_id):
        """获取块的大小（文件数量）"""
        return self.block_sizes.get(block_id, 0)

    def get_block_key(self, block_id):
        """获取加密的块密钥（Base64）"""
        for block in self.manifest['blocks']:
            if block['block_id'] == block_id:
                return block['encrypted_key_b64']
        return None