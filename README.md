# Multi-Tool Agent 项目

一个基于 Google ADK (Agent Development Kit) 的多功能代理系统，集成了代码执行、网页抓取、数据分析、Google 搜索、市场新闻获取和加密货币市场数据等多种功能。

## 🌟 项目亮点

- 🤖 **多个专业子代理**: 每个代理专精特定领域，协同工作完成复杂任务
- 🧠 **智能协调系统**: 自动选择最适合的代理处理不同类型的请求
- 💻 **代码执行环境**: 安全的 Python 沙箱，预装 30+常用库
- 🌐 **高级网页抓取**: Playwright 驱动，支持 JS 渲染和复杂交互
- 🔍 **智能搜索**: Google 搜索自动化，结构化结果提取
- 📰 **实时资讯**: 金融市场新闻和资讯实时获取
- 💰 **加密货币专家**: 5 大交易所实时数据，完整交易功能
- 📝 **AiScript 支持**: 专业的 AiScript 代码助手，MCP 服务器集成

## 🏗️ 项目架构

```
agents/
├── multi_tool_agent/               # 主要的多工具代理系统
│   ├── agent.py                   # 智能协调代理（主入口）
│   └── sub_agents/               # 专业子代理集合
│       ├── code_execution_agent.py     # Python代码执行专家
│       ├── web_scrapy_agent.py         # 网页抓取专家
│       ├── google_search_agent.py      # Google搜索专家
│       ├── market_news_agent.py        # 市场新闻分析师
│       ├── crypto_market_agent.py      # 加密货币市场数据分析师
│       └── crypto_trade_agent.py       # 加密货币交易执行师
├── aiscript_agent/               # AiScript代码助手
│   └── agent.py                  # AiScript专家代理
├── requirements.txt              # 项目依赖
├── QUICKSTART.md                # 快速开始指南
└── README.md                    # 本文档
```

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt
playwright install

# 2. 启动ADK Web界面
adk web
```

浏览器访问 `http://localhost:8000`，在左上角下拉菜单选择 `multi_tool_agent`

### 使用 ADK 命令行界面

```bash
# 直接在终端中与代理对话
adk run multi_tool_agent
```

### 💡 使用示例

在 Web UI 或命令行中，您可以尝试以下查询：

- **数据分析**: "请用 Python 分析一下最近 30 天的比特币价格趋势"
- **加密货币查询**: "请帮我查询一下比特币当前的价格"
- **市场新闻**: "请搜索一下最新的比特币相关新闻"
- **网页抓取**: "请帮我抓取 https://news.ycombinator.com 的内容"
- **Google 搜索**: "搜索 'Python 数据分析教程'"
- **代码执行**: "请执行以下 Python 代码：import pandas as pd; print(pd.**version**)"

## 各子代理功能说明

### 1. 代码执行代理 (code_execution_agent)

**功能**: 执行 Python 代码，支持数据分析和可视化

**预装库**:

- 基础库：os, sys, json, datetime, time, random, math, re
- 数据处理：pandas, numpy, statistics
- 网络请求：requests, curl_cffi
- 加密货币：ccxt
- 其他：collections, itertools, functools

**使用示例**:

```python
# 通过主代理调用
response = root_agent.send_message("""
请执行以下Python代码：
import pandas as pd
import numpy as np

data = np.random.randn(100)
df = pd.DataFrame(data, columns=['values'])
result = df.describe()
print(result)
""")
```

### 2. 网页抓取代理 (web_scrapy_agent)

**功能**: 使用 Playwright 进行高级网页抓取

**特性**:

- 支持 JavaScript 渲染的页面
- 提取页面内容、链接、表单信息
- 自动处理各种网页类型

**使用示例**:

```python
response = root_agent.send_message("请抓取 https://news.ycombinator.com 的内容")
```

### 3. Google 搜索代理 (google_search_agent)

**功能**: 自动化 Google 搜索并提取结构化结果

