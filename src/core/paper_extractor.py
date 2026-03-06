"""
单篇论文信息提取模块
支持从ACL论文URL提取标题、摘要和PDF信息
"""
import re
import requests
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from ..models.paper import Paper
from ..core.parser import PaperParser
from ..config.settings import Config
from ..config.constants import BASE_URL, HTTP_OK


class PaperExtractor:
    """单篇论文信息提取器"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化提取器
        Args:
            config: 配置对象
        """
        self.config = config or Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.session.timeout = self.config.get('scraper', 'timeout', 30)

    def extract_from_url(self, url: str, download_pdf: bool = False) -> Dict[str, Any]:
        """
        从URL提取论文信息
        Args:
            url: ACL论文URL
            download_pdf: 是否下载PDF文件
        Returns:
            包含论文信息的字典
        """
        if not self._is_acl_url(url):
            return {
                'success': False,
                'error': 'URL不是有效的ACL Anthology链接'
            }

        try:
            # 获取页面内容
            response = self.session.get(url)
            response.encoding = 'utf-8'

            if response.status_code != HTTP_OK:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}'
                }

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取基本信息
            paper_info = self._extract_paper_info(soup, url)

            if not paper_info['title']:
                return {
                    'success': False,
                    'error': '无法提取论文信息，请确认URL是否正确'
                }

            # 下载PDF（如果需要）
            pdf_path = None
            if download_pdf and paper_info.get('pdf_url'):
                pdf_path = self._download_pdf(paper_info['pdf_url'], paper_info['title'])

            # 构建结果
            result = {
                'success': True,
                'title': paper_info['title'],
                'abstract': paper_info['abstract'],
                'pdf_url': paper_info['pdf_url'],
                'authors': paper_info.get('authors', []),
                'venue': paper_info.get('venue', ''),
                'year': paper_info.get('year', 0),
                'session': paper_info.get('session', ''),
                'pages': paper_info.get('pages', ''),
                'doi': paper_info.get('doi', ''),
                'pdf_path': pdf_path,
                'original_url': url
            }

            return result

        except Exception as e:
            return {
                'success': False,
                'error': f'提取信息时出错: {str(e)}'
            }

    def _is_acl_url(self, url: str) -> bool:
        """检查是否为ACL Anthology URL"""
        acl_domains = [
            'aclanthology.org',
            'www.aclanthology.org'
        ]
        return any(domain in url.lower() for domain in acl_domains)

    def _extract_paper_info(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """从BeautifulSoup对象中提取论文信息"""
        paper_info = {
            'title': '',
            'abstract': '',
            'pdf_url': '',
            'authors': [],
            'venue': '',
            'year': 0,
            'session': '',
            'pages': '',
            'doi': ''
        }

        # 提取标题
        title = self._extract_title(soup)
        paper_info['title'] = title

        # 提取摘要
        abstract = self._extract_abstract(soup)
        paper_info['abstract'] = abstract

        # 提取PDF URL
        pdf_url = self._extract_pdf_url(soup, url)
        paper_info['pdf_url'] = pdf_url

        # 提取作者
        authors = self._extract_authors(soup)
        paper_info['authors'] = authors

        # 提取会议信息
        venue, year = self._extract_venue_year(soup, url)
        paper_info['venue'] = venue
        paper_info['year'] = year

        # 提取其他信息
        paper_info['session'] = self._extract_session(soup)
        paper_info['pages'] = self._extract_pages(soup)
        paper_info['doi'] = self._extract_doi(soup)

        return paper_info

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取论文标题"""
        # 尝试多种方式提取标题
        title_selectors = [
            'h2[id*="title"]',
            'h1[id*="title"]',
            '.title',
            'h2',
            'h1',
            'title'
        ]

        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                title = element.get_text().strip()
                # 过滤掉网站标题
                if title and 'ACL Anthology' not in title and len(title) > 10:
                    return re.sub(r'\s+', ' ', title)

        # 备用方法：从页面内容中查找标题
        content_div = soup.find('div', class_='paper')
        if content_div:
            title_elem = content_div.find(['h1', 'h2', 'h3'])
            if title_elem:
                title = title_elem.get_text().strip()
                if len(title) > 10:
                    return re.sub(r'\s+', ' ', title)

        return ''

    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """提取论文摘要"""
        # 使用现有的摘要提取功能
        return PaperParser.extract_abstract(soup.get_text())

    def _extract_pdf_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """提取PDF URL"""
        # 查找PDF链接
        pdf_links = soup.find_all('a', href=True)
        for link in pdf_links:
            href = link['href']
            link_text = link.get_text().lower().strip()

            if ('pdf' in link_text and href.endswith('.pdf')) or \
               ('download' in link_text and 'pdf' in href):

                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"https://aclanthology.org{href}"
                else:
                    # 相对路径处理
                    base_parts = base_url.split('/')
                    if len(base_parts) > 3:
                        return '/'.join(base_parts[:-1]) + '/' + href

        return ''

    def _extract_authors(self, soup: BeautifulSoup) -> list:
        """提取作者信息"""
        authors = []

        # 尝试多种作者选择器
        author_selectors = [
            '.authors',
            '[id*="author"]',
            '.paper-authors'
        ]

        for selector in author_selectors:
            author_elements = soup.select(selector)
            for element in author_elements:
                # 提取作者链接或文本
                author_links = element.find_all('a')
                if author_links:
                    for link in author_links:
                        author_name = link.get_text().strip()
                        if author_name and len(author_name) > 1:
                            authors.append(author_name)
                else:
                    # 如果没有链接，直接提取文本
                    author_text = element.get_text().strip()
                    if author_text:
                        # 分割多个作者
                        author_names = re.split(r'[,;and]', author_text)
                        for name in author_names:
                            name = name.strip()
                            if name and len(name) > 1:
                                authors.append(name)

                if authors:  # 如果找到作者，停止搜索
                    break

        # 备用方法：在页面中查找包含作者信息的元素
        if not authors:
            content = soup.get_text()
            # 查找可能的作者模式
            author_patterns = [
                r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
            ]

            for pattern in author_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, str) and len(match) > 3:
                        authors.append(match.strip())

        # 去重
        return list(set(authors))

    def _extract_venue_year(self, soup: BeautifulSoup, url: str) -> tuple[str, int]:
        """提取会议和年份信息"""
        venue = ''
        year = 0

        # 从URL中提取年份
        year_match = re.search(r'(\d{4})', url)
        if year_match:
            year = int(year_match.group(1))

        # 从URL中提取会议
        venue_patterns = [
            r'/([A-Za-z]+)\-\d{4}/',
            r'/events/([A-Za-z]+)-\d{4}',
        ]

        for pattern in venue_patterns:
            match = re.search(pattern, url)
            if match:
                venue = match.group(1).upper()
                break

        # 从页面内容中提取
        if not venue or not year:
            content = soup.get_text()

            # 查找会议信息
            venue_patterns_content = [
                r'(ACL|EMNLP|NAACL|EACL|COLING|AACL|WMT|SEMEVAL|CoNLL|LREC)\s+(\d{4})',
                r'Proceedings\s+of\s+\d+\w*\s+(ACL|EMNLP|NAACL|EACL|COLING|AACL|WMT|SEMEVAL|CoNLL|LREC)\s+(\d{4})',
            ]

            for pattern in venue_patterns_content:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        venue, year_str = match.groups()
                    else:
                        venue = match.group(1)
                        # 查找年份
                        year_search = re.search(r'(\d{4})', match.group(0))
                        if year_search:
                            year_str = year_search.group(1)
                        else:
                            continue
                    venue = venue.upper()
                    year = int(year_str)
                    break

        return venue, year

    def _extract_session(self, soup: BeautifulSoup) -> str:
        """提取会议场次信息"""
        session_selectors = [
            '.session',
            '[id*="session"]',
            '.paper-session'
        ]

        for selector in session_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()

        return ''

    def _extract_pages(self, soup: BeautifulSoup) -> str:
        """提取页码信息"""
        # 查找页码模式
        content = soup.get_text()
        page_patterns = [
            r'pages?\s+(\d+(?:-\d+)?)',
            r'pp\.\s*(\d+(?:-\d+)?)',
            r'(\d+(?:-\d+)?)\s*pages?'
        ]

        for pattern in page_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return ''

    def _extract_doi(self, soup: BeautifulSoup) -> str:
        """提取DOI信息"""
        doi_patterns = [
            r'https?://doi\.org/([^\s]+)',
            r'DOI:\s*([^\s\n]+)',
            r'doi:\s*([^\s\n]+)'
        ]

        content = soup.get_text()
        for pattern in doi_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                doi = match.group(1)
                if not doi.startswith('https://'):
                    doi = f"https://doi.org/{doi}"
                return doi

        return ''

    def _download_pdf(self, pdf_url: str, title: str) -> Optional[str]:
        """下载PDF文件"""
        if not pdf_url:
            return None

        try:
            response = self.session.get(pdf_url, stream=True)
            if response.status_code == HTTP_OK:
                # 生成文件名
                from ..utils.file_utils import clean_filename
                safe_title = clean_filename(title, 100)
                filename = f"{safe_title}.pdf"

                # 保存文件
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                return filename
            else:
                print(f"PDF下载失败，HTTP状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"PDF下载时出错: {e}")
            return None

    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()