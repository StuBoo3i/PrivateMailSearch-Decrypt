import os
import json
import glob
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import base64
import shutil

# ================= 配置区域 =================
# 源数据目录 (请根据实际情况修改)
SOURCE_DIR = r"D:\Data\Pycharm\System\System\trec06c\ham"
# 输出目录 (加密后的数据将存放在这里)
OUTPUT_DIR = r"/data"
# 块大小 (每个块包含的文件数)
BLOCK_SIZE = 1000
# RSA 密钥长度
RSA_KEY_SIZE = 2048


# ===========================================

def generate_rsa_keys():
    """生成 RSA 公私钥对"""
    print("[*] 正在生成 RSA 密钥对...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=RSA_KEY_SIZE,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    # 序列化密钥 (PEM 格式)
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # 生产环境建议加密码保护私钥
    )
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 保存密钥到文件 (实际场景中，私钥应由用户离线保存，不要放在服务器)
    with open(os.path.join(OUTPUT_DIR, "private_key.pem"), "wb") as f:
        f.write(pem_private)
    with open(os.path.join(OUTPUT_DIR, "public_key.pem"), "wb") as f:
        f.write(pem_public)

    print("[+] 密钥对已生成: public_key.pem (公开), private_key.pem (用户保密)")
    return public_key, private_key


def encrypt_file_content(file_path, aes_key):
    """使用 AES-GCM 加密单个文件内容"""
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)  # GCM 模式推荐的 12 字节 nonce

    with open(file_path, "rb") as f:
        plaintext = f.read()

    # 加密：密文 = nonce + ciphertext + tag (cryptography 库自动处理 tag)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # 将 nonce 和密文组合存储 (解密时需要 nonce)
    return nonce + ciphertext


def process_dataset():
    # 1. 准备环境
    if os.path.exists(OUTPUT_DIR):
        # 警告：这将清空输出目录
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, "blocks"))

    # 2. 生成密钥
    public_key, private_key = generate_rsa_keys()

    # 3. 获取所有文件列表并排序 (确保顺序一致)
    # 假设文件名为 000000_001.txt 这种格式，直接排序即可
    all_files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.txt")))
    total_files = len(all_files)
    print(f"[*] 发现 {total_files} 个文件，开始分块处理...")

    manifest = {
        "block_size": BLOCK_SIZE,
        "total_files": total_files,
        "blocks": []
    }

    # 4. 分块处理
    block_id = 0
    for i in range(0, total_files, BLOCK_SIZE):
        block_files = all_files[i: i + BLOCK_SIZE]
        current_block_id = f"block_{block_id:03d}"
        block_dir = os.path.join(OUTPUT_DIR, "blocks", current_block_id)
        os.makedirs(block_dir)

        print(f"[*] 处理 {current_block_id} (文件 {i + 1} - {min(i + BLOCK_SIZE, total_files)})...")

        # A. 为该块生成随机 AES 密钥 (32 字节 = 256 位)
        block_key = AESGCM.generate_key(bit_length=256)

        # B. 用 RSA 公钥加密这个 AES 密钥 (密钥封装)
        encrypted_block_key = public_key.encrypt(
            block_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # C. 加密块内的所有文件
        file_map = []  # 记录该块内文件名与加密后文件名的映射
        for idx, src_file in enumerate(block_files):
            filename = os.path.basename(src_file)
            # 加密文件内容
            encrypted_content = encrypt_file_content(src_file, block_key)

            # 保存加密文件 (命名规则：原文件名.enc)
            dest_filename = f"{filename}.enc"
            dest_path = os.path.join(block_dir, dest_filename)

            with open(dest_path, "wb") as f:
                f.write(encrypted_content)

            file_map.append({
                "original_name": filename,
                "encrypted_name": dest_filename,
                "size_original": os.path.getsize(src_file),
                "size_encrypted": os.path.getsize(dest_path)
            })

        # D. 记录块信息到清单
        manifest["blocks"].append({
            "block_id": current_block_id,
            "file_count": len(block_files),
            "encrypted_key_b64": base64.b64encode(encrypted_block_key).decode('utf-8'),  # 存 Base64 字符串
            "files": file_map
        })

        block_id += 1

    # 5. 保存清单文件 (Manifest)
    # 注意：manifest 中包含的是被公钥加密的密钥，没有私钥无法解密
    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] 处理完成！")
    print(f"    - 加密数据目录：{os.path.join(OUTPUT_DIR, 'blocks')}")
    print(f"    - 索引清单：{manifest_path}")
    print(f"    - 公钥：{os.path.join(OUTPUT_DIR, 'public_key.pem')}")
    print(f"    - 私钥：{os.path.join(OUTPUT_DIR, 'private_key.pem')} (请妥善保管并删除服务器上的副本!)")


if __name__ == "__main__":
    try:
        process_dataset()
    except Exception as e:
        print(f"[!] 发生错误：{e}")
        import traceback

        traceback.print_exc()