"""
文件下载器模块
负责下载论文PDF和摘要文件
"""
import os
import json
import time
import requests
from typing import List, Optional
from tqdm import tqdm
from ..models.paper import Paper, PaperList, DownloadTask
from ..core.scraper import ACLScraper
from ..utils.file_utils import ensure_dir, clean_filename
from ..config.settings import Config
from ..config.constants import (
    HTTP_OK, METADATA_FILENAME, PDF_EXTENSION, ABSTRACT_EXTENSION,
    STATUS_PENDING, STATUS_COMPLETED, STATUS_FAILED, STATUS_SKIPPED,
    STATUS_DOWNLOADING
)


class PaperDownloader:
    """论文文件下载器"""

    def __init__(self, config: Optional[Config] = None, resume_mode: bool = False):
        """
        初始化下载器
        Args:
            config: 配置对象
            resume_mode: 是否为恢复模式（不覆盖 metadata.json）
        """
        self.config = config or Config()
        self.output_dir = os.path.abspath(self.config.get('downloader', 'output_dir', 'papers'))
        self.download_abstracts = self.config.get('downloader', 'download_abstracts', True)
        self.max_filename_length = self.config.get('downloader', 'max_filename_length', 100)
        self.create_year_dirs = self.config.get('downloader', 'create_year_dirs', True)
        self.create_venue_dirs = self.config.get('downloader', 'create_venue_dirs', True)
        self.resume_mode = resume_mode

        # 创建下载会话
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        session.timeout = self.config.get('scraper', 'timeout', 30)
        return session

    def filter_missing_papers(self, papers: List[Paper]) -> List[Paper]:
        """
        过滤出缺失或不完整的论文
        Args:
            papers: 论文列表
        Returns:
            需要下载的论文列表
        """
        missing_papers = []
        for paper in papers:
            pdf_path, _ = self._get_file_paths(paper)
            # 文件不存在或文件太小（不完整）
            if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 1024:
                missing_papers.append(paper)
        return missing_papers

    def download_papers(self, papers: List[Paper], max_download: Optional[int] = None) -> int:
        """
        下载论文文件
        Args:
            papers: 论文列表
            max_download: 最大下载数量
        Returns:
            成功下载的数量
        """
        if not papers:
            print("没有论文需要下载")
            return 0

        # 控制下载数量
        if max_download and max_download > 0:
            papers = papers[:max_download]
            print(f"限制下载数量为: {max_download} 篇")
        else:
            print(f"将下载全部 {len(papers)} 篇论文")

        # 创建输出目录
        ensure_dir(self.output_dir)

        # 创建下载任务
        download_tasks = self._create_download_tasks(papers)

        # 执行下载
        success_count = 0
        with tqdm(download_tasks, desc="Downloading papers") as pbar:
            for task in pbar:
                result = self._download_single_paper(task)
                if result:
                    success_count += 1

                # 更新进度条描述
                pbar.set_postfix({
                    'success': success_count,
                    'failed': len([t for t in download_tasks[:pbar.n+1] if t.is_failed()]),
                    'skipped': len([t for t in download_tasks[:pbar.n+1] if t.status == STATUS_SKIPPED])
                })

                # 请求延迟
                delay = self.config.get('scraper', 'delay', 0.5)
                if delay > 0:
                    time.sleep(delay)

        # 保存元数据（resume 模式不覆盖）
        if not self.resume_mode:
            self._save_metadata(papers)

        return success_count

    def _create_download_tasks(self, papers: List[Paper]) -> List[DownloadTask]:
        """
        创建下载任务
        Args:
            papers: 论文列表
        Returns:
            下载任务列表
        """
        tasks = []

        for paper in papers:
            pdf_path, abstract_path = self._get_file_paths(paper)
            task = DownloadTask(paper, pdf_path, abstract_path)

            # 检查文件是否已存在
            if os.path.exists(pdf_path):
                task.status = STATUS_SKIPPED
            else:
                task.status = STATUS_PENDING

            tasks.append(task)

        return tasks

    def _get_file_paths(self, paper: Paper) -> tuple[str, str]:
        """
        获取论文和摘要的文件路径
        Args:
            paper: 论文对象
        Returns:
            (PDF文件路径, 摘要文件路径)
        """
        safe_title = clean_filename(paper.title, self.max_filename_length)

        # 构建目录路径
        if self.create_venue_dirs and self.create_year_dirs:
            # papers/venue/year/
            dir_path = os.path.join(self.output_dir, paper.venue, str(paper.year))
        elif self.create_venue_dirs:
            # papers/venue/
            dir_path = os.path.join(self.output_dir, paper.venue)
        else:
            # papers/
            dir_path = self.output_dir

        # 确保目录存在
        ensure_dir(dir_path)

        # 构建文件路径
        pdf_path = os.path.join(dir_path, f"{safe_title}{PDF_EXTENSION}")
        abstract_path = os.path.join(dir_path, f"{safe_title}{ABSTRACT_EXTENSION}")

        return pdf_path, abstract_path

    def _download_single_paper(self, task: DownloadTask) -> bool:
        """
        下载单个论文
        Args:
            task: 下载任务
        Returns:
            是否成功
        """
        if task.status == STATUS_SKIPPED:
            print(f"○ 文件已存在: {os.path.relpath(task.pdf_path, self.output_dir)}")
            return True

        if task.status != STATUS_PENDING:
            return False

        task.status = STATUS_DOWNLOADING

        try:
            # 下载PDF
            success = self._download_pdf(task.paper, task.pdf_path)
            if success:
                task.mark_success()

                # 下载摘要（如果启用）
                if self.download_abstracts:
                    self._download_abstract(task.paper, task.abstract_path)

                print(f"✓ 下载成功: {os.path.relpath(task.pdf_path, self.output_dir)}")
                return True
            else:
                error_msg = f"PDF下载失败"
                task.mark_failed(error_msg)
                print(f"✗ 下载失败: {task.paper.title[:50]}... - {error_msg}")
                return False

        except Exception as e:
            error_msg = str(e)
            task.mark_failed(error_msg)
            print(f"✗ 下载出错: {task.paper.title[:50]}... - {error_msg}")
            return False

    def _download_pdf(self, paper: Paper, pdf_path: str) -> bool:
        """
        下载PDF文件
        Args:
            paper: 论文对象
            pdf_path: PDF文件保存路径
        Returns:
            是否成功
        """
        try:
            response = self.session.get(paper.pdf_url, stream=True, timeout=self.config.get('scraper', 'timeout', 30))

            if response.status_code == HTTP_OK:
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                    print(f"警告: 内容类型不是PDF: {content_type}")

                # 下载文件
                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # 验证文件大小
                if os.path.getsize(pdf_path) < 1024:  # 小于1KB可能是错误页面
                    os.remove(pdf_path)
                    return False

                return True
            else:
                print(f"HTTP错误 {response.status_code}: {paper.pdf_url}")
                return False

        except Exception as e:
            print(f"下载PDF时出错: {e}")
            return False

    def _download_abstract(self, paper: Paper, abstract_path: str):
        """
        下载摘要
        Args:
            paper: 论文对象
            abstract_path: 摘要文件保存路径
        """
        if os.path.exists(abstract_path):
            return

        try:
            with ACLScraper(self.config) as scraper:
                abstract = scraper.get_paper_abstract(paper)

                with open(abstract_path, 'w', encoding='utf-8') as f:
                    f.write(abstract)

        except Exception as e:
            print(f"下载摘要时出错: {e}")

    def _save_metadata(self, papers: List[Paper]):
        """
        保存论文元数据
        Args:
            papers: 论文列表
        """
        try:
            metadata_path = os.path.join(self.output_dir, METADATA_FILENAME)

            # 构建元数据
            metadata = []
            for paper in papers:
                pdf_path, abstract_path = self._get_file_paths(paper)
                metadata.append({
                    'title': paper.title,
                    'year': paper.year,
                    'venue': paper.venue,
                    'pdf_url': paper.pdf_url,
                    'abstract_id': paper.abstract_id,
                    'pdf_file': os.path.relpath(pdf_path, self.output_dir),
                    'abstract_file': os.path.relpath(abstract_path, self.output_dir) if self.download_abstracts else None,
                })

            # 保存到文件
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"元数据已保存: {metadata_path}")

        except Exception as e:
            print(f"保存元数据时出错: {e}")

    def get_download_stats(self) -> dict:
        """
        获取下载统计信息
        Returns:
            统计信息字典
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'pdf_count': 0,
            'abstract_count': 0,
        }

        if not os.path.exists(self.output_dir):
            return stats

        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    stats['total_files'] += 1
                    stats['total_size'] += os.path.getsize(file_path)

                    if file.endswith(PDF_EXTENSION):
                        stats['pdf_count'] += 1
                    elif file.endswith(ABSTRACT_EXTENSION):
                        stats['abstract_count'] += 1

        return stats

    def cleanup_incomplete_downloads(self):
        """
        清理不完整的下载
        """
        incomplete_files = []

        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith(PDF_EXTENSION):
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) < 1024:  # 小于1KB认为不完整
                        incomplete_files.append(file_path)

        for file_path in incomplete_files:
            try:
                os.remove(file_path)
                print(f"已删除不完整文件: {file_path}")
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")

    def close(self):
        """关闭下载器"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()