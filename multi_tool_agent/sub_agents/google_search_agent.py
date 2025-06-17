import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from google.adk.agents import Agent
import time
import curl_cffi
import os
from bs4 import BeautifulSoup


def _playwright_google_search_internal(query: str, num_results: int, lang: str) -> dict:
    """在独立线程中运行的 Playwright Google 搜索内部函数"""
    from patchright.sync_api import sync_playwright
    
    result = {
        "status": "success",
        "query": query,
        "results": [],
        "total_results": 0,
        "search_url": "",
        "search_stats": "",
        "timestamp": datetime.now().isoformat()
    }
    
    with sync_playwright() as p:
        import os
        # 获取代理设置
        http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
        proxy_url = https_proxy or http_proxy
        
        # 启动浏览器时配置代理
        browser = p.chromium.launch(
            headless=True,
            proxy={
                "server": proxy_url
            } if proxy_url else None
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale=lang
        )
        page = context.new_page()
        
        try:
            page.set_default_timeout(30000)  # 30秒
            
            # 构建 Google 搜索 URL
            encoded_query = urllib.parse.quote_plus(query)
            google_url = f"https://www.google.com/search?q={encoded_query}&hl={lang}&num={num_results}"
            result["search_url"] = google_url
            
            # 访问 Google 搜索页面
            page.goto(google_url, wait_until="domcontentloaded")
            
            # 检查是否有验证码或其他阻塞
            if page.locator('div:has-text("检测到异常流量")').count() > 0 or \
               page.locator('div:has-text("unusual traffic")').count() > 0:
                result["status"] = "error"
                result["error_message"] = "Google 检测到异常流量，请稍后再试"
                return result
            
            # 解析搜索结果
            search_results = []
            result_containers = page.locator('div[data-ved]').all()
            
            for container in result_containers:
                try:
                    title_element = container.locator('h3').first
                    link_element = container.locator('a[href^="http"]').first
                    
                    if title_element.count() > 0 and link_element.count() > 0:
                        title = title_element.inner_text().strip()
                        url = link_element.get_attribute('href')
                        
                        # 获取描述
                        description = ""
                        desc_selectors = [
                            'div[data-sncf="1"]',
                            'div[style*="-webkit-line-clamp"]',
                            'span[style*="-webkit-line-clamp"]',
                            '.VwiC3b'
                        ]
                        
                        for selector in desc_selectors:
                            desc_element = container.locator(selector).first
                            if desc_element.count() > 0:
                                description = desc_element.inner_text().strip()
                                break
                        # 获取显示的 URL
                        displayed_url = ""
                        url_selectors = ['cite', 'span[style*="color"]', '.UdQCqe']
                        
                        for selector in url_selectors:
                            url_element = container.locator(selector).first
                            if url_element.count() > 0:
                                displayed_url = url_element.inner_text().strip()
                                break
                        
                        if title and url:
                            # 检查URL是否已存在
                            url_exists = any(result["url"] == url for result in search_results)
                            if not url_exists:
                                search_results.append({
                                    "title": title,
                                    "url": url,
                                    "displayed_url": displayed_url,
                                    "description": description,
                                    "position": len(search_results) + 1
                                })
                        
                        if len(search_results) >= num_results:
                            break
                            
                except Exception:
                    continue
            
            result["results"] = search_results
            result["total_results"] = len(search_results)
            
            # 获取搜索统计信息
            try:
                stats_element = page.locator('#result-stats').first
                if stats_element.count() > 0:
                    result["search_stats"] = stats_element.inner_text()
            except Exception:
                result["search_stats"] = ""
            
        except Exception as e:
            result["status"] = "error"
            result["error_message"] = f"搜索过程中出错: {str(e)}"
        
        finally:
            context.close()
            browser.close()
    
    return result

