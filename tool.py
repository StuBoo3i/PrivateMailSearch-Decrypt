import os
import shutil


def extract_ham_emails(source_index_path, source_data_dir, target_ham_dir):
    """
    从TREC06C数据集中提取所有正常邮件(ham)并保存到新目录

    Args:
        source_index_path: 标注文件index的路径
        source_data_dir: 原始数据目录(data/)
        target_ham_dir: 目标正常邮件目录
    """
    # 创建目标目录
    if not os.path.exists(target_ham_dir):
        os.makedirs(target_ham_dir)
        print(f"创建目录: {target_ham_dir}")

    ham_count = 0
    error_count = 0

    # 读取标注文件
    with open(source_index_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"开始处理 {len(lines)} 条标注记录...")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            # 解析标注行: [标签] [邮件路径]
            parts = line.split(' ', 1)
            if len(parts) != 2:
                continue

            label, relative_path = parts

            # 如果是正常邮件，则复制到目标目录
            if label == 'ham':
                # 构建原始邮件文件路径
                # 相对路径通常是类似 "../data/000/000" 的格式
                original_file_path = os.path.join(os.path.dirname(source_index_path), relative_path)

                # 检查原始文件是否存在
                if os.path.exists(original_file_path):
                    # 获取原始文件名
                    original_filename = os.path.basename(original_file_path)

                    # 生成目标文件路径，添加序号以避免重名
                    target_file_path = os.path.join(target_ham_dir, f"{ham_count:06d}_{original_filename}.txt")

                    # 复制文件
                    shutil.copy2(original_file_path, target_file_path)
                    ham_count += 1

                    if ham_count % 1000 == 0:
                        print(f"已处理 {ham_count} 封正常邮件...")
                else:
                    print(f"警告: 文件不存在 {original_file_path}")
                    error_count += 1

        except Exception as e:
            print(f"处理行时出错: {line}, 错误: {str(e)}")
            error_count += 1

    print(f"\n处理完成!")
    print(f"成功提取正常邮件数量: {ham_count}")
    print(f"遇到错误数量: {error_count}")


def main():
    # 设置路径
    base_path = r"C:\Users\Administrator\Downloads\trec06c\trec06c"
    source_index_path = os.path.join(base_path, "full", "index")
    source_data_dir = os.path.join(base_path, "data")
    target_ham_dir = os.path.join(base_path, "ham")

    print("TREC06C 邮件数据集处理工具")
    print("=" * 50)
    print(f"源标注文件: {source_index_path}")
    print(f"源数据目录: {source_data_dir}")
    print(f"目标正常邮件目录: {target_ham_dir}")
    print("=" * 50)

    # 检查源文件是否存在
    if not os.path.exists(source_index_path):
        print(f"错误: 标注文件不存在 {source_index_path}")
        return

    if not os.path.exists(source_data_dir):
        print(f"错误: 数据目录不存在 {source_data_dir}")
        return

    # 开始处理
    extract_ham_emails(source_index_path, source_data_dir, target_ham_dir)


if __name__ == "__main__":
    main()