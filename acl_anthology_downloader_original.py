import requests
from bs4 import BeautifulSoup
import os
import re
import time
from tqdm import tqdm
import json
import urllib.parse


def get_paper_links(venue, start_year, end_year):
    """获取指定Venue和时间范围内所有论文的详细信息"""
    venue = venue.upper()
    base_search_url = "https://aclanthology.org/events/"
    years = list(range(int(start_year), int(end_year) + 1))
    all_papers = []

    for year in tqdm(years, desc="Processing years"):
        event_url = f"{base_search_url}{venue.lower()}-{year}/"
        try:
            response = requests.get(event_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            paper_elements = soup.find_all('p', class_='d-sm-flex align-items-stretch')

            if not paper_elements:
                paper_elements = soup.find_all('div', class_='card-body')

            for element in paper_elements:
                paper_info = extract_paper_info_from_element(element, venue, year)
                if paper_info:
                    all_papers.append(paper_info)
            time.sleep(0.5)

        except Exception as e:
            print(f"获取 {venue} {year} 论文时出错: {e}")
            continue

    return all_papers


def extract_paper_info_from_element(element, venue, year):
    """从HTML元素中提取论文信息"""
    try:
        title_elem = element.find('strong') or element.find('a', class_='align-middle')
        if not title_elem:
            return None

        title = title_elem.get_text().strip()
        pdf_url = None
        abstract_id = None
        links = element.find_all('a', href=True)

        for link in links:
            href = link['href']
            link_text = link.get_text().lower()
            if 'pdf' in link_text and href.endswith('.pdf'):
                pdf_url = href if href.startswith('http') else f"https://aclanthology.org{href}"
            elif 'abs' in link_text or 'abstract' in link_text:
                if 'href' in link.attrs and '#' in link['href']:
                    abstract_id = link['href'].split('#')[-1]

        if pdf_url:
            return {
                'title': title,
                'pdf_url': pdf_url,
                'abstract_id': abstract_id,
                'venue': venue,
                'year': year
            }

    except Exception as e:
        print(f"提取论文信息时出错: {e}")
    return None


def get_abstract_from_page(paper_info):
    """从论文页面获取摘要内容"""
    if not paper_info.get('abstract_id'):
        return "摘要不可用"

    try:
        pdf_url = paper_info['pdf_url']
        paper_page_url = pdf_url.replace('.pdf', '/')
        response = requests.get(paper_page_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 方法1：通过abstract_id精准查找
        abstract_div = soup.find('div', id=paper_info['abstract_id'])
        if abstract_div:
            abstract_text = abstract_div.get_text().strip()
            return re.sub(r'\s+', ' ', abstract_text)

        # 方法2：查找含abstract类的容器
        abstract_containers = soup.find_all('div', class_=re.compile(r'abstract'))
        for container in abstract_containers:
            text = container.get_text().strip()
            if len(text) > 50:
                return re.sub(r'\s+', ' ', text)

        # 方法3：查找含"Abstract"关键词的段落
        for elem in soup.find_all(['p', 'div']):
            if 'abstract' in elem.get_text().lower() and len(elem.get_text()) > 100:
                return re.sub(r'\s+', ' ', elem.get_text().strip())

        return "摘要未找到"

    except Exception as e:
        print(f"获取摘要时出错: {e}")
        return f"获取摘要失败: {e}"


def clean_filename(filename):
    """清理文件名，移除非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def download_papers(paper_list, output_dir="papers", download_abstracts=True, max_download=None):
    """
    下载PDF文件和摘要（新增：支持指定最大下载数量）
    参数:
        max_download (int/None): 最大下载数量，None表示下载全部
    """
    os.makedirs(output_dir, exist_ok=True)
    metadata_file = os.path.join(output_dir, "metadata.json")
    metadata = []
    success_count = 0

    # ---------------------- 新增：控制下载数量 ----------------------
    total_papers = len(paper_list)
    # 若指定了max_download，截取前N篇论文；若超过总数，自动用总数
    if max_download and isinstance(max_download, int):
        download_list = paper_list[:max_download]
        actual_download = len(download_list)
        print(f"\n📌 已指定最大下载数量：{max_download} 篇")
        print(f"📌 实际可下载论文数量：{actual_download} 篇（总论文数：{total_papers}）")
    else:
        download_list = paper_list
        actual_download = total_papers
        print(f"\n📌 未指定下载数量，将下载全部 {actual_download} 篇论文")
    # ----------------------------------------------------------------

    for paper in tqdm(download_list, desc="Downloading papers"):
        try:
            venue = paper['venue']
            year = str(paper['year'])
            safe_title = clean_filename(paper['title'])[:100]  # 限制标题长度防溢出

            # 创建二级目录：output_dir/venue/year
            paper_subdir = os.path.join(output_dir, venue, year)
            os.makedirs(paper_subdir, exist_ok=True)

            # 生成文件路径（仅含标题）
            pdf_filename = f"{safe_title}.pdf"
            pdf_path = os.path.join(paper_subdir, pdf_filename)
            abstract_filename = f"{safe_title}_abstract.txt"
            abstract_path = os.path.join(paper_subdir, abstract_filename)

            # 下载PDF（检查是否已存在）
            if not os.path.exists(pdf_path):
                response = requests.get(paper['pdf_url'], stream=True)
                if response.status_code == 200:
                    with open(pdf_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    print(f"✓ 下载成功: {venue}/{year}/{pdf_filename}")
                    success_count += 1
                else:
                    print(f"✗ 下载失败: {venue}/{year}/{pdf_filename}, 状态码: {response.status_code}")
                    continue
            else:
                print(f"○ 文件已存在: {venue}/{year}/{pdf_filename}")
                success_count += 1

            # 下载摘要
            if download_abstracts and not os.path.exists(abstract_path):
                abstract = get_abstract_from_page(paper)
                with open(abstract_path, 'w', encoding='utf-8') as f:
                    f.write(abstract)

            # 记录元数据（仅记录已下载的论文）
            metadata.append({
                'title': paper['title'],
                'year': paper['year'],
                'venue': venue,
                'pdf_url': paper['pdf_url'],
                'abstract_id': paper.get('abstract_id', ''),
                'pdf_file': os.path.join(venue, year, pdf_filename),
                'abstract_file': os.path.join(venue, year, abstract_filename)
            })

            time.sleep(0.5)

        except Exception as e:
            print(f"✗ 处理论文时出错 '{paper['title']}': {e}")
            continue

    # 保存元数据
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return success_count


def get_papers_by_venue_year(venue, year):
    """直接获取特定会议和年份的论文"""
    url = f"https://aclanthology.org/events/{venue.lower()}-{year}/"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        items = soup.find_all('p', class_='d-sm-flex align-items-stretch')

        for item in items:
            title_elem = item.find('strong') or item.find('a', class_='align-middle')
            if not title_elem:
                continue

            title = title_elem.get_text().strip()
            pdf_link = None
            abstract_id = None

            for a in item.find_all('a', href=True):
                href = a['href']
                text = a.get_text().lower()
                if 'pdf' in text and href.endswith('.pdf'):
                    pdf_link = href if href.startswith('http') else f"https://aclanthology.org{href}"
                if ('abs' in text or 'abstract' in text) and '#' in href:
                    abstract_id = href.split('#')[-1]

            if pdf_link and abstract_id:
                papers.append({
                    'title': title,
                    'pdf_url': pdf_link,
                    'abstract_id': abstract_id,
                    'venue': venue.upper(),
                    'year': year
                })

        return papers

    except Exception as e:
        print(f"获取论文列表时出错: {e}")
        return []


def main():
    print("=" * 60)
    print("ACL Anthology 论文爬虫 (支持自定义下载数量)")
    print("=" * 60)
    print("文件存储结构：papers/会议名/年份/论文标题.pdf")
    print("可通过修改 max_download 控制下载数量（None=下载全部）")
    print("=" * 60)

    # ---------------------- 配置参数（可直接修改） ----------------------
    venue = 'ACL'  # 目标会议（如 ACL, EMNLP, NAACL）
    start_year = '2025'  # 开始年份
    end_year = '2025'  # 结束年份
    output_dir = 'papers'  # 根输出目录
    max_download = 5  # 最大下载数量（设为None表示下载全部）
    # -------------------------------------------------------------------

    print(f"\n目标会议: {venue}")
    print(f"时间范围: {start_year}-{end_year}")
    print(f"根输出目录: {output_dir}")
    print(f"最大下载数量: {'全部' if max_download is None else max_download} 篇")

    print("\n正在获取论文信息，请稍候...")
    all_papers = []
    for year in range(int(start_year), int(end_year) + 1):
        papers = get_papers_by_venue_year(venue, year)
        all_papers.extend(papers)
        print(f"找到 {len(papers)} 篇 {venue} {year} 的论文")
        time.sleep(0.5)

    print(f"\n总共找到 {len(all_papers)} 篇论文")

    if all_papers:
        print("\n开始下载PDF文件和摘要...")
        # 传入max_download参数控制下载数量
        success_count = download_papers(all_papers, output_dir, download_abstracts=True, max_download=max_download)
        print(f"\n下载完成！成功下载 {success_count} 篇论文")
        print(f"文件存储路径示例：{output_dir}/{venue}/{start_year}/[论文标题].pdf")
        print(f"论文元数据保存在: {output_dir}/metadata.json")

        # 显示前几篇下载的论文位置
        display_count = min(3, success_count)  # 最多显示3篇
        print(f"\n前{display_count}篇论文存储位置:")
        for i, paper in enumerate(all_papers[:display_count]):
            safe_title = clean_filename(paper['title'])[:50]
            print(f"  {i + 1}. {output_dir}/{paper['venue']}/{paper['year']}/{safe_title}...pdf")
    else:
        print("\n未找到任何论文，请检查会议名称和年份范围是否正确")
        print("支持的会议格式: ACL, EMNLP, NAACL, EACL, COLING 等")


if __name__ == "__main__":
    main()