def google_search_playwright(query: str, num_results: int, lang: str) -> dict:
    """使用 Playwright 进行 Google 搜索。
    
    这个工具使用 Playwright 浏览器自动化技术来执行 Google 搜索，
    可以获取搜索结果的标题、URL、描述等信息。适用于需要获取
    最新搜索结果或绕过 API 限制的场景。
    
    Args:
        query (str): 搜索关键词，不能为空。例如："Python 编程教程"
        num_results (int): 期望返回的结果数量，范围 1-100。例如：10
        lang (str): 搜索语言代码。例如："zh-CN"（中文）、"en"（英文）
    
    Returns:
        dict: 搜索结果字典
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含搜索结果数据
                - query (str): 搜索关键词
                - results (list): 搜索结果列表，每个结果包含：
                    - title (str): 网页标题
                    - url (str): 网页链接
                    - displayed_url (str): 显示的URL
                    - description (str): 网页描述
                    - position (int): 结果位置
                - total_results (int): 实际返回的结果数量
                - search_url (str): 搜索页面URL
                - search_stats (str): 搜索统计信息
            - error_message (str): 错误时的说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = google_search_playwright("Python 教程", 5, "zh-CN")
        >>> if result["status"] == "success":
        ...     for item in result["data"]["results"]:
        ...         print(f"{item['title']}: {item['url']}")
    """
    print(f"--- Tool: google_search_playwright called with query='{query}', num_results={num_results}, lang='{lang}' ---")
    
    # 输入验证
    if not query or not query.strip():
        return {
            "status": "error",
            "error_message": "搜索关键词不能为空"
        }
    
    if not isinstance(num_results, int) or num_results < 1 or num_results > 100:
        return {
            "status": "error",
            "error_message": "结果数量必须是 1-100 之间的整数"
        }
    
    if not lang or not lang.strip():
        return {
            "status": "error",
            "error_message": "语言代码不能为空"
        }
    
    # 标准化输入
    query_normalized = query.strip()
    lang_normalized = lang.strip()
    
    try:
        # 检查 Playwright 是否已安装
        try:
            from patchright.sync_api import sync_playwright
        except ImportError:
            return {
                "status": "error",
                "error_message": "Playwright 未安装。请运行: pip install patchright && patchright install"
            }
        
        # 使用线程池执行搜索
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                future = executor.submit(_playwright_google_search_internal, query_normalized, num_results, lang_normalized)
                search_result = future.result(timeout=60)
                
                if search_result["status"] == "success":
                    print(f"--- Tool: google_search_playwright completed successfully, found {search_result['total_results']} results ---")
                    return {
                        "status": "success",
                        "data": search_result,
                        "metadata": {
                            "timestamp": datetime.now().isoformat(),
                            "processed_query": query_normalized,
                            "search_language": lang_normalized,
                            "requested_results": num_results
                        }
                    }
                else:
                    error_msg = search_result.get("error_message", "搜索失败")
                    print(f"--- Tool: google_search_playwright failed - {error_msg} ---")
                    return {
                        "status": "error",
                        "error_message": error_msg
                    }
                
            except FutureTimeoutError:
                error_msg = "搜索超时（60秒）"
                print(f"--- Tool: google_search_playwright failed - {error_msg} ---")
                return {
                    "status": "error",
                    "error_message": error_msg
                }
            except Exception as e:
                error_msg = f"线程执行错误: {str(e)}"
                print(f"--- Tool: google_search_playwright failed - {error_msg} ---")
                return {
                    "status": "error",
                    "error_message": error_msg
                }
        
    except Exception as e:
        error_msg = f"搜索失败: {str(e)}"
        print(f"--- Tool: google_search_playwright failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

def search_and_extract_content(query: str, num_results: int=10) -> dict:
    """搜索并提取网页内容。
    
    这个工具首先执行 Google 搜索，然后对每个搜索结果进行网页内容提取，
    返回包含完整内容的搜索结果。适用于需要深入分析搜索结果内容的场景。
    
    Args:
        query (str): 搜索关键词，不能为空。例如："人工智能发展趋势"
        num_results (int): 搜索结果数量，范围 1-10（内容提取较耗时）。例如：3
    
    Returns:
        dict: 搜索和内容提取结果
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含增强的搜索结果
                - query (str): 搜索关键词
                - results (list): 增强的搜索结果列表，每个结果包含：
                    - title (str): 网页标题
                    - url (str): 网页链接
                    - description (str): 搜索结果描述
                    - content (str): 提取的网页内容（前2000字符）
                    - page_title (str): 网页实际标题
                    - content_available (bool): 内容是否成功提取
                    - content_error (str): 内容提取失败时的错误信息
                - total_results (int): 结果数量
                - content_extracted (bool): 是否进行了内容提取
            - error_message (str): 错误时的说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = search_and_extract_content("机器学习算法", 3)
        >>> if result["status"] == "success":
        ...     for item in result["data"]["results"]:
        ...         if item["content_available"]:
        ...             print(f"{item['title']}: {item['content'][:100]}...")
    """
    print(f"--- Tool: search_and_extract_content called with query='{query}', num_results={num_results} ---")
    
    # 输入验证
    if not query or not query.strip():
        return {
            "status": "error",
            "error_message": "搜索关键词不能为空"
        }
    
    if not isinstance(num_results, int) or num_results < 1 or num_results > 10:
        return {
            "status": "error",
            "error_message": "结果数量必须是 1-10 之间的整数（内容提取较耗时）"
        }
    
    query_normalized = query.strip()
    
    try:
        # # 先进行搜索
        search_result = google_search_playwright(query_normalized, num_results, "zh-CN")
        
        if search_result["status"] != "success":
            return search_result
        
        # 导入网页抓取工具
        try:
            # 修复导入错误问题
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from multi_tool_agent.sub_agents.web_scrapy_agent import web_scrapy_playwright
        except ImportError:
            return {
                "status": "error",
                "error_message": "网页抓取工具不可用，请检查 web_scrapy_agent 模块"
            }
        
        # 对每个搜索结果进行内容提取
        enhanced_results = []
        search_data = search_result["data"]
        
        for result in search_data["results"]:
            enhanced_result = result.copy()
            
            try:
                # 抓取网页内容
                # scrapy_result = web_scrapy_playwright(result["url"])
                # 改用 requests 直接请求网站内容
                # 获取代理设置
                http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
                https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
                proxy_url = https_proxy or http_proxy
                response = curl_cffi.get(result['url'], impersonate='chrome', timeout=30, proxies={"http": proxy_url, "https": proxy_url})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取页面标题
                title = soup.title.string if soup.title else ""
                
                # 提取主要内容
                content = ""
                # 尝试获取主要内容区域
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main', 'article'])
                if main_content:
                    content = main_content.get_text(strip=True)
                else:
                    # 如果没有找到主要内容区域，获取所有段落文本
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                # 限制内容长度
                # content = content[:5000] if len(content) > 5000 else content
                
                enhanced_result["content"] = content
                enhanced_result["page_title"] = title
                enhanced_result["content_available"] = True
                    
            except Exception as e:
                enhanced_result["content"] = ""
                enhanced_result["content_available"] = False
                enhanced_result["content_error"] = f"内容提取失败: {str(e)}"
            
            enhanced_results.append(enhanced_result)
        
        # 更新搜索结果
        search_data["results"] = enhanced_results
        search_data["content_extracted"] = True
        
        print(f"--- Tool: search_and_extract_content completed successfully, extracted content for {len(enhanced_results)} results ---")
        
        return {
            "status": "success",
            "data": search_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processed_query": query_normalized,
                "content_extraction_performed": True,
                "results_with_content": sum(1 for r in enhanced_results if r["content_available"])
            }
        }
        
    except Exception as e:
        error_msg = f"搜索和内容提取失败: {str(e)}"
        print(f"--- Tool: search_and_extract_content failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

def quick_google_search(query: str) -> dict:
    """快速 Google 搜索（返回前10个结果）。
    
    这是一个简化的搜索工具，使用默认参数快速获取搜索结果。
    适用于需要快速获取少量搜索结果的场景。
    
    Args:
        query (str): 搜索关键词，不能为空。例如："今日新闻"
    
    Returns:
        dict: 搜索结果字典
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含搜索结果数据（结构同 google_search_playwright）
            - error_message (str): 错误时的说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = quick_google_search("Python 最新版本")
        >>> if result["status"] == "success":
        ...     print(f"找到 {result['data']['total_results']} 个结果")
    """
    print(f"--- Tool: quick_google_search called with query='{query}' ---")
    
    # 输入验证
    if not query or not query.strip():
        return {
            "status": "error",
            "error_message": "搜索关键词不能为空"
        }
    
    try:
        # 使用默认参数调用完整搜索功能
        result = google_search_playwright(query.strip(), 10, "zh-CN")
        
        if result["status"] == "success":
            print(f"--- Tool: quick_google_search completed successfully ---")
            # 更新元数据以标识这是快速搜索
            result["metadata"]["search_type"] = "quick_search"
            result["metadata"]["default_params_used"] = True
        else:
            print(f"--- Tool: quick_google_search failed ---")
        
        return result
        
    except Exception as e:
        error_msg = f"快速搜索失败: {str(e)}"
        print(f"--- Tool: quick_google_search failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

google_search_agent = Agent(
    name="google_search_agent",
    model="gemini-2.5-flash-preview-05-20",
    description=(
        "专业的 Google 搜索智能体，使用 Playwright 浏览器自动化技术执行搜索。"
        "能够获取实时搜索结果、提取网页内容，并提供结构化的搜索数据。"
        "支持多种搜索模式：标准搜索、快速搜索、搜索+内容提取。"
    ),
    instruction=(
        "你是一个专业的搜索助手，能够帮助用户进行 Google 搜索并获取相关信息。"
        "你有以下三个主要工具：\n"
        "1. quick_google_search - 快速搜索，返回前10个中文结果\n"
        "2. google_search_playwright - 完整的 Google 搜索，可自定义结果数量和语言\n"
        "3. search_and_extract_content - 可以优先使用，google搜索并提取每个结果的网页内容（很方便，可以深入分析每一个 url内容）\n\n"
        "使用指南：\n"
        "- 对于一般搜索需求，使用 quick_google_search\n"
        "- 需要大量结果或特定语言时，使用 google_search_playwright\n"
        "- （可以优先使用）需要深入分析网页内容时，使用 search_and_extract_content\n"
        "- 始终提供准确、相关的搜索结果\n"
        "- 如果搜索失败，解释原因并建议替代方案"
    ),
    tools=[quick_google_search, google_search_playwright, search_and_extract_content],
)


if __name__ == "__main__":
    result = search_and_extract_content("Python 教程", 10)
    print(result)