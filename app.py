import logging
import os
from flask import Flask
from config import LOG_LEVEL
from routes import app

# 配置日志
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    # 确保数据目录存在
    if not os.path.exists('data'):
        os.makedirs('data')

    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)