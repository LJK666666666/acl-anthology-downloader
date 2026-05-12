"""
命令行接口模块
提供丰富的命令行功能
"""
import click
import sys
import os
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.scraper import PaperScraperManager
from src.core.downloader import PaperDownloader
from src.core.paper_extractor import PaperExtractor
from src.config.settings import Config, get_config, create_default_config_file
from src.models.paper import PaperList
from src.utils.validators import validate_year_range, is_valid_venue, is_valid_url
from src.utils.file_utils import format_file_size, get_directory_size
from src.config.constants import SUPPORTED_VENUES


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config, verbose):
    """ACL Anthology 论文下载工具 - 重构版"""

    # 确保上下文对象存在
    ctx.ensure_object(dict)

    # 加载配置
    if config:
        ctx.obj['config'] = get_config(config)
    else:
        ctx.obj['config'] = get_config()

    # 设置详细输出
    if verbose:
        ctx.obj['config'].set('cli', 'verbose', True)

    # 显示欢迎信息
    if ctx.invoked_subcommand is None:
        click.echo("=" * 60)
        click.echo("ACL Anthology 论文下载工具 (重构版)")
        click.echo("=" * 60)
        click.echo("使用 --help 查看可用命令")
        click.echo("=" * 60)


@cli.command()
@click.option('--venue', '-v', required=True, type=str, help='会议名称 (如 ACL, EMNLP, NAACL)')
@click.option('--start-year', '-s', required=True, type=int, help='开始年份')
@click.option('--end-year', '-e', required=True, type=int, help='结束年份')
@click.option('--output', '-o', default='papers', type=str, help='输出目录 (默认: papers)')
@click.option('--max-download', '-n', type=int, help='最大下载数量')
@click.option('--no-abstract', is_flag=True, help='不下载摘要')
@click.option('--dry-run', is_flag=True, help='仅获取论文列表，不下载')
@click.pass_context
def download(ctx, venue, start_year, end_year, output, max_download, no_abstract, dry_run):
    """下载指定会议和年份范围的论文"""

    config = ctx.obj['config']

    # 验证输入参数
    if not is_valid_venue(venue, SUPPORTED_VENUES):
        click.echo(f"错误: 不支持的会议 '{venue}'")
        click.echo(f"支持的会议: {', '.join(SUPPORTED_VENUES)}")
        sys.exit(1)

    is_valid, error_msg = validate_year_range(start_year, end_year)
    if not is_valid:
        click.echo(f"错误: {error_msg}")
        sys.exit(1)

    # 更新配置（规范化为绝对路径）
    output = os.path.abspath(output)
    config.set('downloader', 'output_dir', output)
    if max_download:
        config.set('downloader', 'max_download', max_download)
    config.set('downloader', 'download_abstracts', not no_abstract)

    click.echo(f"\n目标会议: {venue}")
    click.echo(f"时间范围: {start_year}-{end_year}")
    click.echo(f"输出目录: {output}")
    if max_download:
        click.echo(f"最大下载数量: {max_download}")
    click.echo(f"下载摘要: {'是' if not no_abstract else '否'}")

    try:
        # 获取论文列表
        scraper_manager = PaperScraperManager(config)
        paper_list = scraper_manager.scrape_papers(venue, start_year, end_year, max_download)

        if not paper_list.papers:
            click.echo("\n未找到任何论文，请检查会议名称和年份范围")
            sys.exit(1)

        click.echo(f"\n找到 {len(paper_list)} 篇论文")

        if dry_run:
            click.echo("\n--- 论文列表 (仅显示前10篇) ---")
            for i, paper in enumerate(paper_list.papers[:10], 1):
                click.echo(f"{i:2d}. {paper.title} ({paper.venue} {paper.year})")

            if len(paper_list.papers) > 10:
                click.echo(f"... 还有 {len(paper_list.papers) - 10} 篇论文")
            return

        # 下载论文
        click.echo("\n开始下载...")
        with PaperDownloader(config) as downloader:
            success_count = downloader.download_papers(paper_list.papers, max_download)

            # 显示下载统计
            stats = downloader.get_download_stats()
            click.echo(f"\n下载完成！")
            click.echo(f"成功下载: {success_count} 篇论文")
            click.echo(f"总文件数: {stats['total_files']}")
            click.echo(f"总大小: {format_file_size(stats['total_size'])}")
            click.echo(f"PDF文件: {stats['pdf_count']}")
            if not no_abstract:
                click.echo(f"摘要文件: {stats['abstract_count']}")

            # 显示元数据文件位置
            metadata_path = os.path.join(output, "metadata.json")
            if os.path.exists(metadata_path):
                click.echo(f"元数据已保存: {metadata_path}")

    except KeyboardInterrupt:
        click.echo("\n\n下载被用户中断")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n下载过程中出错: {e}")
        if config.get('cli', 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--venue', '-v', required=True, type=str, help='会议名称')
@click.option('--year', '-y', required=True, type=int, help='年份')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json', 'csv']),
              help='输出格式')
