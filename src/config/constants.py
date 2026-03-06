"""
常量定义
"""
# URL常量
BASE_URL = "https://aclanthology.org"
EVENTS_URL = f"{BASE_URL}/events/"

# 默认配置
DEFAULT_OUTPUT_DIR = "papers"
DEFAULT_MAX_DOWNLOAD = None
DEFAULT_DELAY = 0.5
DEFAULT_TIMEOUT = 30

# 支持的会议列表
SUPPORTED_VENUES = [
    'ACL', 'EMNLP', 'NAACL', 'EACL', 'COLING', 'AACL', 'WMT', 'SEMEVAL',
    'CoNLL', 'LREC', 'INTERSPEECH', 'ICASSP'
]

# 文件扩展名
PDF_EXTENSION = ".pdf"
ABSTRACT_EXTENSION = "_abstract.txt"
METADATA_FILENAME = "metadata.json"

# HTTP状态码
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

# 正则表达式模式
CLEAN_FILENAME_PATTERN = r'[<>:"/\\|?*]'
MULTI_SPACE_PATTERN = r'[_\s]+'

# 下载状态
STATUS_PENDING = "pending"
STATUS_DOWNLOADING = "downloading"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 秒