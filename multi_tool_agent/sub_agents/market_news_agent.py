import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from curl_cffi import requests as cffi_requests
from google.adk.agents import Agent

# 设置日志
logger = logging.getLogger(__name__)

def get_market_data(last_id: str = '') -> List[Dict[str, Any]]:
    """获取最新的市场快讯数据
    
    Args:
        last_id (str): 上一次获取数据的最后一个ID，用于分页获取
    
    Returns:
        List[Dict[str, Any]]: 市场快讯数据列表
    """
    if last_id is None:
        last_id = ''
    
    params = {
        "type": "1",
        "lan": "cn",
        "userid": "",
        "lastid": last_id,
        "pagesize": 1000,
        "version": "v1"
    }
    
    headers = {
        'user-agent': 'AICoin_Test/2.5.54 (android SDK 31; OnePlus/900 screenSize/1080x2208 density/3.0 isStoreRelease/false)',
        'content-type': 'application/json; charset=utf-8',
        'accept-encoding': 'gzip',
        'host': 'api-test.aicoin.com'
    }
    
    while True:
        try:
            res = requests.post(
                'https://129.226.222.113/v3/hotFlash/getNewsFlashList', 
                json=params, 
                timeout=10,
                proxies=None, 
                verify=False, 
                headers=headers
            )
            data = res.json()
            break
        except Exception as e:
            logger.warning(f'获取市场数据失败，正在重试: {str(e)}')
            time.sleep(5)
    
    return data['data']['tbody']