@click.option('--save', '-s', type=click.Path(), help='保存到文件')
def list(venue, year, output_format, save):
    """列出指定会议和年份的论文"""

    # 验证输入
    if not is_valid_venue(venue, SUPPORTED_VENUES):
        click.echo(f"错误: 不支持的会议 '{venue}'")
        click.echo(f"支持的会议: {', '.join(SUPPORTED_VENUES)}")
        sys.exit(1)

    if not is_valid_year(year):
        click.echo(f"错误: 年份无效: {year}")
        sys.exit(1)

    try:
        scraper_manager = PaperScraperManager()
        paper_list = scraper_manager.scrape_single_year(venue, year)

        if not paper_list.papers:
            click.echo(f"未找到 {venue} {year} 的论文")
            return

        click.echo(f"\n{venue} {year} 论文列表 (共 {len(paper_list)} 篇):")
        click.echo("-" * 80)

        if output_format == 'table':
            for i, paper in enumerate(paper_list.papers, 1):
                click.echo(f"{i:3d}. {paper.title}")
                click.echo(f"     URL: {paper.pdf_url}")
                if i < len(paper_list.papers):
                    click.echo()

        elif output_format == 'json':
            json_output = paper_list.to_json()
            if save:
                with open(save, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                click.echo(f"论文列表已保存到: {save}")
            else:
                click.echo(json_output)

        elif output_format == 'csv':
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Title', 'Venue', 'Year', 'PDF URL', 'Abstract ID'])

            for paper in paper_list.papers:
                writer.writerow([
                    paper.title,
                    paper.venue,
                    paper.year,
                    paper.pdf_url,
                    paper.abstract_id or ''
                ])

            csv_content = output.getvalue()

            if save:
                with open(save, 'w', encoding='utf-8', newline='') as f:
                    f.write(csv_content)
                click.echo(f"论文列表已保存到: {save}")
            else:
                click.echo(csv_content)

    except Exception as e:
        click.echo(f"获取论文列表时出错: {e}")
        sys.exit(1)


@cli.command()
def venues():
    """显示支持的会议列表"""
    click.echo("支持的会议列表:")
    click.echo("-" * 30)
    for venue in SUPPORTED_VENUES:
        click.echo(f"  • {venue}")


@cli.command()
@click.option('--directory', '-d', default='papers', type=str, help='论文目录路径')
def stats(directory):
    """显示下载统计信息"""

    if not os.path.exists(directory):
        click.echo(f"错误: 目录 '{directory}' 不存在")
        sys.exit(1)

    from src.utils.file_utils import count_files

    pdf_count = count_files(directory, '.pdf')
    abstract_count = count_files(directory, '_abstract.txt')
    total_size = get_directory_size(directory)

    click.echo(f"论文目录统计: {directory}")
    click.echo("-" * 40)
    click.echo(f"PDF文件: {pdf_count}")
    click.echo(f"摘要文件: {abstract_count}")
    click.echo(f"总大小: {format_file_size(total_size)}")

    # 按会议统计
    if os.path.isdir(directory):
        click.echo("\n按会议统计:")
        click.echo("-" * 20)

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                pdfs = count_files(item_path, '.pdf')
                if pdfs > 0:
                    click.echo(f"  {item}: {pdfs} 篇")


@cli.command()
@click.option('--output', '-o', default='config/default.yaml', type=str, help='配置文件路径')
def init_config(output):
    """创建默认配置文件"""

    try:
        create_default_config_file(output)
        click.echo(f"默认配置文件已创建: {output}")
        click.echo("您可以编辑此文件来自定义下载行为")
    except Exception as e:
        click.echo(f"创建配置文件失败: {e}")
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', default='papers', type=str, help='清理的目录')
def cleanup(directory):
    """清理不完整的下载文件"""

    if not os.path.exists(directory):
        click.echo(f"错误: 目录 '{directory}' 不存在")
        sys.exit(1)

    config = get_config()

    try:
        with PaperDownloader(config) as downloader:
            downloader.output_dir = directory
            downloader.cleanup_incomplete_downloads()
        click.echo("清理完成")
    except Exception as e:
        click.echo(f"清理过程中出错: {e}")
        sys.exit(1)


@cli.command()
@click.option('--venue', '-v', required=True, type=str, help='会议名称')
@click.option('--start-year', '-s', required=True, type=int, help='开始年份')
@click.option('--end-year', '-e', required=True, type=int, help='结束年份')
def check(venue, start_year, end_year):
    """检查指定会议和年份范围是否有可用论文"""

    # 验证输入
    if not is_valid_venue(venue, SUPPORTED_VENUES):
        click.echo(f"错误: 不支持的会议 '{venue}'")
        sys.exit(1)

    is_valid, error_msg = validate_year_range(start_year, end_year)
    if not is_valid:
        click.echo(f"错误: {error_msg}")
        sys.exit(1)

    try:
        from src.core.scraper import ACLScraper

        config = get_config()
        with ACLScraper(config) as scraper:
            available_years = scraper.get_available_years(venue, start_year, end_year)

            click.echo(f"\n{venue} 会议可用年份检查结果:")
            click.echo(f"检查范围: {start_year}-{end_year}")
            click.echo(f"可用年份: {available_years}")
            click.echo(f"可用年份数量: {len(available_years)}")

    except Exception as e:
        click.echo(f"检查过程中出错: {e}")
        sys.exit(1)


def is_valid_year(year):
    """验证年份是否有效"""
    try:
        year_int = int(year)
        return 1990 <= year_int <= 2030
    except (ValueError, TypeError):
        return False


@cli.command()
@click.option('--url', '-u', required=True, type=str, help='ACL论文URL地址')
@click.option('--download-pdf', is_flag=True, help='同时下载PDF文件')
@click.option('--save', '-s', type=click.Path(), help='保存结果到文件')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json', 'text']),
              help='输出格式')
