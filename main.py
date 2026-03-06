#!/usr/bin/env python3
"""
ACL Anthology 论文下载工具 - 重构版
主程序入口

这是重构后的主程序，保持了与原始版本相同的功能，
但采用了模块化设计，提高了可维护性和扩展性。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli.commands import cli


def main():
    """主函数"""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()