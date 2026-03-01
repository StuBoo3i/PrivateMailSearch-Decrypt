import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def load_public_key():
    """加载公钥（服务器仅使用公钥）"""
    public_key_path = os.path.join(os.getenv('DATA_DIR', 'data'), 'public_key.pem')
    try:
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        return public_key
    except Exception as e:
        raise ValueError(f"Failed to load public key: {e}")

def get_public_key_pem():
    """获取公钥的PEM格式字符串（用于前端显示）"""
    public_key = load_public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')