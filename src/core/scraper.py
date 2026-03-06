"""
网络爬虫模块
负责从ACL Anthology网站获取论文信息
"""
import time
import requests
from typing import List, Optional
from tqdm import tqdm
from ..models.paper import Paper, PaperList
from ..core.parser import PaperParser
from ..config.settings import Config
from ..config.constants import HTTP_OK, HTTP_NOT_FOUND


class ACLScraper:
    """ACL Anthology爬虫"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化爬虫
        Args:
            config: 配置对象
        """
        self.config = config or Config()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        创建HTTP会话
        Returns:
            配置好的requests.Session对象
        """
        session = requests.Session()

        # 设置请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # 设置超时
        timeout = self.config.get('scraper', 'timeout', 30)
        session.timeout = timeout

        return session

    def get_papers_by_venue_year(self, venue: str, year: int) -> List[Paper]:
        """
        获取指定会议和年份的论文
        Args:
            venue: 会议名称 (如 ACL, EMNLP)
            year: 年份
        Returns:
            论文列表
        """
        venue = venue.upper()
        base_url = self.config.get('scraper', 'events_url', 'https://aclanthology.org/events/')
        url = f"{base_url}{venue.lower()}-{year}/"

        try:
            response = self._make_request(url)
            if response and response.status_code == HTTP_OK:
                # 验证页面是否包含正确的会议信息
                if not PaperParser.validate_venue(response.text, venue):
                    print(f"警告: 页面可能不包含 {venue} {year} 的信息")
                    return []

                papers = PaperParser.parse_paper_list(response.text, venue, year)
                print(f"找到 {len(papers)} 篇 {venue} {year} 的论文")
                return papers
            else:
                print(f"获取 {venue} {year} 页面失败，状态码: {response.status_code if response else 'None'}")
                return []

        except Exception as e:
            print(f"获取 {venue} {year} 论文时出错: {e}")
            return []

    def get_papers_by_range(self, venue: str, start_year: int, end_year: int) -> List[Paper]:
        """
        获取指定会议和时间范围内的所有论文
        Args:
            venue: 会议名称
            start_year: 开始年份
            end_year: 结束年份
        Returns:
            论文列表
        """
        venue = venue.upper()
        years = list(range(start_year, end_year + 1))
        all_papers = []

        print(f"正在获取 {venue} {start_year}-{end_year} 的论文信息...")

        for year in tqdm(years, desc="Processing years"):
            papers = self.get_papers_by_venue_year(venue, year)
            all_papers.extend(papers)

            # 延迟请求，避免对服务器造成压力
            delay = self.config.get('scraper', 'delay', 0.5)
            if delay > 0:
                time.sleep(delay)

        print(f"总共找到 {len(all_papers)} 篇论文")
        return all_papers

    def get_paper_abstract(self, paper: Paper) -> str:
        """
        获取论文摘要
        Args:
            paper: 论文对象
        Returns:
            摘要文本
        """
        if not paper.pdf_url:
            return "摘要不可用：无PDF链接"

        try:
            # 构造论文详情页面URL
            paper_page_url = paper.pdf_url.replace('.pdf', '/')
            response = self._make_request(paper_page_url)

            if response and response.status_code == HTTP_OK:
                abstract = PaperParser.extract_abstract(response.text, paper.abstract_id)
                return abstract
            else:
                return f"摘要不可用：无法访问论文页面 (状态码: {response.status_code if response else 'None'})"

        except Exception as e:
            return f"获取摘要失败: {e}"

    def test_venue_availability(self, venue: str, year: int) -> bool:
        """
        测试指定会议和年份是否可用
        Args:
            venue: 会议名称
            year: 年份
        Returns:
            是否可用
        """
        base_url = self.config.get('scraper', 'events_url', 'https://aclanthology.org/events/')
        url = f"{base_url}{venue.lower()}-{year}/"

        try:
            response = self._make_request(url)
            if response and response.status_code == HTTP_OK:
                # 检查是否有论文内容
                paper_count = PaperParser.get_paper_count(response.text)
                return paper_count > 0
            elif response and response.status_code == HTTP_NOT_FOUND:
                return False
            else:
                return False

        except Exception:
            return False

    def get_available_years(self, venue: str, start_year: int, end_year: int) -> List[int]:
        """
        获取可用的年份列表
        Args:
            venue: 会议名称
            start_year: 开始年份
            end_year: 结束年份
        Returns:
            可用的年份列表
        """
        available_years = []
        venue = venue.upper()

        print(f"检查 {venue} 会议的可用年份...")

        for year in range(start_year, end_year + 1):
            if self.test_venue_availability(venue, year):
                available_years.append(year)
                print(f"  ✓ {venue} {year} - 可用")
            else:
                print(f"  ✗ {venue} {year} - 不可用或无论文")

            delay = self.config.get('scraper', 'delay', 0.5)
            if delay > 0:
                time.sleep(delay)

        return available_years

    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        发送HTTP请求，支持重试
        Args:
            url: 请求URL
            max_retries: 最大重试次数
        Returns:
            响应对象或None
        """
        retry_delay = self.config.get('scraper', 'retry_delay', 1.0)

        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.config.get('scraper', 'timeout', 30))
                response.encoding = 'utf-8'
                return response

            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    print(f"请求失败，正在重试 ({attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                else:
                    print(f"请求最终失败: {e}")
                    return None

        return None

    def close(self):
        """关闭HTTP会话"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class PaperScraperManager:
    """论文爬虫管理器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def scrape_papers(self, venue: str, start_year: int, end_year: int,
                     max_download: Optional[int] = None) -> PaperList:
        """
        爬取论文
        Args:
            venue: 会议名称
            start_year: 开始年份
            end_year: 结束年份
            max_download: 最大下载数量
        Returns:
            论文列表
        """
        with ACLScraper(self.config) as scraper:
            papers = scraper.get_papers_by_range(venue, start_year, end_year)

            if max_download and len(papers) > max_download:
                papers = papers[:max_download]
                print(f"限制下载数量为: {max_download} 篇")

            return PaperList(papers)

    def scrape_single_year(self, venue: str, year: int) -> PaperList:
        """
        爬取单个年份的论文
        Args:
            venue: 会议名称
            year: 年份
        Returns:
            论文列表
        """
        with ACLScraper(self.config) as scraper:
            papers = scraper.get_papers_by_venue_year(venue, year)
            return PaperList(papers)

    def get_available_venues(self) -> List[str]:
        """
        获取支持的会议列表
        Returns:
            会议列表
        """
        return self.config.get('cli', 'supported_venues', [])