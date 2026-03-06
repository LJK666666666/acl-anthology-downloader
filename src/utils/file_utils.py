"""
文件操作工具模块
"""
import os
import re
import shutil
from pathlib import Path
from typing import Optional


def ensure_dir(dir_path: str) -> bool:
    """
    确保目录存在，不存在则创建
    Args:
        dir_path: 目录路径
    Returns:
        是否成功
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败 {dir_path}: {e}")
        return False


def clean_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名，移除非法字符
    Args:
        filename: 原始文件名
        max_length: 最大长度
    Returns:
        清理后的文件名
    """
    if not filename:
        return "unnamed"

    # 移除非法字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # 移除多余的空格和下划线
    safe_name = re.sub(r'[_\s]+', '_', safe_name.strip())

    # 移除开头和结尾的下划线
    safe_name = safe_name.strip('_')

    # 限制长度
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip('_')

    return safe_name or "unnamed"


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    Args:
        file_path: 文件路径
    Returns:
        文件大小（字节），如果文件不存在返回0
    """
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
    except Exception:
        pass
    return 0


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    Args:
        size_bytes: 字节数
    Returns:
        格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def is_pdf_file(file_path: str) -> bool:
    """
    检查文件是否为PDF
    Args:
        file_path: 文件路径
    Returns:
        是否为PDF文件
    """
    if not os.path.exists(file_path):
        return False

    # 检查文件扩展名
    if not file_path.lower().endswith('.pdf'):
        return False

    # 检查文件头
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except Exception:
        return False


def copy_file(src: str, dst: str) -> bool:
    """
    复制文件
    Args:
        src: 源文件路径
        dst: 目标文件路径
    Returns:
        是否成功
    """
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"复制文件失败 {src} -> {dst}: {e}")
        return False


def move_file(src: str, dst: str) -> bool:
    """
    移动文件
    Args:
        src: 源文件路径
        dst: 目标文件路径
    Returns:
        是否成功
    """
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        return True
    except Exception as e:
        print(f"移动文件失败 {src} -> {dst}: {e}")
        return False


def delete_file(file_path: str) -> bool:
    """
    删除文件
    Args:
        file_path: 文件路径
    Returns:
        是否成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败 {file_path}: {e}")
        return False


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    获取相对路径
    Args:
        file_path: 文件路径
        base_path: 基础路径
    Returns:
        相对路径
    """
    try:
        return os.path.relpath(file_path, base_path)
    except Exception:
        return file_path


def find_files(directory: str, pattern: str = "*", recursive: bool = True) -> list:
    """
    查找文件
    Args:
        directory: 搜索目录
        pattern: 文件名模式
        recursive: 是否递归搜索
    Returns:
        匹配的文件路径列表
    """
    import glob

    if recursive:
        search_pattern = os.path.join(directory, "**", pattern)
        return glob.glob(search_pattern, recursive=True)
    else:
        search_pattern = os.path.join(directory, pattern)
        return glob.glob(search_pattern)


def count_files(directory: str, extension: Optional[str] = None) -> int:
    """
    统计文件数量
    Args:
        directory: 目录路径
        extension: 文件扩展名过滤
    Returns:
        文件数量
    """
    if not os.path.exists(directory):
        return 0

    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if extension is None or file.lower().endswith(extension.lower()):
                count += 1

    return count


def get_directory_size(directory: str) -> int:
    """
    获取目录大小
    Args:
        directory: 目录路径
    Returns:
        目录大小（字节）
    """
    if not os.path.exists(directory):
        return 0

    total_size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                total_size += os.path.getsize(file_path)
            except Exception:
                continue

    return total_size


def create_backup_file(file_path: str, backup_suffix: str = ".bak") -> str:
    """
    创建备份文件
    Args:
        file_path: 原文件路径
        backup_suffix: 备份文件后缀
    Returns:
        备份文件路径
    """
    backup_path = file_path + backup_suffix
    counter = 1

    # 如果备份文件已存在，添加数字后缀
    while os.path.exists(backup_path):
        backup_path = f"{file_path}{backup_suffix}.{counter}"
        counter += 1

    copy_file(file_path, backup_path)
    return backup_path


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名（去除特殊字符）
    Args:
        filename: 原始文件名
    Returns:
        安全的文件名
    """
    # 移除或替换特殊字符
    safe_name = re.sub(r'[^\w\s-]', '_', filename)

    # 替换空格为下划线
    safe_name = re.sub(r'[-\s]+', '_', safe_name)

    # 移除开头和结尾的特殊字符
    safe_name = safe_name.strip('_-')

    return safe_name or "file"


def validate_path(path: str) -> bool:
    """
    验证路径是否有效
    Args:
        path: 路径
    Returns:
        是否有效
    """
    try:
        Path(path)
        return True
    except Exception:
        return False