**特性**:

- 支持中英文搜索
- 提取标题、URL、描述
- 可选择性提取网页内容

**使用示例**:

```python
response = root_agent.send_message("请搜索 'Python数据分析教程'")
```

### 4. 市场新闻代理 (market_news_agent)

**功能**: 获取实时金融市场快讯

**特性**:

- 获取最新市场快讯
- 关键词搜索新闻
- 分页获取大量数据

**使用示例**:

```python
response = root_agent.send_message("请获取最新的10条市场新闻")
```

### 5. 加密货币市场代理 (crypto_market_agent)

**功能**: 获取多个交易所的实时加密货币市场数据

**支持的交易所**:

- Binance (币安)
- OKX (欧易)
- Bybit
- Bitget
- Gate.io

**主要功能**:

- 获取实时价格数据 (Ticker)
- 获取交易深度 (Order Book)
- 获取历史交易记录
- 获取 K 线数据 (OHLCV)
- 批量获取多个交易对数据
- 市场概览和统计

**使用示例**:

```python
# 获取比特币价格
response = root_agent.send_message("请查询 Binance 上 BTC/USDT 的当前价格")

# 获取K线数据并分析
response = root_agent.send_message("请获取比特币最近30天的日K线数据，并分析价格趋势")

# 获取多个币种的价格
response = root_agent.send_message("请查询 BTC、ETH、BNB 的当前价格")
```

### 6. AiScript 代理 (aiscript_agent)

**功能**: AiScript 代码助手，通过 MCP 服务器提供支持

**特性**:

- 连接到远程 MCP 服务器
- 提供 AiScript 编程支持

## 运行项目

### 方法 1：直接使用

```python
from multi_tool_agent.agent import root_agent

# 开始对话
while True:
    user_input = input("请输入您的问题: ")
    if user_input.lower() in ['quit', 'exit', '退出']:
        break

    try:
        response = root_agent.send_message(user_input)
        print(f"代理回复: {response}")
    except Exception as e:
        print(f"错误: {e}")
```

### 方法 2：创建运行脚本

创建 `main.py` 文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from multi_tool_agent.agent import root_agent

def main():
    print("=== Multi-Tool Agent 启动 ===")
    print("支持的功能：")
    print("1. 代码执行和数据分析")
    print("2. 网页抓取")
    print("3. Google搜索")
    print("4. 市场新闻获取")
    print("5. 加密货币市场数据")
    print("6. AiScript编程支持")
    print("\n输入 'quit' 或 'exit' 退出")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n请输入您的问题: ")
            if user_input.lower().strip() in ['quit', 'exit', '退出', 'q']:
                print("感谢使用！再见！")
                break

            if not user_input.strip():
                continue

            print("正在处理您的请求...")
            response = root_agent.send_message(user_input)
            print(f"\n代理回复: {response}")

        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print("请重试或检查您的输入")

if __name__ == "__main__":
    main()
