"""
文本处理工具模块
"""
import re
import unicodedata
from typing import Optional, List


def normalize_text(text: str) -> str:
    """
    规范化文本，移除多余空白和特殊字符
    Args:
        text: 原始文本
    Returns:
        规范化后的文本
    """
    if not text:
        return ""

    # Unicode规范化
    text = unicodedata.normalize('NFKC', text)

    # 移除控制字符
    text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))

    # 规范化空白字符
    text = re.sub(r'\s+', ' ', text.strip())

    return text


def clean_title(title: str) -> str:
    """
    清理论文标题
    Args:
        title: 原始标题
    Returns:
        清理后的标题
    """
    if not title:
        return ""

    # 移除多余的空白
    title = normalize_text(title)

    # 移除常见的无用后缀
    patterns_to_remove = [
        r'\.\.\.$',  # 结尾的...
        r'\s*-\s*ACL\s+\d{4}$',  # - ACL 2024
        r'\s*\(\s*ACL\s+\d{4}\s*\)$',  # (ACL 2024)
        r'\s*\.\s*ACL\s+\d{4}$',  # . ACL 2024
    ]

    for pattern in patterns_to_remove:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    return title.strip()


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
    """
    从文本中提取关键词
    Args:
        text: 输入文本
        min_length: 关键词最小长度
        max_keywords: 最大关键词数量
    Returns:
        关键词列表
    """
    if not text:
        return []

    # 简单的关键词提取（移除停用词和短词）
    words = re.findall(r'\b[a-zA-Z]{%d,}\b' % min_length, text.lower())

    # 简单的停用词列表
    stop_words = {
        'the', 'and', 'for', 'are', 'with', 'this', 'that', 'from', 'they',
        'have', 'been', 'has', 'had', 'was', 'were', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'could', 'shall', 'should', 'must',
        'our', 'your', 'their', 'its', 'his', 'her', 'who', 'whom', 'which',
        'what', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same',
        'than', 'too', 'very', 'just', 'now', 'also', 'here', 'there', 'well'
    }

    keywords = [word for word in words if word not in stop_words]

    # 统计词频并返回最常见的
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后的后缀
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def remove_html_tags(text: str) -> str:
    """
    移除HTML标签
    Args:
        text: 包含HTML标签的文本
    Returns:
        移除标签后的纯文本
    """
    if not text:
        return ""

    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 规范化空白字符
    text = normalize_text(text)

    return text


def extract_urls(text: str) -> List[str]:
    """
    从文本中提取URL
    Args:
        text: 输入文本
    Returns:
        URL列表
    """
    if not text:
        return []

    # URL正则表达式
    url_pattern = r'https?://[^\s<>"\'{}|\\^`[\]]+'
    urls = re.findall(url_pattern, text)

    return list(set(urls))  # 去重


def extract_emails(text: str) -> List[str]:
    """
    从文本中提取邮箱地址
    Args:
        text: 输入文本
    Returns:
        邮箱列表
    """
    if not text:
        return []

    # 邮箱正则表达式
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)

    return list(set(emails))  # 去重


def split_into_sentences(text: str) -> List[str]:
    """
    将文本分割为句子
    Args:
        text: 输入文本
    Returns:
        句子列表
    """
    if not text:
        return []

    # 句子分割正则表达式
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(sentence_pattern, text)

    # 清理每个句子
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    return sentences


def count_words(text: str) -> int:
    """
    统计文本中的单词数量
    Args:
        text: 输入文本
    Returns:
        单词数量
    """
    if not text:
        return 0

    # 使用正则表达式匹配单词
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def detect_language(text: str) -> str:
    """
    简单的语言检测（基于字符特征）
    Args:
        text: 输入文本
    Returns:
        语言代码 ('en', 'zh', 'unknown')
    """
    if not text:
        return "unknown"

    # 统计中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(re.sub(r'\s', '', text))

    if total_chars == 0:
        return "unknown"

    chinese_ratio = chinese_chars / total_chars

    if chinese_ratio > 0.3:
        return "zh"
    else:
        return "en"


def format_citation(title: str, authors: str, venue: str, year: int) -> str:
    """
    格式化引用
    Args:
        title: 论文标题
        authors: 作者
        venue: 会议名称
        year: 年份
    Returns:
        格式化的引用字符串
    """
    if not title:
        return ""

    citation_parts = []

    if authors:
        citation_parts.append(authors)

    if title:
        citation_parts.append(f'"{title}"')

    if venue and year:
        citation_parts.append(f"{venue} {year}")

    return ". ".join(citation_parts) + "."


def clean_abstract(abstract: str) -> str:
    """
    清理摘要文本
    Args:
        abstract: 原始摘要
    Returns:
        清理后的摘要
    """
    if not abstract:
        return ""

    # 移除常见的摘要前缀
    prefixes_to_remove = [
        r'^\s*abstract\s*[:\-]?\s*',
        r'^\s*摘要\s*[:\-]?\s*',
        r'^\s*this\s+paper\s+',
        r'^\s*we\s+present\s+',
    ]

    for prefix in prefixes_to_remove:
        abstract = re.sub(prefix, '', abstract, flags=re.IGNORECASE)

    # 清理文本
    abstract = normalize_text(abstract)

    # 移除无意义的结尾
    abstract = re.sub(r'\s*\.\s*$', '.', abstract)

    return abstract.strip()