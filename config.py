import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录（相对于项目根目录）
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 块大小（与加密时一致）
BLOCK_SIZE = 1000

# PIR 块大小（用于PIR计算的块大小，与数据块一致）
PIR_BLOCK_SIZE = 1000

# 日志配置
LOG_LEVEL = 'INFO'