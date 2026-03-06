"""
数据验证工具模块
"""
import re
from typing import Optional, List, Any
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    验证URL是否有效
    Args:
        url: URL字符串
    Returns:
        是否有效
    """
    if not url or not isinstance(url, str):
        return False

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_pdf_url(url: str) -> bool:
    """
    验证是否为有效的PDF URL
    Args:
        url: URL字符串
    Returns:
        是否有效
    """
    if not is_valid_url(url):
        return False

    return url.lower().endswith('.pdf')


def is_valid_year(year: Any) -> bool:
    """
    验证年份是否有效
    Args:
        year: 年份
    Returns:
        是否有效
    """
    try:
        year_int = int(year)
        return 1990 <= year_int <= 2030  # 合理的年份范围
    except (ValueError, TypeError):
        return False


def is_valid_venue(venue: str, supported_venues: Optional[List[str]] = None) -> bool:
    """
    验证会议名称是否有效
    Args:
        venue: 会议名称
        supported_venues: 支持的会议列表
    Returns:
        是否有效
    """
    if not venue or not isinstance(venue, str):
        return False

    venue = venue.strip().upper()

    # 基本格式验证
    if not re.match(r'^[A-Z]+$', venue):
        return False

    # 如果提供了支持的会议列表，检查是否在其中
    if supported_venues:
        return venue in [v.upper() for v in supported_venues]

    return True


def is_valid_title(title: str) -> bool:
    """
    验证论文标题是否有效
    Args:
        title: 论文标题
    Returns:
        是否有效
    """
    if not title or not isinstance(title, str):
        return False

    title = title.strip()

    # 检查长度
    if len(title) < 5 or len(title) > 500:
        return False

    # 检查是否包含有意义的内容
    if len(re.findall(r'[a-zA-Z]', title)) < 3:
        return False

    return True


def validate_paper_data(paper_data: dict) -> tuple[bool, List[str]]:
    """
    验证论文数据是否完整和有效
    Args:
        paper_data: 论文数据字典
    Returns:
        (是否有效, 错误消息列表)
    """
    errors = []

    # 检查必需字段
    required_fields = ['title', 'pdf_url']
    for field in required_fields:
        if field not in paper_data or not paper_data[field]:
            errors.append(f"缺少必需字段: {field}")

    # 验证标题
    if 'title' in paper_data:
        if not is_valid_title(paper_data['title']):
            errors.append("论文标题无效")

    # 验证PDF URL
    if 'pdf_url' in paper_data:
        if not is_valid_pdf_url(paper_data['pdf_url']):
            errors.append("PDF URL无效")

    # 验证年份
    if 'year' in paper_data:
        if not is_valid_year(paper_data['year']):
            errors.append("年份无效")

    # 验证会议名称
    if 'venue' in paper_data:
        if not is_valid_venue(paper_data['venue']):
            errors.append("会议名称无效")

    return len(errors) == 0, errors


def validate_config(config_data: dict) -> tuple[bool, List[str]]:
    """
    验证配置数据
    Args:
        config_data: 配置数据字典
    Returns:
        (是否有效, 错误消息列表)
    """
    errors = []

    # 验证scraper配置
    if 'scraper' in config_data:
        scraper_config = config_data['scraper']

        if 'delay' in scraper_config:
            try:
                delay = float(scraper_config['delay'])
                if delay < 0:
                    errors.append("scraper.delay 不能为负数")
            except (ValueError, TypeError):
                errors.append("scraper.delay 必须是数字")

        if 'timeout' in scraper_config:
            try:
                timeout = int(scraper_config['timeout'])
                if timeout <= 0:
                    errors.append("scraper.timeout 必须大于0")
            except (ValueError, TypeError):
                errors.append("scraper.timeout 必须是正整数")

        if 'max_retries' in scraper_config:
            try:
                max_retries = int(scraper_config['max_retries'])
                if max_retries < 0:
                    errors.append("scraper.max_retries 不能为负数")
            except (ValueError, TypeError):
                errors.append("scraper.max_retries 必须是非负整数")

    # 验证downloader配置
    if 'downloader' in config_data:
        downloader_config = config_data['downloader']

        if 'max_download' in downloader_config:
            try:
                max_download = downloader_config['max_download']
                if max_download is not None:
                    max_download = int(max_download)
                    if max_download <= 0:
                        errors.append("downloader.max_download 必须大于0或为None")
            except (ValueError, TypeError):
                errors.append("downloader.max_download 必须是正整数或None")

        if 'max_filename_length' in downloader_config:
            try:
                max_length = int(downloader_config['max_filename_length'])
                if max_length <= 0:
                    errors.append("downloader.max_filename_length 必须大于0")
            except (ValueError, TypeError):
                errors.append("downloader.max_filename_length 必须是正整数")

    return len(errors) == 0, errors


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    Args:
        filename: 原始文件名
    Returns:
        安全的文件名
    """
    if not filename:
        return "unnamed"

    # 移除或替换不安全字符
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    safe_name = re.sub(unsafe_chars, '_', filename)

    # 移除控制字符
    safe_name = ''.join(char for char in safe_name if ord(char) >= 32)

    # 限制长度
    if len(safe_name) > 255:
        safe_name = safe_name[:255]

    return safe_name.strip()


def validate_year_range(start_year: Any, end_year: Any) -> tuple[bool, str]:
    """
    验证年份范围
    Args:
        start_year: 开始年份
        end_year: 结束年份
    Returns:
        (是否有效, 错误消息)
    """
    try:
        start = int(start_year)
        end = int(end_year)

        if not is_valid_year(start):
            return False, f"开始年份无效: {start_year}"

        if not is_valid_year(end):
            return False, f"结束年份无效: {end_year}"

        if start > end:
            return False, f"开始年份 ({start}) 不能大于结束年份 ({end})"

        return True, ""

    except (ValueError, TypeError):
        return False, "年份必须是数字"


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """
    验证文件路径
    Args:
        file_path: 文件路径
    Returns:
        (是否有效, 错误消息)
    """
    if not file_path or not isinstance(file_path, str):
        return False, "文件路径不能为空"

    # 检查路径长度
    if len(file_path) > 260:  # Windows路径长度限制
        return False, "文件路径过长"

    # 检查非法字符
    illegal_chars = r'[<>:"|?*]'
    if re.search(illegal_chars, file_path):
        return False, "文件路径包含非法字符"

    return True, ""


def validate_email(email: str) -> bool:
    """
    验证邮箱地址格式
    Args:
        email: 邮箱地址
    Returns:
        是否有效
    """
    if not email or not isinstance(email, str):
        return False

    # 简单的邮箱验证正则表达式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def is_positive_integer(value: Any) -> bool:
    """
    检查是否为正整数
    Args:
        value: 待检查的值
    Returns:
        是否为正整数
    """
    try:
        int_value = int(value)
        return int_value > 0
    except (ValueError, TypeError):
        return False


def is_non_negative_integer(value: Any) -> bool:
    """
    检查是否为非负整数
    Args:
        value: 待检查的值
    Returns:
        是否为非负整数
    """
    try:
        int_value = int(value)
        return int_value >= 0
    except (ValueError, TypeError):
        return False


def validate_list_length(lst: List[Any], min_length: int = 0, max_length: int = None) -> bool:
    """
    验证列表长度
    Args:
        lst: 列表
        min_length: 最小长度
        max_length: 最大长度
    Returns:
        是否有效
    """
    if not isinstance(lst, list):
        return False

    length = len(lst)

    if length < min_length:
        return False

    if max_length is not None and length > max_length:
        return False

    return True