```

然后运行：

```bash
python main.py
```

## 故障排除

### 常见问题

1. **Playwright 安装问题**:

   ```bash
   # 重新安装Playwright浏览器
   playwright install
   # 或指定特定浏览器
   playwright install chromium
   ```

2. **Google ADK 配置问题**:

   - 确保已正确安装 Google ADK
   - 检查 API 密钥和权限配置

3. **网络连接问题**:

   - 确保网络连接正常
   - 某些功能可能需要科学上网

4. **依赖版本冲突**:
   ```bash
   # 创建新的虚拟环境
   python -m venv fresh_env
   fresh_env\Scripts\activate  # Windows
   # 重新安装所有依赖
   ```

### 日志和调试

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如果您有任何问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件到 [您的邮箱]

## 更新日志

### v1.0.0

- 初始版本发布
- 集成 6 个专业代理
- 支持多种数据源和功能

# ADK 工具定义最佳实践指南

## 概述

在 Google ADK 中，工具是赋予智能体超越纯文本生成能力的构建块。它们通常是执行特定操作的常规 Python 函数，如调用 API、查询数据库或执行计算。

## 函数工具

将函数转换为工具是将自定义逻辑集成到你的智能体中的直接方式。实际上，当你将一个函数分配给智能体的 `tools` 列表时，框架会自动将其包装为函数工具。这种方式灵活且易于集成。

```python
# 示例：创建包含工具的智能体
agent = Agent(
    name="example_agent",
    model="gemini-2.5-flash-preview-05-20",
    tools=[get_weather, web_scrapy_playwright],  # 函数自动转换为工具
)
```

## 核心概念

### 文档字符串至关重要！

你的函数的 docstring（或上方注释）会作为工具的描述发送给 LLM。因此，编写良好且全面的 docstring 对于 LLM 有效理解工具至关重要。

智能体的 LLM 严重依赖函数的文档字符串来理解：

- **工具做什么** - 功能的清晰描述
- **何时使用它** - 使用场景和条件
- **它需要什么参数** - 参数类型、格式和约束
- **它返回什么信息** - 返回值的结构和含义

## 最佳实践

### 1. 参数设计原则

**使用 JSON 可序列化类型**：使用标准的 JSON 可序列化类型（例如，字符串、整数、列表、字典）定义你的函数参数。

**避免默认值**：重要的是避免为参数设置默认值，因为语言模型（LLM）目前不支持解释它们。

```python
# ✅ 推荐做法
def get_weather(city: str, include_forecast: bool) -> dict:
    """获取指定城市的天气信息。

    Args:
        city (str): 城市名称，例如 "Beijing", "New York"
        include_forecast (bool): 是否包含天气预报信息
    """

# ❌ 避免使用默认值
def get_weather(city: str, include_forecast: bool = False) -> dict:
    # LLM 无法理解默认值
```

### 2. 返回类型设计

**推荐字典类型**：函数工具的首选返回类型是 Python 中的字典。这允许你用键值对结构化响应，为 LLM 提供上下文和清晰度。

**包含 status 键**：作为最佳实践，在你的返回字典中包含一个 "status" 键来表示整体结果（如 "success"、"error"、"pending"），为 LLM 提供关于操作状态的明确信号。

**描述性返回值**：尽量让你的返回值具有描述性。例如，不要返回数字错误代码，而是返回带有 "error_message" 键的字典，包含人类可读的解释。

```python
# ✅ 推荐的返回格式
{
    "status": "success" | "error" | "pending",
    "data": {...},           # 成功时的具体数据
    "error_message": "...",  # 错误时的人类可读说明
    "metadata": {...}        # 可选的元信息
}

