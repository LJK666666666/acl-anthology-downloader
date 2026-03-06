#!/usr/bin/env python3
"""
ACL Anthology 论文下载工具安装脚本
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="acl-anthology-downloader",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to download papers from ACL Anthology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/acl-anthology-downloader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements[:6],  # 只安装核心依赖
    extras_require={
        "dev": requirements[6:],  # 开发依赖
        "data": ["pandas>=1.5.0"],  # 数据分析依赖
    },
    entry_points={
        "console_scripts": [
            "acl-downloader=src.cli.commands:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
)