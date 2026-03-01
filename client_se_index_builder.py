# client_se_index_builder.py
import os
import json
import hashlib
import requests
import jieba
import time
import sys
import logging
import re
from collections import Counter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def download_jieba_data():
    """检查并下载jieba"""
    try:
        # 简单测试jieba是否可用
        jieba.lcut("测试")
        logging.info("Jieba 模块加载成功")
        return True
    except Exception as e:
        logging.info("正在安装/初始化 Jieba...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'jieba', '-q'])
            logging.info("Jieba 安装/初始化完成")
            return True
        except Exception as ex:
            logging.error(f"Jieba 初始化失败: {ex}")
            return False


def extract_chinese_keywords(content):
    """
    使用中文NLP提取关键词
    """
    if not content:
        return []

    # 1. 只保留中文字符 (Unicode范围 \u4e00-\u9fa5)
    # 这一步会自动过滤掉所有英文、数字、标点和乱码
    chinese_text = re.sub(r'[^\u4e00-\u9fa5]', ' ', content)
    chinese_text = re.sub(r'\s+', ' ', chinese_text).strip()

    if not chinese_text:
        return []

    # 2. 分词
    words = jieba.lcut(chinese_text)

    # 3. 内置停用词表 (高频无意义词)
    stop_words = {
        '的', '了', '在', '是', '和', '我', '你', '他', '她', '它', '这', '那',
        '个', '一', '不', '有', '就', '都', '上', '下', '中', '人', '为', '来',
        '去', '好', '着', '会', '也', '可', '以', '但', '而', '或', '又', '对',
        '从', '于', '吧', '呢', '啊', '哦', '呀', '啦', '呵', '嗯', '哎', '哈',
        '呜', '吗', '什', '么', '怎', '样', '谁', '哪', '些', '此', '其', '及',
        '等', '者', '被', '把', '让', '叫', '向', '往', '至', '到', '过', '还',
        '更', '最', '很', '太', '极', '非常', '已经', '但是', '所以', '因为',
        '如果', '虽然', '即使', '关于', '对于', '根据', '按照', '通过', '进行'
    }

    # 4. 过滤：长度>1 且 不在停用词表中
    filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]

    # 5. 词频统计，取前50个高频词作为该文件的关键词
    if not filtered_words:
        return []

    word_freq = Counter(filtered_words)
    top_words = [word for word, _ in word_freq.most_common(50)]

    return top_words


def read_file_robust(file_path):
    """
    鲁棒的文件读取函数：尝试多种编码，遇到错误直接忽略坏字节
    """
    encodings = ['gbk', 'gb18030', 'utf-8', 'latin-1']

    for encoding in encodings:
        try:
            # errors='ignore' 是关键：遇到无法解码的字节直接跳过，不报错
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            # 如果读到了内容（不仅仅是空白），则返回
            if content.strip():
                return content
        except Exception:
            continue

    # 如果所有编码都失败（极少见），尝试用二进制读取并强制转换
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
        # 尝试用 utf-8 忽略错误解码
        return raw.decode('utf-8', errors='ignore')
    except Exception as e:
        logging.warning(f"无法读取文件 {os.path.basename(file_path)}: {e}")
        return ""


def build_se_index(plaintext_dir, server_url='http://localhost:5000'):
    """构建SE索引主流程"""
    se_index = {}
    processed_count = 0
    error_count = 0

    logging.info(f"开始扫描目录: {plaintext_dir}")
    start_time = time.time()

    # 确保jieba可用
    if not download_jieba_data():
        logging.error("Jieba 不可用，终止程序")
        return False

    files = [f for f in os.listdir(plaintext_dir) if f.endswith('.txt')]
    total_files = len(files)
    logging.info(f"发现 {total_files} 个文件，开始处理...")

    for i, filename in enumerate(files):
        file_path = os.path.join(plaintext_dir, filename)

        # 进度显示 (每1000个文件打印一次)
        if (i + 1) % 1000 == 0:
            logging.info(f"进度: {i + 1}/{total_files} ...")

        try:
            content = read_file_robust(file_path)

            if not content:
                continue

            # 提取关键词
            keywords = extract_chinese_keywords(content)
            # print(keywords)

            # 构建索引
            for word in keywords:
                if word not in se_index:
                    se_index[word] = []
                # 避免同一个文件在同一关键词下重复添加
                if filename not in se_index[word]:
                    se_index[word].append(filename)

            processed_count += 1

        except Exception as e:
            error_count += 1
            # 记录错误但不中断程序
            logging.warning(f"文件 {filename} 处理异常: {e}")

    # 创建加密索引 (SHA-256 Hash)
    encrypted_index = {}
    for word, files_list in se_index.items():
        print(word)
        trapdoor = hashlib.sha256(word.encode('utf-8')).hexdigest()
        encrypted_index[trapdoor] = files_list

    elapsed = time.time() - start_time
    logging.info(f"处理完成！成功: {processed_count}, 跳过/错误: {error_count}, 唯一关键词: {len(se_index)}")
    logging.info(f"总耗时: {elapsed:.2f}秒")

    # 上传到服务器
    logging.info(f"正在上传索引到 {server_url} ...")
    try:
        response = requests.post(
            f"{server_url}/api/upload_se_index",
            json={'index': encrypted_index},
            timeout=60  # 增加超时时间
        )

        if response.status_code == 200:
            logging.info("✅ SE索引上传成功！")
            return True
        else:
            logging.error(f"❌ 上传失败: HTTP {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logging.error("❌ 连接失败：无法连接到服务器。请确保 Flask 服务器已启动 (python app.py)")
        return False
    except Exception as e:
        logging.error(f"❌ 上传过程出错: {e}")
        return False


def main():
    # 配置路径
    PLAINTEXT_DIR = r"D:\Data\Pycharm\System\System\trec06c\ham"
    SERVER_URL = "http://localhost:5000"

    print("=" * 60)
    print("邮件隐私系统 - 中文SE索引构建工具 (鲁棒版)")
    print("=" * 60)
    print(f"数据源: {PLAINTEXT_DIR}")
    print(f"服务器: {SERVER_URL}")
    print("=" * 60)

    if not os.path.exists(PLAINTEXT_DIR):
        print(f"❌ 错误：目录不存在 -> {PLAINTEXT_DIR}")
        sys.exit(1)

    success = build_se_index(PLAINTEXT_DIR, SERVER_URL)

    if success:
        print("\n🎉 全部完成！现在可以启动网页进行搜索了。")
    else:
        print("\n⚠️ 过程结束，但存在错误。请检查上方日志。")
        if not success:  # 如果是连接失败
            print("💡 提示：请先在另一个终端运行 'python app.py' 启动服务器。")


if __name__ == "__main__":
    main()