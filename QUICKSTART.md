# 🚀 Multi-Tool Agent 快速开始指南

## 一键运行（推荐方法）

确保您已经安装了依赖和 Google ADK：

```bash
# 安装Google ADK
pip install google-adk

# 安装其他依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install
```

然后启动项目：

```bash
# 启动 ADK Web 开发界面
adk web
```

打开浏览器访问 `http://localhost:8000`，在左上角下拉菜单选择 `multi_tool_agent`

## 手动安装步骤

### 1. 检查 Python 版本

确保您的系统已安装 Python 3.8 或更高版本：

```bash
python --version  # Windows
python3 --version # Linux/Mac
```

### 2. 克隆或下载项目

```bash
git clone <your-repo-url>
cd multi-tool-agent
```

### 3. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 4. 安装依赖

```bash
# 自动安装所有依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install
```

### 5. 运行项目

```bash
python main.py
```

## 快速测试

启动后，您可以尝试以下命令：

### 基础功能测试

```
help                           # 查看帮助
examples                       # 查看示例
```

### 代码执行测试

```
请执行Python代码：print("Hello, Multi-Tool Agent!")
```

### 加密货币数据测试

```
查询比特币当前价格
```

### Google 搜索测试

```
搜索 "Python编程教程"
```

### 市场新闻测试

```
获取最新的5条市场新闻
```

### 网页抓取测试

```
抓取 https://httpbin.org/json 的内容
```

## 常见问题解决

### 问题 1：Google ADK 安装失败

```bash
# 确保网络连接正常，可能需要科学上网
pip install google-adk --upgrade
```

### 问题 2：Playwright 浏览器安装失败

```bash
# 重新安装 Playwright 浏览器
playwright install chromium
```

### 问题 3：CCXT 相关错误

```bash
# 重新安装 CCXT
pip uninstall ccxt
pip install ccxt
```

### 问题 4：权限错误（Linux/Mac）

```bash
# 确保脚本有执行权限
chmod +x start.sh
chmod +x install.py
```

### 问题 5：模块导入错误

```bash
# 检查是否在正确的虚拟环境中
which python  # Linux/Mac
where python  # Windows

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

## 调试模式

如果遇到问题，可以开启调试模式：

### 方法 1：环境变量

```bash
# Windows
set DEBUG=true
python main.py

# Linux/Mac
DEBUG=true python3 main.py
```

### 方法 2：修改 .env 文件

```
DEBUG=true
```

## 高级配置

### 配置交易所 API（可选）

编辑 `.env` 文件：

```
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
```

### 配置代理（可选）

```
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

## 性能优化建议

1. **使用虚拟环境**：避免依赖冲突
2. **定期更新依赖**：`pip install -r requirements.txt --upgrade`
3. **关闭不需要的功能**：如果不使用某些功能，可以注释相关代理
4. **监控内存使用**：处理大量数据时注意内存使用

## 获取帮助

- 📖 查看完整文档：`README.md`
- 💬 运行时帮助：输入 `help`
- 🌟 使用示例：输入 `examples`
- 🐛 报告问题：提交 GitHub Issue

---

🎉 **恭喜！您已成功设置 Multi-Tool Agent！**

现在您可以享受这个强大的多功能 AI 代理系统带来的便利了！
