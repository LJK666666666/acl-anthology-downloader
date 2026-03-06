# ACL Anthology 论文下载工具 (重构版)

一个用于从 ACL Anthology 网站下载学术论文的工具，支持批量下载和摘要提取。

## 🆕 重构改进

相比原始版本，重构版本具有以下优势：

- **模块化设计**：代码按功能模块分离，提高可维护性
- **丰富的命令行接口**：支持多种操作模式
- **配置驱动**：支持配置文件和环境变量
- **错误处理**：更好的异常处理和恢复机制
- **扩展性**：易于添加新功能和自定义输出格式

## 📦 安装

### 方法1：直接使用

```bash
# 克隆项目
git clone https://github.com/yourusername/acl-anthology-downloader.git
cd acl-anthology-downloader

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py --help
```

### 方法2：安装为包

```bash
# 安装包
pip install -e .

# 使用命令行工具
acl-downloader --help
```

## 🚀 快速开始

### 下载论文

```bash
# 下载 ACL 2024 的所有论文（限制5篇用于测试）
python main.py download -v ACL -s 2024 -e 2024 -n 5

# 下载 EMNLP 2023-2024 的论文
python main.py download -v EMNLP -s 2023 -e 2024 -o emnlp_papers

# 仅获取论文列表，不下载
python main.py download -v NAACL -s 2024 -e 2024 --dry-run
```

### 列出论文

```bash
# 列出 ACL 2024 的论文
python main.py list -v ACL -y 2024

# 以 JSON 格式输出并保存
python main.py list -v ACL -y 2024 --format json --save acl2024.json
```

### 测试单篇论文

```bash
# 分析单篇论文信息
python main.py test -u https://aclanthology.org/2024.acl-long.123/

# 下载PDF并保存信息
python main.py test -u https://aclanthology.org/2024.acl-long.123/ --download-pdf --save paper_info.txt

# 以JSON格式输出
python main.py test -u https://aclanthology.org/2024.acl-long.123/ --format json
```

### 其他功能

```bash
# 查看支持的会议
python main.py venues

# 检查会议年份可用性
python main.py check -v ACL -s 2020 -e 2024

# 查看下载统计
python main.py stats -d papers

# 创建默认配置文件
python main.py init-config -o my_config.yaml

# 清理不完整的下载
python main.py cleanup -d papers
```

## 📋 命令参考

### download - 下载论文

```bash
python main.py download [OPTIONS]

选项:
  -v, --venue TEXT          会议名称 (必需) [ACL, EMNLP, NAACL, ...]
  -s, --start-year INTEGER  开始年份 (必需)
  -e, --end-year INTEGER    结束年份 (必需)
  -o, --output TEXT         输出目录 (默认: papers)
  -n, --max-download INTEGER 最大下载数量
  --no-abstract            不下载摘要
  --dry-run                仅获取论文列表，不下载
  -c, --config PATH        配置文件路径
  -v, --verbose            详细输出
```

### list - 列出论文

```bash
python main.py list [OPTIONS]

选项:
  -v, --venue TEXT          会议名称 (必需)
  -y, --year INTEGER        年份 (必需)
  --format [table|json|csv] 输出格式 (默认: table)
  -s, --save PATH           保存到文件
```

### 其他命令

- `venues` - 显示支持的会议列表
- `stats` - 显示下载统计信息
- `check` - 检查会议年份可用性
- `init-config` - 创建默认配置文件
- `cleanup` - 清理不完整的下载文件
- `test` - 测试单篇论文信息提取

#### test - 测试单篇论文

```bash
python main.py test [OPTIONS]

选项:
  -u, --url TEXT            ACL论文URL (必需)
  --download-pdf           同时下载PDF文件
  -s, --save PATH          保存结果到文件
  --format [table|json|text] 输出格式 (默认: table)
```

**使用示例:**

```bash
# 分析单篇论文
python main.py test -u https://aclanthology.org/2024.acl-long.123/

# 下载PDF并保存结果
python main.py test -u https://aclanthology.org/2024.acl-long.123/ --download-pdf --save paper_info.json --format json

# 以文本格式显示
python main.py test -u https://aclanthology.org/2024.acl-long.123/ --format text
```

## ⚙️ 配置

### 配置文件

创建自定义配置文件：

```bash
python main.py init-config -o config/custom.yaml
```

配置文件示例 (YAML 格式):

```yaml
scraper:
  delay: 1.0              # 请求间隔（秒）
  timeout: 30             # 超时时间（秒）
  max_retries: 3          # 最大重试次数

downloader:
  output_dir: "my_papers"  # 输出目录
  max_download: 100       # 最大下载数量
  download_abstracts: true # 下载摘要
  max_filename_length: 80 # 文件名最大长度

cli:
  verbose: true           # 详细输出
```

### 环境变量

也可以通过环境变量配置：

```bash
export ACL_OUTPUT_DIR="my_papers"
export ACL_MAX_DOWNLOAD=100
export ACL_DELAY=1.0
export ACL_VERBOSE=true
```

## 📁 项目结构

```
acl-anthology-downloader/
├── src/                     # 源代码
│   ├── core/               # 核心功能模块
│   │   ├── scraper.py      # 网络爬虫
│   │   ├── parser.py       # HTML解析器
│   │   └── downloader.py   # 文件下载器
│   ├── models/             # 数据模型
│   │   └── paper.py        # 论文数据模型
│   ├── config/             # 配置管理
│   │   ├── settings.py     # 配置类
│   │   └── constants.py    # 常量定义
│   ├── utils/              # 工具函数
│   │   ├── file_utils.py   # 文件操作工具
│   │   ├── text_utils.py   # 文本处理工具
│   │   └── validators.py   # 数据验证工具
│   └── cli/                # 命令行接口
│       └── commands.py     # CLI命令实现
├── config/                 # 配置文件
│   └── default.yaml        # 默认配置
├── tests/                  # 测试文件
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖列表
└── README.md              # 说明文档
```

## 🔧 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
```

### 类型检查

```bash
mypy src/
```

## 📈 功能对比

| 功能 | 原始版本 | 重构版本 |
|------|----------|----------|
| 模块化设计 | ❌ | ✅ |
| 配置文件支持 | ❌ | ✅ |
| 命令行界面 | 简单 | 丰富 |
| 错误处理 | 基础 | 完善 |
| 断点续传 | ❌ | ✅ |
| 多输出格式 | ❌ | ✅ |
| 扩展性 | 低 | 高 |
| 测试支持 | ❌ | ✅ |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ACL Anthology](https://aclanthology.org/) 提供的论文资源
- 原始版本的开发者

## 📞 联系

如有问题或建议，请提交 Issue 或联系：
- Email: your.email@example.com
- GitHub: https://github.com/yourusername/acl-anthology-downloader