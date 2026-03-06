# Git 使用指南

## 🚀 快速开始

这个项目已经初始化为Git仓库，`.gitignore` 文件已配置好。

### 检查当前状态

```bash
# 查看Git状态
git status

# 查看所有分支
git branch -a

# 查看最近的提交历史
git log --oneline -10
```

### 第一次提交

```bash
# 添加所有文件到暂存区
git add .

# 提交文件
git commit -m "Initial commit: Complete refactor with modular architecture and new features"
```

## 📋 .gitignore 说明

项目中包含了完整的 `.gitignore` 文件，会忽略以下内容：

### 🔒 永远忽略的文件
- **Python缓存文件**: `__pycache__/`, `*.pyc`
- **虚拟环境**: `venv/`, `env/`
- **IDE配置**: `.vscode/`, `.idea/`
- **系统文件**: `.DS_Store`, `Thumbs.db`

### 📄 用户生成的数据
- **下载的论文**: `papers/`, `downloads/`, `*.pdf`
- **配置文件**: `config/custom.yaml`, `.env`
- **临时文件**: `temp/`, `*.tmp`, `*.log`
- **测试输出**: `test_output/`, `test_results/`

### 🏗️ 构建产物
- **Python包**: `build/`, `dist/`, `*.egg-info/`
- **文档构建**: `docs/_build/`
- **测试覆盖率**: `.coverage`, `htmlcov/`

## 🔧 Git 工作流程

### 1. 开发新功能

```bash
# 创建新分支
git checkout -b feature/new-feature-name

# 开发过程中定期提交
git add .
git commit -m "Add new feature implementation"

# 功能完成
git checkout main
git merge feature/new-feature-name
git branch -d feature/new-feature-name
```

### 2. 修复Bug

```bash
# 创建bug修复分支
git checkout -b bugfix/issue-description

# 修复问题
git add .
git commit -m "Fix: description of the bug fix"

# 合并修复
git checkout main
git merge bugfix/issue-description
git branch -d bugfix/issue-description
```

### 3. 版本发布

```bash
# 创建发布分支
git checkout -b release/v2.1.0

# 更新版本号
# 编辑 setup.py 或 __init__.py 中的版本号

# 提交版本更新
git add .
git commit -m "Release version 2.1.0"

# 合并到主分支
git checkout main
git merge release/v2.1.0

# 创建标签
git tag -a v2.1.0 -m "Release version 2.1.0"

# 推送到远程
git push origin main
git push origin v2.1.0
```

## 📊 提交信息规范

使用有意义的提交信息：

```bash
# 功能添加
git commit -m "feat: Add single paper extraction feature"

# 修复Bug
git commit -m "fix: Resolve PDF download timeout issue"

# 文档更新
git commit -m "docs: Update README with new features"

# 代码重构
git commit -m "refactor: Improve error handling in scraper module"

# 测试相关
git commit -m "test: Add unit tests for paper extractor"

# 配置更改
git commit -m "config: Add new configuration options"
```

## 🔄 忽略文件检查

如果你想确认 `.gitignore` 是否正常工作：

```bash
# 检查被忽略的文件
git status --ignored

# 检查特定文件是否被忽略
git check-ignore papers/example.pdf

# 强制查看被忽略的文件
git ls-files --others --ignored --exclude-standard
```

## 🚨 重要注意事项

### ⚠️ 不要提交的文件
- **个人配置文件**: `config/custom.yaml`, `.env.local`
- **下载的论文**: `papers/` 目录下的所有PDF文件
- **API密钥或密码**: 任何包含敏感信息的文件
- **临时文件**: `*.tmp`, `*.log`, `cache/`

### ✅ 应该提交的文件
- **源代码**: `src/` 目录下的所有Python文件
- **配置模板**: `config/default.yaml`
- **文档**: `README.md`, `MIGRATION_GUIDE.md`
- **测试文件**: `test_*.py`, `tests/` 目录
- **项目配置**: `requirements.txt`, `setup.py`, `.gitignore`

## 🛠️ Git 配置建议

### 设置用户信息
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 设置默认分支名
```bash
git config --global init.defaultBranch main
```

### 设置常用别名
```bash
git config --global alias.st "status"
git config --global alias.co "checkout"
git config --global alias.br "branch"
git config --global alias.cm "commit -m"
git config --global alias.unstage "reset HEAD --"
```

## 🌐 远程仓库

### 添加远程仓库
```bash
# GitHub
git remote add origin https://github.com/yourusername/acl-anthology-downloader.git

# 或者其他Git服务
git remote add origin https://gitlab.com/yourusername/acl-anthology-downloader.git
```

### 推送到远程
```bash
# 首次推送
git push -u origin main

# 后续推送
git push origin main

# 推送所有分支和标签
git push --all
git push --tags
```

### 克隆到新位置
```bash
git clone https://github.com/yourusername/acl-anthology-downloader.git
cd acl-anthology-downloader
pip install -r requirements.txt
```

## 📝 项目特定的忽略规则

这个项目的 `.gitignore` 包含了一些特殊的规则：

```gitignore
# 下载的论文和论文数据
papers/
downloads/
*.pdf
*.PDF

# 用户配置文件
config/custom.yaml
config/user_settings.yaml

# 测试输出
test_papers/
sample_papers/
```

这意味着：
- ✅ 提交源代码和文档
- ✅ 提交默认配置文件
- ❌ 不提交下载的论文
- ❌ 不提交个人配置
- ❌ 不提交测试生成的数据

## 🔍 故障排除

### 如果意外提交了不应该提交的文件

```bash
# 从Git中删除文件但保留本地文件
git rm --cached papers/sensitive_file.pdf
git commit -m "Remove sensitive file from tracking"

# 添加到 .gitignore
echo "papers/sensitive_file.pdf" >> .gitignore
git add .gitignore
git commit -m "Add file to gitignore"
```

### 如果需要修改历史提交

```bash
# 警告：这会重写历史，仅在必要时使用
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch large_file.pdf' \
  --prune-empty --tag-name-filter cat -- --all
```

现在你的项目已经配置了完整的Git忽略规则，可以安全地进行版本控制了！