def get_latest_market_news(limit: int) -> dict:
    """获取最新的市场快讯，限制返回数量。

    从AiCoin获取最新的市场快讯数据，支持限制返回数量。
    适用于获取最新市场动态、实时资讯更新的场景。

    Args:
        limit (int): 限制返回的快讯数量，建议范围1-1000

    Returns:
        dict: 包含快讯数据的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含快讯数据
                - news (list): 快讯列表
                - count_info (dict): 数量统计信息
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含获取时间等

    示例:
        >>> result = get_latest_market_news(10)
        >>> if result["status"] == "success":
        ...     news_list = result["data"]["news"]
        ...     print(f"获取到 {len(news_list)} 条最新快讯")
    """
    # 记录工具调用
    print(f"--- Tool: get_latest_market_news called with limit={limit} ---")
    
    # 输入验证
    if not isinstance(limit, int) or limit < 1 or limit > 1000:
        return {
            "status": "error",
            "error_message": "限制数量必须是1-1000之间的整数"
        }
    
    try:
        print(f"--- Tool: get_latest_market_news fetching data ---")
        market_data = get_market_data()
        
        # 限制返回数量
        limited_data = market_data[:limit] if len(market_data) > limit else market_data
        clean_data = []
        for item in limited_data:
            clean_data.append({
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "time": datetime.fromtimestamp(int(item.get("time", 0))).strftime("%Y-%m-%d %H:%M:%S"),
                "source": item.get("source", "")
            })
        # 构建成功响应
        news_data = {
            "news": clean_data,
            "count_info": {
                "total_available": len(market_data),
                "requested_limit": limit,
                "actual_returned": len(clean_data)
            }
        }
        
        metadata = {
            "timestamp": time.time(),
            "data_source": "AiCoin API",
            "requested_limit": limit,
            "total_available_count": len(market_data),
            "returned_count": len(clean_data)
        }
        
        # 记录成功结果
        print(f"--- Tool: get_latest_market_news completed successfully - returned={len(clean_data)}/{len(market_data)} news ---")
        
        return {
            "status": "success",
            "data": news_data,
            "metadata": metadata
        }
        
    except Exception as e:
        error_msg = f"获取最新市场快讯时发生错误: {str(e)}"
        print(f"--- Tool: get_latest_market_news failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

def search_market_news(keyword: str, page_size: int) -> dict:
    """使用AiCoin API搜索特定关键词的市场快讯。

    这个工具直接调用AiCoin的官方API来搜索包含指定关键词的市场快讯。
    适用于需要精确搜索特定主题、公司、货币或事件相关新闻的场景。

    Args:
        keyword (str): 搜索关键词。例如："比特币"、"美联储"、"加息"等
        page_size (int): 每页返回的快讯数量，建议范围1-100

    Returns:
        dict: 包含搜索结果的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含搜索结果数据
                - keyword (str): 搜索的关键词
                - news (list): 匹配的快讯列表
                - page_info (dict): 分页信息
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含API调用时间、搜索参数等

    示例:
        >>> result = search_market_news("比特币", 20)
        >>> if result["status"] == "success":
        ...     news_list = result["data"]["news"]
        ...     print(f"找到 {len(news_list)} 条相关快讯")
    """
    # 记录工具调用
    print(f"--- Tool: search_market_news called with keyword={keyword}, page_size={page_size} ---")
    
    # 输入验证和标准化
    if not keyword or not keyword.strip():
        return {
            "status": "error",
            "error_message": "搜索关键词不能为空"
        }
    
    keyword_normalized = keyword.strip()
    
    # 验证页面大小
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        return {
            "status": "error",
            "error_message": "页面大小必须是1-100之间的整数"
        }
    
    print(f"--- Tool: search_market_news normalized keyword: {keyword_normalized}, page_size: {page_size} ---")
    
    try:
        # API请求参数
        params = {
            "keyWord": keyword_normalized,
            "page": 1,
            "pageSize": page_size
        }
        
        # 请求头和Cookie
        headers = {
            'Content-Type': 'application/json',
            'Cookie': '_pk_id.2.2253=955c231aa2036c22.1685173517.; _ga_8V0M2EXPGG=deleted; _iidt=B1oEWvRWP8qb5RHl9oeSbf+MbJdb3X3D4YdyiC0LHfJpBztOqy1R+WG/yO5q2K2awKL05LpejSjh4A==; _vid_t=6QGXygrxI+fO7WIkdfCiFmi0QdBsFn5f5hNoXj+4STvA7Gsa0F+sPboBfVKCL2Jij+dg1zyyDgrTFw==; _pk_id.2.e882=88133c4497758297.1691215703.; _ga_8V0M2EXPGG=deleted; _ga=GA1.1.878337835.1685173517; _pk_id.DrK34NDqwv.2253=b9f60a4a625d746b.1693397753.; __gads=ID=4e623897912872aa-228b498c73e100be:T=1685173517:RT=1696242384:S=ALNI_MYOvy3l68iVsJGfxHB6uFLoIWrIjw; __gpi=UID=00000c0b87847f7d:T=1685173517:RT=1696242384:S=ALNI_MYizPbrJ9hR21iOuk1b2LrG-g0KXg; NEXT_LOCALE=zh-CN; _pk_ref.DrK34NDqwv.2253=%5B%22%22%2C%22%22%2C1708090536%2C%22https%3A%2F%2Faicoin.app%2F%22%5D; _pk_ses.DrK34NDqwv.2253=1; Hm_lvt_3c606e4c5bc6e9ff490f59ae4106beb4=1705725936,1707444191,1708090542; language=en; _ga_8V0M2EXPGG=GS1.1.1708090536.55.1.1708090768.0.0.0; Hm_lpvt_3c606e4c5bc6e9ff490f59ae4106beb4=1708090768; XSRF-TOKEN=eyJpdiI6Im95TkdZcDJiaWxWZG9NXC9zVkZ5b3R3PT0iLCJ2YWx1ZSI6Ik1meUlJTWNwT1wvc2pGalc5eEdcL0cwTHZzUm9pUWd6cjRrMVBcL3h3N0l5ZnI1eUtUbWU3bVJTV2VqWmhWTlhEUUJYenVPa0Z6blZkTlk4R2tVZlJrbWZ3PT0iLCJtYWMiOiI0OTIzYTA0NmNjZWJjOTI1ODk1ZmJmZmE1OGZjMzM3YWFhN2E0ZTcyOTEwM2RjYWZjYzkyYWQ0MjFhM2Y1NWU0In0%3D; aicoin_session=eyJpdiI6Im1seUs4S2NnRWlqYUVhMFwvXC9MQ2g3Zz09IiwidmFsdWUiOiJGSHptR2dpTnJ3UXRPSEw2SHRrU1pMM21UR1dLNlV1WHErU0dUOXZYd2V1bzN1Q1NCdzlkbCs2YVdGWmZLd2V1WDVCZmorajBiMzYzOE5WbGk4N28xZz09IiwibWFjIjoiNzcwOTJiY2E0NTU0MmU3YzM5MjA5ZDhhYTk1ZTcxM2I3NmFhMjJkZTQ0MTU0MWRmOGE1ZjdkYjFiZjQ1ZGI4MCJ9'
        }
        
        # 发送请求
        print(f"--- Tool: search_market_news making API request ---")
        response = requests.post(
            'https://www.aicoin.com/api/upgrade/search/newsflashByScore',
            json=params,
            headers=headers,
            timeout=30,
            verify=True
        )
        
        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"API请求失败，状态码: {response.status_code}"
            print(f"--- Tool: search_market_news failed - {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
        
        # 解析响应
        try:
            api_data = response.json()
        except ValueError as e:
            error_msg = f"解析API响应失败: {str(e)}"
            print(f"--- Tool: search_market_news failed - {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
        
        # 检查API响应状态
        if not api_data.get('success', False):
            error_msg = f"API返回错误: {api_data.get('message', '未知错误')}"
            print(f"--- Tool: search_market_news failed - {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
        
        # 提取新闻数据
        news_data = api_data.get('data', {})
        news_list = news_data.get('list', []) if isinstance(news_data.get('list'), list) else []
        clean_data = []
        for item in news_list:
            clean_data.append({
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "time": datetime.fromtimestamp(int(item.get("createTime", 0))).strftime("%Y-%m-%d %H:%M:%S"),
                "source": item.get("source", "")
            })
        # 构建成功响应
        search_data = {
            "keyword": keyword_normalized,
            "news": clean_data,
            "page_info": {
                "current_page": 1,
                "page_size": page_size,
                "total_count": news_data.get('count', len(clean_data)),
                "returned_count": len(clean_data)
            }
        }
        
        metadata = {
            "timestamp": time.time(),
            "api_url": "https://www.aicoin.com/api/upgrade/search/newsflashByScore",
            "search_keyword": keyword_normalized,
            "requested_page_size": page_size,
            "actual_returned_count": len(clean_data),
            "api_response_status": response.status_code
        }
        
        # 记录成功结果
        print(f"--- Tool: search_market_news completed successfully - keyword='{keyword_normalized}' found={len(clean_data)} news ---")
        
        return {
            "status": "success",
            "data": search_data,
            "metadata": metadata
        }
        
    except requests.exceptions.Timeout:
        error_msg = "API请求超时（30秒）"
        print(f"--- Tool: search_market_news failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except requests.exceptions.ConnectionError:
        error_msg = "无法连接到AiCoin API服务器"
        print(f"--- Tool: search_market_news failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except Exception as e:
        # 优雅的错误处理
        error_msg = f"搜索市场快讯时发生未知错误: {str(e)}"
        print(f"--- Tool: search_market_news failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

def batch_search_market_news(keywords: List[str], page_size_per_keyword: int) -> dict:
    """批量搜索多个关键词的市场快讯。

    这个工具允许同时搜索多个关键词，为每个关键词调用AiCoin API获取相关快讯。
    适用于需要同时监控多个主题、比较不同关键词相关新闻的场景。

    Args:
        keywords (List[str]): 搜索关键词列表。例如：["比特币", "以太坊", "美联储"]
        page_size_per_keyword (int): 每个关键词返回的快讯数量，建议范围1-100，默认10

    Returns:
        dict: 包含批量搜索结果的字典，具有以下结构：
            - status (str): 'success', 'partial_success' 或 'error'
            - data (dict): 成功时包含搜索结果数据
                - results (list): 每个关键词的搜索结果列表
                - summary (dict): 汇总统计信息
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含批量搜索的统计数据

    示例:
        >>> result = batch_search_market_news(["比特币", "以太坊"], 10)
        >>> if result["status"] in ["success", "partial_success"]:
        ...     for keyword_result in result["data"]["results"]:
        ...         print(f"关键词 '{keyword_result['keyword']}': {len(keyword_result['news'])} 条快讯")
    """
    # 记录工具调用
    print(f"--- Tool: batch_search_market_news called with keywords={keywords}, page_size_per_keyword={page_size_per_keyword} ---")
    
    # 输入验证
    if not keywords or not isinstance(keywords, list):
        return {
            "status": "error",
            "error_message": "关键词列表不能为空且必须是数组格式"
        }
    
    # 过滤和标准化关键词
    valid_keywords = []
    for keyword in keywords:
        if keyword and isinstance(keyword, str) and keyword.strip():
            valid_keywords.append(keyword.strip())
    
    if not valid_keywords:
        return {
            "status": "error",
            "error_message": "没有有效的搜索关键词"
        }
    
    # 验证页面大小
    if not isinstance(page_size_per_keyword, int) or page_size_per_keyword < 1 or page_size_per_keyword > 100:
        page_size_per_keyword = 10
    
    print(f"--- Tool: batch_search_market_news processing {len(valid_keywords)} valid keywords ---")
    
    # 批量搜索结果
    batch_results = []
    successful_searches = 0
    failed_searches = 0
    total_news_count = 0
    
    for i, keyword in enumerate(valid_keywords):
        print(f"--- Tool: batch_search_market_news processing keyword {i+1}/{len(valid_keywords)}: '{keyword}' ---")
        
        try:
            # 调用单个关键词搜索
            search_result = search_market_news(keyword, page_size_per_keyword)
            
            if search_result["status"] == "success":
                successful_searches += 1
                news_count = len(search_result["data"]["news"])
                total_news_count += news_count
                
                # 构建关键词结果
                keyword_result = {
                    "keyword": keyword,
                    "status": "success",
                    "news": search_result["data"]["news"],
                    "news_count": news_count,
                    "search_metadata": search_result.get("metadata", {})
                }
                
                print(f"--- Tool: batch_search_market_news keyword '{keyword}' success: {news_count} news found ---")
            else:
                failed_searches += 1
                keyword_result = {
                    "keyword": keyword,
                    "status": "error",
                    "news": [],
                    "news_count": 0,
                    "error_message": search_result.get("error_message", "未知错误")
                }
                
                print(f"--- Tool: batch_search_market_news keyword '{keyword}' failed: {search_result.get('error_message', 'Unknown error')} ---")
            
            batch_results.append(keyword_result)
            
            # 添加延迟以避免API限制
            if i < len(valid_keywords) - 1:  # 不在最后一个关键词后延迟
                time.sleep(0.5)
                
        except Exception as e:
            failed_searches += 1
            error_msg = f"搜索关键词 '{keyword}' 时发生异常: {str(e)}"
            
            keyword_result = {
                "keyword": keyword,
                "status": "error",
                "news": [],
                "news_count": 0,
                "error_message": error_msg
            }
            
            batch_results.append(keyword_result)
            print(f"--- Tool: batch_search_market_news keyword '{keyword}' exception: {error_msg} ---")
    
    # 确定整体状态
    if successful_searches == len(valid_keywords):
        overall_status = "success"
    elif successful_searches > 0:
        overall_status = "partial_success"
    else:
        overall_status = "error"
    
    # 构建汇总信息
    summary = {
        "total_keywords": len(valid_keywords),
        "successful_searches": successful_searches,
        "failed_searches": failed_searches,
        "total_news_found": total_news_count,
        "success_rate": round(successful_searches / len(valid_keywords) * 100, 2) if valid_keywords else 0
    }
    
    # 构建元数据
    metadata = {
        "timestamp": time.time(),
        "requested_keywords": valid_keywords,
        "page_size_per_keyword": page_size_per_keyword,
        "batch_processing_time": time.time(),
        "api_calls_made": len(valid_keywords)
    }
    
    # 构建最终响应
    if overall_status == "error":
        error_msg = f"批量搜索失败：{failed_searches}/{len(valid_keywords)} 个关键词搜索失败"
        print(f"--- Tool: batch_search_market_news completed with errors - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "data": {
                "results": batch_results,
                "summary": summary
            },
            "metadata": metadata
        }
    else:
        success_msg = f"批量搜索完成 - 成功: {successful_searches}/{len(valid_keywords)}, 总计找到: {total_news_count} 条快讯"
        print(f"--- Tool: batch_search_market_news completed successfully - {success_msg} ---")
        
        return {
            "status": overall_status,
            "data": {
                "results": batch_results,
                "summary": summary
            },
            "metadata": metadata
        }

def get_macro_data(limit: int) -> dict:
    """获取最新宏观经济快讯。

    获取最新的宏观经济快讯。
    适用于获取实时重要宏观信息。

    Args:
        limit (int): 限制返回的数据条数，建议范围1-100，默认50

    Returns:
        dict: 包含宏观数据的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含宏观数据
                - macro_data (list): 宏观快讯
                - count_info (dict): 数量统计信息
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含获取时间、数据源等

    示例:
        >>> result = get_macro_data(30)
        >>> if result["status"] == "success":
        ...     macro_list = result["data"]["macro_data"]
        ...     print(f"获取到 {len(macro_list)} 条宏观数据")
    """
    # 记录工具调用
    print(f"--- Tool: get_macro_data called with limit={limit} ---")
    
    # 输入验证
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        limit = 50
    
    try:
        # 计算 max_time (当前时间减去1小时)
        current_time = datetime.now()
        max_time = current_time - timedelta(hours=1)
        max_time_str = max_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建请求URL
        url = "https://flash-api.jin10.com/get_flash_list"
        params = {
            "channel": "-8200",
            "vip": "1",
            "max_time": max_time_str
        }
        
        # 设置请求头
        headers = {
            "x-app-id": "bVBF4FyRTn5NJF5n",
            "x-version": "1.0.0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.jin10.com/"
        }
        
        print(f"--- Tool: get_macro_data fetching data with max_time={max_time_str} ---")
        
        # 使用 curl_cffi 发送请求
        response = cffi_requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30,
            impersonate="chrome"  # 模拟 Chrome 浏览器
        )
        
        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"金十数据API请求失败，状态码: {response.status_code}"
            print(f"--- Tool: get_jin10_macro_data failed - {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
        
        # 解析响应
        try:
            api_data = response.json()
        except ValueError as e:
            error_msg = f"解析金十数据API响应失败: {str(e)}"
            print(f"--- Tool: get_jin10_macro_data failed - {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
        
        # 检查API响应结构
        if not isinstance(api_data, dict):
            error_msg = "金十数据API返回格式异常"
            print(f"--- Tool: get_jin10_macro_data failed - {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
        
        # 提取数据列表
        data_list = api_data.get("data", [])
        if not isinstance(data_list, list):
            data_list = []
        
        # 限制返回数量并清理数据
        limited_data = data_list[:limit] if len(data_list) > limit else data_list
        clean_data = []
        
        for item in limited_data:
            clean_item = {
                "time": item.get("time", ""),
                "content": item.get("data", "").get("content", ""),
            }
            clean_data.append(clean_item)
        
        # 构建成功响应
        macro_data = {
            "macro_data": clean_data,
            "count_info": {
                "total_available": len(data_list),
                "requested_limit": limit,
                "actual_returned": len(clean_data)
            }
        }
        
        metadata = {
            "timestamp": time.time(),
            "data_source": "金十数据",
            "api_url": url,
            "max_time_used": max_time_str,
            "requested_limit": limit,
            "total_available_count": len(data_list),
            "returned_count": len(clean_data),
            "api_response_status": response.status_code
        }
        
        # 记录成功结果
        print(f"--- Tool: get_jin10_macro_data completed successfully - returned={len(clean_data)}/{len(data_list)} macro data ---")
        
        return {
            "status": "success",
            "data": macro_data,
            "metadata": metadata
        }
        
    except cffi_requests.exceptions.Timeout:
        error_msg = "金十数据API请求超时（30秒）"
        print(f"--- Tool: get_jin10_macro_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except cffi_requests.exceptions.ConnectionError:
        error_msg = "无法连接到金十数据API服务器"
        print(f"--- Tool: get_jin10_macro_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except Exception as e:
        error_msg = f"获取金十宏观数据时发生未知错误: {str(e)}"
        print(f"--- Tool: get_jin10_macro_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

# 创建市场快讯 agent
market_news_agent = Agent(
    name="market_news_agent",
    model="gemini-2.5-flash-preview-05-20",
    description=(
        "专业的市场快讯获取智能体，提供实时金融新闻和市场动态。"
        "支持多种数据获取方式：最新快讯获取、关键词搜索、批量关键词搜索、金十宏观经济快讯获取。"
        "能够处理数据并提供结构化的市场信息分析。"
    ),
    instruction=(
        "你是一个专业的市场快讯助手，可以获取和分析最新的加密货币市场信息和宏观经济数据。"
        
        "可用工具和使用场景："
        "1. get_latest_market_news - 获取指定数量的最新市场快讯（来源：AiCoin）"
        "2. search_market_news - 使用API精确搜索单个关键词相关快讯（来源：AiCoin）"
        "3. batch_search_market_news - 批量搜索多个关键词，支持同时监控多个主题（来源：AiCoin）"
        "4. get_macro_data - 获取最新宏观经济快讯"
        
        "工作流程："
        "1. 仔细检查每个工具返回的 status 字段"
        "2. 成功时（status='success'）分析 data 字段中的内容"
        "3. 对于批量搜索，还需要处理 'partial_success' 状态"
        "4. 失败时（status='error'）解释 error_message 并建议解决方案"
        "5. 为用户提供清晰、有价值的市场信息摘要请包括具体时间点"
        "6. 根据用户需求选择最合适的工具"
        
        "最佳实践："
        "- 对于最新快讯，使用 get_latest_market_news"
        "- 对于单个关键词搜索，使用 search_market_news"
        "- 对于多个关键词同时搜索，使用 batch_search_market_news 提高效率"
        "- 对于宏观经济快讯，使用 get_macro_data 获取宏观经济快讯"
        "- 总结时突出重要的市场趋势和关键信息"
        "- 提供具体的数字统计和时间信息"
        "- 批量搜索时，分别展示每个关键词的结果和整体统计"
        "- 宏观快讯包含最新宏观经济快讯"
    ),
    tools=[get_latest_market_news, search_market_news, batch_search_market_news, get_macro_data],
) 


if __name__ == "__main__":
    # r1 = get_latest_market_news(100)
    # print(r1)
    
    # # 单个关键词搜索测试
    # r2 = search_market_news("比特币", 20)
    # print(r2)
    
    # 批量关键词搜索测试
    # r3 = batch_search_market_news(["比特币", "以太坊", "美联储"], 10)
    # print(r3)
    
    # 金十宏观数据测试
    r4 = get_macro_data(30)
    print(r4)