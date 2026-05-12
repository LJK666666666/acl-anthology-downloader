"""
HTML解析器模块
负责解析ACL Anthology的HTML页面，提取论文信息
"""
import re
from typing import Optional, List
from bs4 import BeautifulSoup
from ..models.paper import Paper
from ..config.constants import BASE_URL


class PaperParser:
    """论文HTML解析器"""

    @staticmethod
    def parse_paper_list(html: str, venue: str, year: int) -> List[Paper]:
        """
        解析论文列表页面，提取所有论文信息
        Args:
            html: HTML内容
            venue: 会议名称
            year: 年份
        Returns:
            论文列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        papers = []

        # 尝试不同的选择器来找到论文元素
        paper_elements = (
            soup.select('div.d-sm-flex.align-items-stretch') or
            soup.select('p.d-sm-flex.align-items-stretch') or
            soup.find_all('div', class_='paper') or
            soup.find_all('li', class_='paper')
        )

        for element in paper_elements:
            paper = PaperParser.extract_paper_info(element, venue, year)
            if paper:
                papers.append(paper)

        return papers

    @staticmethod
    def extract_paper_info(element, venue: str, year: int) -> Optional[Paper]:
        """
        从HTML元素中提取论文信息
        Args:
            element: BeautifulSoup元素
            venue: 会议名称
            year: 年份
        Returns:
            Paper对象或None
        """
        try:
            # 提取标题
            title_elem = (
                element.find('strong') or
                element.find('a', class_='align-middle') or
                element.find('a', class_='title') or
                element.find('h4') or
                element.find('h3')
            )

            if not title_elem:
                return None

            title = title_elem.get_text().strip()
            if not title:
                return None

            # 清理标题
            title = re.sub(r'\s+', ' ', title)

            # 提取链接信息
            pdf_url = None
            abstract_id = None

            for link in element.find_all('a'):
                href = link.get('href', '')
                link_text = link.get_text().lower().strip()

                # PDF链接
                if 'pdf' in link_text and href.endswith('.pdf'):
                    if href.startswith('http'):
                        pdf_url = href
                    else:
                        pdf_url = f"{BASE_URL}{href}"

                # 摘要链接 (支持 href 和 data-bs-target)
                elif 'abs' in link_text or 'abstract' in link_text:
                    target = href if '#' in href else link.get('data-bs-target', '')
                    if '#' in target:
                        abstract_id = target.split('#')[-1]

            # 必须有PDF链接才算有效论文
            if pdf_url:
                return Paper(
                    title=title,
                    pdf_url=pdf_url,
                    venue=venue.upper(),
                    year=year,
                    abstract_id=abstract_id
                )

        except Exception as e:
            print(f"提取论文信息时出错: {e}")

        return None

    @staticmethod
    def extract_abstract(html: str, abstract_id: Optional[str] = None) -> str:
        """
        从论文详情页面提取摘要
        Args:
            html: 论文详情页面HTML
            abstract_id: 摘要元素ID
        Returns:
            摘要文本
        """
        if not html:
            return "摘要不可用"

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 方法1：通过abstract_id精准查找
            if abstract_id:
                abstract_div = soup.find('div', id=abstract_id)
                if abstract_div:
                    text = abstract_div.get_text().strip()
                    if len(text) > 50:  # 确保内容足够长
                        return re.sub(r'\s+', ' ', text)

            # 方法2：查找含abstract类的容器
            abstract_selectors = [
                'div[id*="abstract"]',
                'div[class*="abstract"]',
                '.abstract',
                '[data-testid="abstract"]'
            ]

            for selector in abstract_selectors:
                containers = soup.select(selector)
                for container in containers:
                    text = container.get_text().strip()
                    if len(text) > 50:
                        return re.sub(r'\s+', ' ', text)

            # 方法3：查找含"Abstract"关键词的段落
            abstract_keywords = ['abstract', '摘要', 'abstract:']
            for elem in soup.find_all(['p', 'div', 'section']):
                text = elem.get_text().strip().lower()
                if any(keyword in text for keyword in abstract_keywords):
                    full_text = elem.get_text().strip()
                    # 确保内容足够长且不是标题
                    if len(full_text) > 100 and len(full_text.split()) > 10:
                        return re.sub(r'\s+', ' ', full_text)

            return "摘要未找到"

        except Exception as e:
            return f"获取摘要失败: {e}"

    @staticmethod
    def get_paper_count(html: str) -> int:
        """
        从页面获取论文数量
        Args:
            html: 页面HTML
        Returns:
            论文数量
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            paper_elements = (
                soup.select('div.d-sm-flex.align-items-stretch') or
                soup.select('p.d-sm-flex.align-items-stretch')
            )
            return len(paper_elements)
        except Exception:
            return 0

    @staticmethod
    def validate_venue(html: str, expected_venue: str) -> bool:
        """
        验证页面是否包含指定会议的信息
        Args:
            html: 页面HTML
            expected_venue: 期望的会议名称
        Returns:
            是否匹配
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            page_title = soup.title.get_text().lower() if soup.title else ""
            page_text = soup.get_text().lower()

            expected_venue = expected_venue.lower()

            # 检查标题和页面内容
            return expected_venue in page_title or expected_venue in page_text
        except Exception:
            return False

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本内容
        Args:
            text: 原始文本
        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 移除HTML标签（如果有）
        text = re.sub(r'<[^>]+>', '', text)

        return text