# 示例实现
def get_weather(city: str) -> dict:
    try:
        weather_data = fetch_weather_from_api(city)
        return {
            "status": "success",
            "data": {
                "temperature": weather_data["temp"],
                "condition": weather_data["weather"],
                "humidity": weather_data["humidity"]
            },
            "metadata": {
                "source": "OpenWeatherMap",
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"无法获取 {city} 的天气信息: {str(e)}"
        }
```

### 3. 编写清晰的文档字符串

文档字符串应该清楚说明函数的用途、参数含义和预期返回值：

```python
def get_weather(city: str) -> dict:
    """获取指定城市的当前天气报告。

    这个工具可以获取全球任意城市的实时天气信息，包括温度、湿度、天气状况等。
    适用于需要了解天气情况来做决策的场景。

    Args:
        city (str): 城市名称，支持中英文。
                   例如："北京"、"New York"、"London"、"Tokyo"

    Returns:
        dict: 包含天气信息的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含天气数据
                - temperature (float): 当前温度（摄氏度）
                - condition (str): 天气状况（如"晴天"、"多云"）
                - humidity (int): 湿度百分比
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息（数据源、时间戳等）

    示例:
        >>> result = get_weather("北京")
        >>> if result["status"] == "success":
        ...     print(f"北京当前温度: {result['data']['temperature']}°C")
    """
```

### 4. 记录工具执行

为了便于调试，在工具执行时添加日志记录：

```python
def get_weather(city: str) -> dict:
    # 记录工具调用
    print(f"--- Tool: get_weather called for city: {city} ---")

    # 工具逻辑...

    # 记录执行结果
    print(f"--- Weather query completed for {city} ---")
```

### 5. 输入标准化

对输入进行基本的标准化处理：

```python
def get_weather(city: str) -> dict:
    # 输入标准化
    city_normalized = city.strip().lower()

    # 输入验证
    if not city_normalized:
        return {
            "status": "error",
            "error_message": "城市名称不能为空"
        }
```

### 6. 优雅的错误处理

在工具内部处理潜在错误，确保始终返回有意义的响应：

```python
def get_weather(city: str) -> dict:
    try:
        # 主要逻辑
        return fetch_weather_data(city)
    except ConnectionError:
        return {
            "status": "error",
            "error_message": "网络连接失败，请检查网络连接后重试"
        }
    except ValueError as e:
        return {
            "status": "error",
            "error_message": f"无效的城市名称: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"获取天气信息时发生未知错误: {str(e)}"
        }
```

## 简单性原则

虽然你在定义函数方面有相当大的灵活性，但请记住，简单性增强了 LLM 的可用性。考虑这些指导原则：

### 1. 参数越少越好

尽量减少参数数量以降低复杂性：

```python
# ✅ 推荐：参数简洁
def get_weather(city: str) -> dict:
    """获取城市天气"""

# ❌ 避免：参数过多
def get_weather(city: str, country: str, units: str, lang: str,
                include_forecast: bool, forecast_days: int,
                include_historical: bool, api_key: str) -> dict:
    """参数过多，LLM 难以正确使用"""
```

### 2. 简单数据类型

尽量使用基础数据类型（如 str、int、bool、list、dict），避免自定义类：

```python
# ✅ 推荐：使用基础类型
def search_products(query: str, max_results: int) -> dict:
    """搜索产品"""

# ❌ 避免：复杂的自定义类型
def search_products(criteria: SearchCriteria, options: SearchOptions) -> ProductList:
    """LLM 无法理解自定义类型"""
```

### 3. 有意义的命名

函数名和参数名会极大影响 LLM 如何理解和使用工具。请选择能清晰反映函数用途和输入含义的名称：

```python
# ✅ 推荐：清晰的命名
def get_weather(city: str) -> dict:
    """获取天气信息"""

def search_news(keyword: str, max_articles: int) -> dict:
    """搜索新闻文章"""

def calculate_loan_payment(principal: float, interest_rate: float, years: int) -> dict:
    """计算贷款还款额"""

# ❌ 避免：模糊的命名
def do_stuff(data: str) -> dict:
    """功能不明确"""

def beAgent(input_val: str) -> dict:
    """命名毫无意义"""

def func1(x: str, y: int) -> dict:
    """参数名无法理解"""
```

## 工具开发流程

1. **定义功能** - 明确工具要解决的问题
2. **设计接口** - 确定参数和返回值结构（遵循简单性原则）
3. **选择合适的命名** - 使用清晰、描述性的函数名和参数名
4. **编写文档字符串** - 详细描述工具的用法、参数和返回值
5. **实现功能** - 编写核心逻辑
6. **添加输入验证** - 验证和标准化输入参数
7. **添加错误处理** - 确保工具的健壮性
8. **测试验证** - 验证工具在各种场景下的表现
9. **添加日志记录** - 便于调试和监控

## 示例：完整的工具实现

参考 `multi_tool_agent/sub_agents/web_scrapy_agent.py` 中的 `web_scrapy_playwright` 工具实现，它展示了：

- 清晰的函数命名和参数命名
- 详细的参数和返回值文档
- 输入验证和标准化
- 全面的错误处理
- 结构化的返回数据（包含 status 键）
- 调试日志记录
- 简洁的参数设计（只有一个必需参数）

## 注意事项

- **幂等性**：工具应该是幂等的（多次调用产生相同结果）
- **安全性**：避免在工具中直接打印用户敏感信息
- **性能**：确保工具的执行时间在合理范围内
- **可用性**：为复杂工具提供简单的使用示例
- **可维护性**：保持代码简洁，便于理解和维护
- **国际化**：考虑支持多语言输入和输出

## 框架自动处理

如果你的函数返回的不是字典类型，框架会自动将其包装为一个以 "result" 为键的字典：

```python
def simple_function() -> str:
    return "Hello World"

# 框架自动转换为:
# {"result": "Hello World"}
```

不过，为了更好的可控性和清晰度，建议始终返回字典类型。

# ADK 智能体定义最佳实践指南

## 概述

定义智能体是创建有效 ADK 应用程序的核心步骤。一个良好定义的智能体需要明确的身份、清晰的指令和合适的工具配置。

## 智能体身份和目的

### 1. name（必填）

每个智能体都需要一个唯一的字符串标识符。这个 `name` 对内部操作至关重要，尤其是在多智能体系统中，智能体需要相互引用或委派任务。

**最佳实践**：

- 选择能反映智能体功能的描述性名称
- 使用下划线分隔单词（如 `customer_support_router`、`billing_inquiry_agent`）
- 避免使用像 `user` 这样的保留名称
- 保持名称简洁但具有描述性

```python
# ✅ 推荐的命名
weather_agent = Agent(name="weather_agent")
customer_support_router = Agent(name="customer_support_router")
billing_inquiry_agent = Agent(name="billing_inquiry_agent")

# ❌ 避免的命名
agent1 = Agent(name="agent1")  # 无意义
user = Agent(name="user")      # 保留名称
helper = Agent(name="helper")  # 过于泛泛
```

### 2. description（可选，多智能体推荐）

提供一个简洁的智能体能力摘要。这个描述主要由其他 LLM 智能体用来确定是否应该将任务路由到这个智能体。

**最佳实践**：

- 使其足够具体以区分它与其他智能体
- 描述主要功能和适用场景
- 避免过于技术性的术语
- 保持简洁明了

```python
# ✅ 推荐的描述
description="专门进行网页内容抓取的智能体，使用 Playwright 技术获取网页文本、HTML、链接和表单信息。"

description="处理关于当前账单明细的查询，包括费用明细、付款状态和账单历史。"

# ❌ 避免的描述
description="账单智能体"  # 过于简单
description="使用复杂的 NLP 算法处理各种类型的查询请求"  # 过于技术性
```

### 3. model（必填）

指定将为此智能体的推理提供支持的底层 LLM。模型的选择会影响智能体的能力、成本和性能。

**常用模型**：

- `gemini-2.0-flash` - 高性能，适合复杂任务
- `gemini-2.5-flash-preview-05-20` - 预览版本，最新功能
- `gemini-1.5-pro` - 专业版，处理能力强

```python
# 示例：定义基本智能体身份
capital_agent = Agent(
    model="gemini-2.0-flash",
    name="capital_agent",
    description="回答用户关于某个国家首都的问题。"
)
```

## 指令（instruction）设计

`instruction` 参数可以说是塑造智能体行为最关键的部分。它告诉智能体：

- **核心任务或目标** - 智能体的主要职责
- **个性或角色** - 如何与用户交互
- **行为约束** - 什么可以做，什么不能做
- **工具使用指导** - 何时以及如何使用工具
- **输出格式期望** - 回复的格式和结构

### 有效指令的技巧

#### 1. 清晰明确

避免含糊不清，清楚地说明期望的行动和结果：

```python
# ✅ 清晰明确
instruction="""
你是一个专业的网页抓取助手。当用户提供 URL 时：
1. 使用 web_scrapy_playwright 工具抓取网页内容
2. 分析页面的主要信息（标题、内容摘要、链接数量）
3. 以结构化的方式回复用户
"""

# ❌ 含糊不清
instruction="你是一个助手，帮助用户处理网页相关的事情"
```

#### 2. 使用 Markdown 格式

使用标题、列表等提高复杂指令的可读性：

```python
instruction="""
# 加密货币市场分析助手

你是一个专业的加密货币市场数据分析师。

## 主要职责
- 获取实时加密货币价格数据
- 分析市场趋势和价格变化
- 提供数据驱动的市场洞察

## 工具使用指南
- **get_crypto_price**: 获取特定币种的实时价格
- **get_market_data**: 获取市场概览和统计信息
- **analyze_trends**: 分析价格趋势和技术指标

## 回复格式
请始终以结构化的方式回复，包含：
1. 数据摘要
2. 关键洞察
3. 风险提示（如适用）
"""
```

#### 3. 提供示例（少样本学习）

对于复杂任务或特定输出格式，直接在指令中包含示例：

```python
instruction="""
你是一个国家首都查询助手。

当用户询问某个国家的首都时：
1. 从用户的提问中识别国家名称
2. 使用 get_capital_city 工具查找首都
3. 明确地回复用户，说明该国家的首都

## 示例交互

用户："法国的首都是什么？"
助手："法国的首都是巴黎（Paris）。"

用户："What's the capital of Japan?"
助手："日本的首都是东京（Tokyo）。"
"""
```

#### 4. 指导工具使用

不仅仅是列出工具，解释智能体何时和为什么应该使用它们：

```python
instruction="""
你是一个多功能数据分析助手。

## 工具使用策略

### 代码执行工具 (execute_python_code)
- **何时使用**: 需要进行数据计算、统计分析或生成图表时
- **如何使用**: 编写清晰的 Python 代码，使用预装的库（pandas, numpy 等）
- **注意事项**: 确保代码安全，避免文件系统操作

### 网页抓取工具 (web_scrapy_playwright)
- **何时使用**: 需要获取网页内容、分析网站结构时
- **如何使用**: 提供完整的 URL，包含协议（http/https）
- **注意事项**: 尊重网站的使用条款，避免过度请求

### 搜索工具 (google_search)
- **何时使用**: 需要获取最新信息或查找特定内容时
- **如何使用**: 构造有效的搜索关键词
- **注意事项**: 验证搜索结果的可靠性
"""
```

## 状态和模板变量

指令支持模板语法，可以插入动态值：

### 基本语法

- `{var}` - 插入名为 `var` 的状态变量的值
- `{artifact.var}` - 插入名为 `var` 的人工制品的文本内容
- `{var?}` - 可选变量，如果不存在则忽略错误

### 使用示例

```python
instruction="""
你是 {company_name} 的客户服务助手。

## 当前配置
- 服务时间: {service_hours?}
- 当前用户: {user_name?}
- 会话 ID: {session_id}

## 上下文信息
{artifact.customer_history?}

请根据以上信息为用户提供个性化的服务。
"""
```

## 完整的智能体定义示例

### 单一功能智能体

```python
weather_agent = Agent(
    name="weather_agent",
    model="gemini-2.0-flash",
    description="提供准确的天气信息查询服务，支持全球主要城市的实时天气数据。",
    instruction="""
    # 天气查询助手

    你是一个专业的天气信息助手，致力于为用户提供准确、及时的天气信息。

    ## 主要功能
    - 查询指定城市的当前天气
    - 提供详细的天气状况描述
    - 给出适当的生活建议

    ## 工具使用
    当用户询问天气时，使用 `get_weather` 工具：
    1. 识别用户提到的城市名称
    2. 调用工具获取天气数据
    3. 以友好的方式回复用户

    ## 回复格式
    - 明确说明城市和天气状况
    - 包含温度、湿度等关键信息
    - 提供相关的穿衣或出行建议
    """,
    tools=[get_weather]
)
```

### 多功能协调智能体

```python
root_agent = Agent(
    name="multi_tool_coordinator",
    model="gemini-2.0-flash",
    description="多功能智能体协调器，能够处理代码执行、网页抓取、搜索查询等多种任务。",
    instruction="""
    # 多功能智能助手

    你是一个全能的智能助手，可以协调使用多种专业工具来完成用户的请求。

    ## 核心能力
    - 🔍 信息搜索和网页抓取
    - 💻 代码执行和数据分析
    - 📊 市场数据和新闻获取
    - 💰 加密货币信息查询

    ## 任务处理流程
    1. **理解用户需求**: 仔细分析用户的问题和期望
    2. **选择合适工具**: 根据任务性质选择最适合的工具
    3. **执行任务**: 调用相应工具并获取结果
    4. **整合回复**: 将结果整理成清晰、有用的回复

    ## 工具选择指南

    ### 网页抓取 (web_scrapy_playwright)
    - 用户提供 URL 需要获取内容时
    - 需要分析网页结构和信息时

    ### 代码执行 (execute_python_code)
    - 需要数据计算、统计分析时
    - 用户要求执行代码或生成图表时

    ### 搜索查询 (google_search)
    - 需要最新信息或不确定信息时
    - 用户明确要求搜索时

    ### 市场数据工具
    - 询问股票、加密货币价格时
    - 需要金融市场分析时

    ## 回复原则
    - 始终以用户友好的方式回复
    - 提供准确、有用的信息
    - 在必要时解释数据来源和局限性
    - 对于复杂结果，提供清晰的总结
    """,
    tools=[
        web_scrapy_playwright,
        execute_python_code,
        google_search,
        get_crypto_price,
        get_market_news
    ]
)
```

## 智能体定义检查清单

在创建智能体时，请确保：

- [ ] **name** 是唯一的、描述性的
- [ ] **model** 适合预期的任务复杂度
- [ ] **description** 清楚地说明智能体的用途（多智能体系统中）
- [ ] **instruction** 包含明确的任务定义
- [ ] **instruction** 解释了何时使用每个工具
- [ ] **instruction** 指定了期望的输出格式
- [ ] **tools** 列表包含所有必要的工具函数
- [ ] 指令使用了清晰的 Markdown 格式
- [ ] 提供了具体的使用示例（如适用）

## 常见错误和解决方案

### 错误 1：指令过于简单

```python
# ❌ 错误
instruction="你是一个助手"

# ✅ 正确
instruction="""
你是一个专业的客户服务助手，专门处理产品咨询和技术支持问题。

当用户询问产品信息时，使用产品数据库工具查询详细信息。
当用户报告技术问题时，引导用户进行故障排除步骤。
始终保持友好、专业的语调。
"""
```

### 错误 2：工具使用指导不明确

```python
# ❌ 错误
instruction="你有一些工具可以使用"

# ✅ 正确
instruction="""
## 工具使用指南

### search_tool
- 用途：搜索最新信息
- 使用时机：用户询问当前事件或需要验证信息时
- 注意：搜索结果可能需要进一步验证

### calculate_tool
- 用途：执行数学计算
- 使用时机：用户需要计算数值或分析数据时
- 注意：对于复杂计算，解释计算过程
"""
```

### 错误 3：缺少输出格式说明

```python
# ❌ 错误
instruction="回答用户问题"

# ✅ 正确
instruction="""
## 回复格式要求

对于天气查询，请按以下格式回复：
**城市**: [城市名称]
**天气**: [天气状况]
**温度**: [当前温度]
**建议**: [穿衣或出行建议]
"""
```

通过遵循这些最佳实践，你可以创建出功能强大、行为可预测的智能体，为用户提供优质的服务体验。