@click.pass_context
def test(ctx, url, download_pdf, save, output_format):
    """测试单篇论文信息提取"""

    # 验证URL
    if not is_valid_url(url):
        click.echo("❌ 错误: 无效的URL格式")
        sys.exit(1)

    click.echo(f"🔍 正在分析论文: {url}")
    click.echo("-" * 60)

    config = ctx.obj['config']

    try:
        with PaperExtractor(config) as extractor:
            result = extractor.extract_from_url(url, download_pdf=download_pdf)

        if result['success']:
            click.echo("✅ 论文信息提取成功！")
            click.echo("=" * 60)

            if output_format == 'table':
                _display_table_format(result)
            elif output_format == 'json':
                _display_json_format(result)
            elif output_format == 'text':
                _display_text_format(result)

            # 保存结果到文件
            if save:
                _save_result_to_file(result, save, output_format)

        else:
            click.echo("❌ 论文信息提取失败")
            click.echo(f"错误原因: {result.get('error', '未知错误')}")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ 处理过程中出现错误: {e}")
        if config.get('cli', 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_table_format(result):
    """以表格格式显示结果"""
    # 标题
    click.echo(f"📄 标题:")
    click.echo(f"   {result['title']}")
    click.echo()

    # 作者
    if result['authors']:
        click.echo(f"👥 作者:")
        for i, author in enumerate(result['authors'], 1):
            click.echo(f"   {i}. {author}")
        click.echo()

    # 会议信息
    if result['venue'] or result['year']:
        click.echo(f"🏛️ 会议信息:")
        if result['venue']:
            click.echo(f"   会议: {result['venue']}")
        if result['year']:
            click.echo(f"   年份: {result['year']}")
        if result['session']:
            click.echo(f"   场次: {result['session']}")
        click.echo()

    # 摘要
    if result['abstract']:
        click.echo(f"📝 摘要:")
        click.echo(f"   {result['abstract']}")
        click.echo()

    # 链接信息
    click.echo(f"🔗 链接信息:")
    click.echo(f"   原文链接: {result['original_url']}")
    if result['pdf_url']:
        click.echo(f"   PDF链接: {result['pdf_url']}")
    if result['doi']:
        click.echo(f"   DOI: {result['doi']}")

    # PDF下载信息
    if result['pdf_path']:
        click.echo()
        click.echo(f"💾 PDF文件:")
        click.echo(f"   保存位置: {result['pdf_path']}")
        from src.utils.file_utils import get_file_size, format_file_size
        size = get_file_size(result['pdf_path'])
        click.echo(f"   文件大小: {format_file_size(size)}")


def _display_json_format(result):
    """以JSON格式显示结果"""
    import json
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


def _display_text_format(result):
    """以纯文本格式显示结果"""
    output = f"""论文信息提取结果
=====================

标题: {result['title']}

作者: {', '.join(result['authors']) if result['authors'] else '未知'}

会议: {result['venue']} {result['year']}

摘要:
{result['abstract']}

链接:
- 原文: {result['original_url']}
- PDF: {result['pdf_url']}
- DOI: {result['doi']}

{f"PDF文件: {result['pdf_path']}" if result['pdf_path'] else ""}
"""
    click.echo(output)


def _save_result_to_file(result, filepath, output_format):
    """保存结果到文件"""
    try:
        import json
        from pathlib import Path

        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            if output_format == 'json':
                json.dump(result, f, ensure_ascii=False, indent=2)
            else:
                # 以文本格式保存
                f.write(f"论文信息提取结果\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"标题: {result['title']}\n\n")
                f.write(f"作者: {', '.join(result['authors']) if result['authors'] else '未知'}\n\n")
                f.write(f"会议: {result['venue']} {result['year']}\n\n")
                f.write(f"摘要:\n{result['abstract']}\n\n")
                f.write(f"链接:\n")
                f.write(f"- 原文: {result['original_url']}\n")
                if result['pdf_url']:
                    f.write(f"- PDF: {result['pdf_url']}\n")
                if result['doi']:
                    f.write(f"- DOI: {result['doi']}\n")
                if result['pdf_path']:
                    f.write(f"\nPDF文件: {result['pdf_path']}\n")

        click.echo(f"\n💾 结果已保存到: {filepath}")

    except Exception as e:
        click.echo(f"\n❌ 保存文件时出错: {e}")


if __name__ == '__main__':
    cli()