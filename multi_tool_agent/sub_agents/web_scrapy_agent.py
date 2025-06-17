import datetime
import sys
import io
import contextlib
import re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from google.adk.agents import Agent

def _playwright_scraper(url: str) -> dict:
    """在独立线程中运行的 Playwright 爬虫函数"""
    from patchright.sync_api import sync_playwright
    import time
    
    result = {
        "status": "success",
        "url": url,
        "content": "",
        "title": "",
        "meta_data": {},
        "links": [],
        "error": None
    }
    
    with sync_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            # 启动浏览器（使用 Chromium）
            import os
            # 获取代理设置
            http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
            https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
            proxy_url = https_proxy or http_proxy
            
            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": proxy_url
                } if proxy_url else None
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # 设置超时时间
            page.set_default_timeout(30000)  # 30秒
            
            # 访问页面
            response = page.goto(url, wait_until="domcontentloaded")
            
            # 等待页面加载完成
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            
            # 获取页面标题
            result["title"] = page.title()
            
            # 获取页面文本内容
            result["content"] = page.inner_text("body")
            
            # 获取页面HTML内容
            # result["html"] = page.content()
            
            # 获取元数据
            result["meta_data"] = {
                "status_code": response.status if response else None,
                "url": page.url,
                "title": result["title"],
                "viewport": page.viewport_size,
                "timestamp": time.time()
            }
            
            # 获取所有链接
            try:
                # 使用evaluate_all一次性获取所有链接信息，减少DOM操作
                links_data = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                        href: a.href,
                        text: a.innerText.trim().slice(0, 100)
                    }));
                }""")
                
                result["links"] = []
                for link_data in links_data:
                    try:
                        href = link_data["href"]
                        text = link_data["text"]
                        
                        # 验证URL是否有效
                        parsed = urlparse(href)
                        if parsed.scheme and parsed.netloc:
                            result["links"].append({
                                "url": href,
                                "text": text
                            })
                    except Exception:
                        continue
            except Exception:
                result["links"] = []
            
            # # 获取表单信息
            # try:
            #     forms = page.locator("form").all()
            #     result["forms"] = []
            #     for form in forms:
            #         try:
            #             action = form.get_attribute("action") or ""
            #             method = form.get_attribute("method") or "GET"
            #             inputs = form.locator("input, select, textarea").all()
            #             form_inputs = []
            #             for inp in inputs:
            #                 try:
            #                     input_type = inp.get_attribute("type") or "text"
            #                     name = inp.get_attribute("name") or ""
            #                     if name:
            #                         form_inputs.append({
            #                             "name": name,
            #                             "type": input_type
            #                         })
            #                 except Exception:
            #                     continue
                        
            #             result["forms"].append({
            #                 "action": action,
            #                 "method": method.upper(),
            #                 "inputs": form_inputs
            #             })
            #         except Exception:
            #             continue
            # except Exception:
            #     result["forms"] = []
            
        except Exception as e:
            result["error"] = f"页面加载错误: {str(e)}"
            result["status"] = "error"
        
        finally:
            # 清理资源
            try:
                if context:
                    context.close()
                if browser:
                    browser.close()
            except Exception:
                pass  # 忽略清理时的错误
    
    return result

def web_scrapy_playwright(url: str) -> dict:
    """使用 Playwright 进行网页内容抓取。

    这个工具可以抓取网页的文本内容、HTML、链接、表单等信息。
    适用于需要获取网页内容进行分析、提取信息或监控网站变化的场景。

    Args:
        url (str): 要抓取的网页 URL。必须是有效的 HTTP/HTTPS URL。
                  例如："https://example.com"、"http://localhost:3000"

    Returns:
        dict: 包含抓取结果的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含页面数据
                - url (str): 实际访问的 URL
                - content (str): 页面的纯文本内容
                - title (str): 页面标题
                - links (list): 页面中的链接列表，每个链接包含 'url' 和 'text'
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含状态码、时间戳、视口大小等

    示例:
        >>> result = web_scrapy_playwright("https://example.com")
        >>> if result["status"] == "success":
        ...     print(f"页面标题: {result['data']['title']}")
        ...     print(f"链接数量: {len(result['data']['links'])}")
    """
    # 记录工具调用
    print(f"--- Tool: web_scrapy_playwright called with url={url} ---")
    
    # 输入验证和标准化
    if not url or not url.strip():
        return {
            "status": "error",
            "error_message": "URL 不能为空"
        }
    
    # 标准化 URL - 添加协议如果缺失
    url_normalized = url.strip()
    if not url_normalized.startswith(('http://', 'https://')):
        url_normalized = 'https://' + url_normalized
    
    # 验证 URL 格式
    try:
        parsed = urlparse(url_normalized)
        if not parsed.netloc:
            return {
                "status": "error",
                "error_message": f"无效的 URL 格式: {url}"
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"URL 解析错误: {str(e)}"
        }
    
    print(f"--- Tool: web_scrapy_playwright normalized URL to: {url_normalized} ---")
    
    try:
        # 检查 Playwright 是否已安装
        try:
            from patchright.sync_api import sync_playwright
        except ImportError:
            return {
                "status": "error",
                "error_message": "Playwright 未安装。请运行: pip install playwright && playwright install"
            }
        
        # 使用 ThreadPoolExecutor 在新线程中运行 Playwright 同步代码
        # 这样可以避免与现有的 asyncio 事件循环冲突
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                print(f"--- Tool: web_scrapy_playwright starting page scraping ---")
                # 提交任务到线程池，设置超时时间为 60 秒
                future = executor.submit(_playwright_scraper, url_normalized)
                scraper_result = future.result(timeout=60)
                
                # 处理爬虫结果
                if scraper_result["status"] == "error":
                    print(f"--- Tool: web_scrapy_playwright failed - {scraper_result.get('error', '未知错误')} ---")
                    return {
                        "status": "error",
                        "error_message": scraper_result.get("error", "爬取过程中发生未知错误")
                    }
                
                # 构建成功响应
                page_data = {
                    "url": scraper_result["url"],
                    "content": scraper_result["content"],
                    "title": scraper_result["title"],
                    "links": scraper_result.get("links", []),
                }
                
                metadata = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "links_count": len(page_data["links"]),
                    "content_length": len(page_data["content"])
                }
                
                if "meta_data" in scraper_result:
                    metadata.update(scraper_result["meta_data"])
                
                # 记录成功结果
                print(f"--- Tool: web_scrapy_playwright completed successfully - title='{page_data['title'][:50]}...' links={len(page_data['links'])} ---")
                
                return {
                    "status": "success",
                    "data": page_data,
                    "metadata": metadata
                }
                
            except FutureTimeoutError:
                error_msg = "页面抓取超时（60秒）"
                print(f"--- Tool: web_scrapy_playwright failed - {error_msg} ---")
                return {
                    "status": "error",
                    "error_message": error_msg
                }
            except Exception as e:
                error_msg = f"线程执行错误: {str(e)}"
                print(f"--- Tool: web_scrapy_playwright failed - {error_msg} ---")
                return {
                    "status": "error",
                    "error_message": error_msg
                }
        
    except Exception as e:
        # 优雅的错误处理
        error_msg = f"抓取网页时发生未知错误: {str(e)}"
        print(f"--- Tool: web_scrapy_playwright failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }


web_scrapy_agent = Agent(
    name="web_scrapy_agent",
    model="gemini-2.5-flash-preview-05-20",
    description=(
        "专业的网页内容抓取智能体，使用 Playwright 技术安全高效地获取网页文本、HTML、链接和表单信息。"
        "支持现代网页的动态内容加载，能够处理JavaScript渲染的页面。"
    ),
    instruction=(
        "你是一个专业的网页抓取助手，擅长使用 Playwright 技术获取网页内容。"
        "工作流程："
        "1. 当用户请求抓取网页时，使用 web_scrapy_playwright 工具"
        "2. 仔细检查工具返回的 status 字段"
        "3. 如果成功（status='success'），分析 data 字段中的内容并提供有用的总结"
        "4. 如果失败（status='error'），解释 error_message 并建议解决方案"
        "5. 重点关注页面标题、主要内容、重要链接和表单信息"
        "6. 为用户提供清晰、结构化的内容摘要"
        
        "注意事项："
        "- 如果抓取失败，提供具体的错误原因和建议"
        "- 总结时突出最有价值的信息"
    ),
    tools=[web_scrapy_playwright],
)


if __name__ == "__main__":
    result = web_scrapy_playwright("https://github.com/farcasterxyz/protocol/blob/main/docs/SPECIFICATION.md")
    print(result)