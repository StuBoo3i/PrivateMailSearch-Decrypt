# routes.py
from flask import Flask, request, jsonify, render_template, send_file
from services import PrivacyService
from key_management import get_public_key_pem
import json
import os
import hashlib

app = Flask(__name__)
privacy_service = PrivacyService()

import hashlib
import logging

# ... 其他导入 ...

logger = logging.getLogger(__name__)


@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    if not data or 'keyword' not in data:
        return jsonify({'error': 'Missing keyword'}), 400

    keyword = data['keyword']
    logger.info(f"🔍 [搜索请求] 收到原始关键词: '{keyword}'")

    # 【关键逻辑】必须与 client_se_index_builder.py 中的哈希逻辑完全一致
    # 1. 编码必须是 utf-8
    # 2. 算法必须是 sha256
    try:
        trapdoor = hashlib.sha256(keyword.encode('utf-8')).hexdigest()
        logger.info(f"🔑 [计算陷门] 生成的哈希值: {trapdoor}")
    except Exception as e:
        logger.error(f"哈希计算错误: {e}")
        return jsonify({'error': 'Hash error'}), 500

    # 检查索引
    se_index = privacy_service.db.se_index
    logger.info(f"📚 [索引状态] 当前索引中关键词总数: {len(se_index)}")

    # 调试：打印索引中的前 5 个哈希值，方便对比
    if len(se_index) > 0:
        sample_keys = list(se_index.keys())[:5]
        logger.info(f"👀 [索引样本] 索引中前5个哈希: {sample_keys}")

    if trapdoor in se_index:
        results = se_index[trapdoor]
        logger.info(f"✅ [匹配成功] 找到 {len(results)} 个文件")

        # 组装返回数据 (需要包含 block_id)
        response_data = []
        for filename in results:
            block_id = privacy_service.db.get_block_for_file(filename)
            response_data.append({
                'original_name': filename,
                'block_id': block_id
            })
        return jsonify(response_data)
    else:
        logger.warning(f"❌ [匹配失败] 哈希值 '{trapdoor}' 不在索引中")
        return jsonify([])


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


# @app.route('/api/search', methods=['POST'])
# def search():
#     """执行搜索（SE） - 服务器端只返回匹配的文件元数据"""
#     keyword = request.json.get('keyword', '')
#     if not keyword:
#         return jsonify({'error': 'Keyword is required'}), 400
#
#     # 服务器端不处理关键词，只返回索引中的匹配
#     results = privacy_service.search(keyword)
#     return jsonify(results)


@app.route('/api/retrieve_block', methods=['POST'])
def retrieve_block():
    """获取整个块的加密数据（用于PIR）"""
    block_id = request.json.get('block_id', '')
    if not block_id:
        return jsonify({'error': 'Block ID is required'}), 400

    block_data = privacy_service.retrieve_block(block_id)
    return jsonify({
        'block_id': block_id,
        'files': block_data
    })


@app.route('/api/block_key', methods=['POST'])
def get_block_key():
    """获取加密的块密钥（客户端解密用）"""
    block_id = request.json.get('block_id', '')
    if not block_id:
        return jsonify({'error': 'Block ID is required'}), 400

    encrypted_key = privacy_service.get_block_key(block_id)
    if not encrypted_key:
        return jsonify({'error': 'Block not found'}), 404

    return jsonify({
        'block_id': block_id,
        'encrypted_key': encrypted_key
    })


@app.route('/api/public_key', methods=['GET'])
def get_public_key():
    """获取公钥（用于客户端加密）"""
    return jsonify({
        'public_key': get_public_key_pem()
    })


@app.route('/api/upload_se_index', methods=['POST'])
def upload_se_index():
    """上传加密的SE索引（由客户端发送）"""
    if 'index' not in request.json:
        return jsonify({'error': 'SE索引数据缺失'}), 400

    index_data = request.json['index']
    se_index_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'se_index.enc')

    try:
        with open(se_index_path, 'w') as f:
            json.dump(index_data, f)
        return jsonify({'status': 'success', 'message': 'SE index uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 用于测试
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'data_dir': os.getenv('DATA_DIR', 'data')
    })

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """返回系统当前状态，包括索引是否加载"""
    try:
        # 尝试从服务中获取索引大小
        # 假设 privacy_service.db.se_index 已经加载
        index_count = len(privacy_service.db.se_index)
        return jsonify({
            'status': 'ok',
            'index_loaded': index_count > 0,
            'keyword_count': index_count,
            'blocks_count': len(privacy_service.db.manifest['blocks'])
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'index_loaded': False,
            'message': str(e)
        }), 500


# 在 routes.py 或 app.py 中添加

@app.route('/api/block_encrypted_key', methods=['POST'])
def get_block_encrypted_key():
    """
    获取指定块的加密密钥 (Encrypted Block Key)
    服务器无法解密此密钥，仅原样返回给客户端
    """
    data = request.json
    block_id = data.get('block_id')

    if not block_id:
        return jsonify({'error': 'Missing block_id'}), 400

    # 从数据库/manifest 中查找
    try:
        encrypted_key_b64 = privacy_service.db.get_block_key(block_id)
        if not encrypted_key_b64:
            return jsonify({'error': 'Block not found'}), 404

        return jsonify({
            'block_id': block_id,
            'encrypted_key_b64': encrypted_key_b64
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 还需要一个接口来获取加密文件的二进制内容
@app.route('/api/download_encrypted_file', methods=['POST'])
def download_encrypted_file():
    """
    下载指定的加密文件 (.enc)
    返回二进制流供前端解密
    """
    try:
        data = request.get_json()  # 推荐使用 get_json() 更安全
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        block_id = data.get('block_id')
        filename = data.get('filename')

        if not block_id or not filename:
            return jsonify({'error': 'Missing parameters: block_id or filename'}), 400

        # 构建文件路径
        # 注意：privacy_service.db.blocks_dir 是你的基础数据目录
        file_path = os.path.join(privacy_service.db.blocks_dir, block_id, filename)

        # 安全检查：防止目录遍历攻击 (可选但推荐)
        # 确保解析后的绝对路径仍然在 blocks_dir 内
        abs_path = os.path.abspath(file_path)
        abs_base = os.path.abspath(privacy_service.db.blocks_dir)
        if not abs_path.startswith(abs_base):
            return jsonify({'error': 'Invalid file path'}), 403

        if not os.path.exists(file_path):
            return jsonify({'error': f'File not found: {filename} in {block_id}'}), 404

        # 发送文件
        # mimetype='application/octet-stream' 告诉浏览器这是二进制流，不要尝试预览
        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=False  # 直接返回流，不触发浏览器下载对话框
        )

    except Exception as e:
        # 记录详细错误日志以便调试
        import logging
        logging.error(f"Download error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500