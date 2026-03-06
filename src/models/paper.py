"""
论文数据模型
定义论文的数据结构和相关操作
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import json


@dataclass
class Paper:
    """论文数据模型"""
    title: str
    pdf_url: str
    venue: str = ""
    year: int = 0
    abstract_id: Optional[str] = None
    abstract: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """从字典创建Paper实例"""
        return cls(**data)

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Paper':
        """从JSON字符串创建Paper实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_safe_filename(self, max_length: int = 100) -> str:
        """获取安全的文件名"""
        import re
        # 移除非法字符并替换为下划线
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', self.title)
        # 移除多余的空格和下划线
        safe_name = re.sub(r'[_\s]+', '_', safe_name.strip())
        # 限制长度
        return safe_name[:max_length].strip('_')

    def get_relative_path(self, base_dir: str = "papers") -> str:
        """获取文件的相对存储路径"""
        safe_title = self.get_safe_filename()
        return f"{base_dir}/{self.venue}/{self.year}/{safe_title}.pdf"

    def __str__(self) -> str:
        return f"{self.title} ({self.venue} {self.year})"

    def __repr__(self) -> str:
        return f"Paper(title='{self.title[:50]}...', venue='{self.venue}', year={self.year})"


@dataclass
class DownloadTask:
    """下载任务模型"""
    paper: Paper
    pdf_path: str
    abstract_path: str
    status: str = "pending"  # pending, downloading, completed, failed
    error_message: Optional[str] = None

    def mark_success(self):
        """标记下载成功"""
        self.status = "completed"
        self.error_message = None

    def mark_failed(self, error_message: str):
        """标记下载失败"""
        self.status = "failed"
        self.error_message = error_message

    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.status == "failed"


class PaperList:
    """论文列表管理类"""

    def __init__(self, papers: Optional[List[Paper]] = None):
        self.papers = papers or []

    def add_paper(self, paper: Paper):
        """添加论文"""
        self.papers.append(paper)

    def add_papers(self, papers: List[Paper]):
        """批量添加论文"""
        self.papers.extend(papers)

    def get_by_venue(self, venue: str) -> 'PaperList':
        """按会议筛选"""
        filtered = [p for p in self.papers if p.venue.upper() == venue.upper()]
        return PaperList(filtered)

    def get_by_year(self, year: int) -> 'PaperList':
        """按年份筛选"""
        filtered = [p for p in self.papers if p.year == year]
        return PaperList(filtered)

    def get_by_venue_year(self, venue: str, year: int) -> 'PaperList':
        """按会议和年份筛选"""
        filtered = [
            p for p in self.papers
            if p.venue.upper() == venue.upper() and p.year == year
        ]
        return PaperList(filtered)

    def limit(self, count: int) -> 'PaperList':
        """限制数量"""
        return PaperList(self.papers[:count])

    def to_dicts(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [paper.to_dict() for paper in self.papers]

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dicts(), ensure_ascii=False, indent=2)

    def save_to_file(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def from_dicts(cls, data: List[Dict[str, Any]]) -> 'PaperList':
        """从字典列表创建"""
        papers = [Paper.from_dict(item) for item in data]
        return cls(papers)

    @classmethod
    def from_json_file(cls, filepath: str) -> 'PaperList':
        """从JSON文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dicts(data)

    def __len__(self) -> int:
        return len(self.papers)

    def __iter__(self):
        return iter(self.papers)

    def __getitem__(self, index):
        return self.papers[index]

    def __str__(self) -> str:
        return f"PaperList({len(self.papers)} papers)"