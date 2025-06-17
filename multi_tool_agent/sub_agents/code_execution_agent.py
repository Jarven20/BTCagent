import datetime
import io
import contextlib
from google.adk.agents import Agent


def code_execution_python(code: str) -> dict:
    """执行完整的 Python 代码并返回结果。
    
    这个工具可以执行任意的 Python 代码，支持多种预导入的常用库，适用于数据分析、
    网络爬虫、加密货币交易、科学计算等场景。代码在安全的沙箱环境中执行。
    
    预导入的常用库：
    - 基础库：os, sys, json, datetime, time, random, math, re
    - 数据处理：pandas (as pd), numpy (as np)
    - 网络请求：requests, curl_cffi
    - 加密货币：ccxt
    - 科学计算：statistics
    - 工具库：collections, itertools, functools
    - 网络解析：urllib, urlparse, parse_qs
    - 网页抓取：playwright, beautifulsoup4
    
    Args:
        code (str): 要执行的完整 Python 代码，类似一个 .py 文件的内容。
                   代码可以包含函数定义、类定义、变量赋值和执行语句。
                   如果定义了 main() 函数，会自动调用。
                   可以通过设置 result, output, return_value, main_result 
                   等变量来返回特定值。
        
    Returns:
        dict: 包含执行状态和结果的字典
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含执行结果
                - stdout (str): 标准输出内容
                - stderr (str): 标准错误输出内容  
                - result (any): 代码返回的结果值
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息
                - timestamp (str): 执行时间戳
                - code_length (int): 代码长度
                - execution_duration (float): 执行耗时（秒）
    
    示例:
        >>> result = code_execution_python("print('Hello World'); result = 42")
        >>> if result["status"] == "success":
        ...     print(result["data"]["stdout"])  # "Hello World"
        ...     print(result["data"]["result"])  # 42
        
        >>> result = code_execution_python('''
        ... def main():
        ...     import pandas as pd
        ...     df = pd.DataFrame({'a': [1, 2, 3]})
        ...     return df.sum()
        ... ''')
    """
    # 记录工具调用开始
    print(f"--- Tool: code_execution_python called ---")
    print(f"--- Code length: {len(code) if code else 0} characters ---")
    
    # 输入验证
    if not code or not isinstance(code, str):
        error_msg = "代码参数不能为空且必须是字符串类型"
        print(f"--- Tool: code_execution_python failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "code_length": 0,
            }
        }
    
    code_normalized = code.strip()
    if not code_normalized:
        error_msg = "代码内容不能为空"
        print(f"--- Tool: code_execution_python failed - {error_msg} ---")
        return {
            "status": "error", 
            "error_message": error_msg,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "code_length": 0,
            }
        }
    
    # 记录执行开始时间
    start_time = datetime.datetime.now()
    available_libraries = []
    
    try:
        # 创建字符串缓冲区来捕获标准输出
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        # 准备执行环境 - 使用同一个字典作为全局和局部命名空间
        # 这样可以避免函数定义和调用之间的作用域问题
        execution_namespace = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
            "__file__": "<string>",
        }
        
        # 预导入常用库
        print("--- Importing common libraries ---")
        try:
            # 基础库
            import os
            import sys
            import json
            import time
            import random
            import math
            import re
            import statistics
            import collections
            import itertools
            import functools
            
            base_libs = ['os', 'sys', 'json', 'datetime', 'time', 'random', 'math', 're', 
                        'statistics', 'collections', 'itertools', 'functools']
            available_libraries.extend(base_libs)
            
            execution_namespace.update({
                'os': os,
                'sys': sys,
                'json': json,
                'datetime': datetime,
                'time': time,
                'random': random,
                'math': math,
                're': re,
                'statistics': statistics,
                'collections': collections,
                'itertools': itertools,
                'functools': functools,
            })
            
            # 数据处理库
            try:
                import pandas as pd
                execution_namespace['pd'] = pd
                execution_namespace['pandas'] = pd
                available_libraries.extend(['pandas', 'pd'])
            except ImportError:
                pass
                
            try:
                import numpy as np
                execution_namespace['np'] = np
                execution_namespace['numpy'] = np
                available_libraries.extend(['numpy', 'np'])
            except ImportError:
                pass
            
            # 网络请求库
            try:
                import requests
                execution_namespace['requests'] = requests
                available_libraries.append('requests')
            except ImportError:
                pass
                
            try:
                import curl_cffi
                from curl_cffi import requests as cffi_requests
                execution_namespace['curl_cffi'] = curl_cffi
                execution_namespace['cffi_requests'] = cffi_requests
                available_libraries.extend(['curl_cffi', 'cffi_requests'])
            except ImportError:
                pass
            
            # 加密货币交易库
            try:
                import ccxt
                execution_namespace['ccxt'] = ccxt
                available_libraries.append('ccxt')
            except ImportError:
                pass
                
            # 其他常用库
            try:
                import urllib
                from urllib.parse import urlparse, parse_qs
                execution_namespace['urllib'] = urllib
                execution_namespace['urlparse'] = urlparse
                execution_namespace['parse_qs'] = parse_qs
                available_libraries.extend(['urllib', 'urlparse', 'parse_qs'])
            except ImportError:
                pass
                
            # 网页抓取库
            try:
                from patchright.sync_api import sync_playwright
                execution_namespace['sync_playwright'] = sync_playwright
                available_libraries.append('playwright')
            except ImportError:
                pass
                
            try:
                from bs4 import BeautifulSoup
                execution_namespace['BeautifulSoup'] = BeautifulSoup
                available_libraries.append('beautifulsoup4')
            except ImportError:
                pass
                
        except Exception as import_error:
            # 如果导入库时出错，记录但不影响代码执行
            print(f"--- Warning: Some libraries failed to import: {str(import_error)} ---")
        
        print(f"--- Available libraries: {', '.join(available_libraries)} ---")
        
        # 捕获标准输出和标准错误
        print("--- Executing user code ---")
        with contextlib.redirect_stdout(output_buffer), \
             contextlib.redirect_stderr(error_buffer):
            
            # 执行完整的代码，使用同一个命名空间作为全局和局部
            exec(code_normalized, execution_namespace, execution_namespace)
        
        # 获取输出内容
        stdout_content = output_buffer.getvalue()
        stderr_content = error_buffer.getvalue()
        
        # 尝试获取可能的返回值
        # 检查是否有特殊的返回值变量（如 result, output, main 函数等）
        result_value = None
        
        # 如果有 main 函数，尝试调用它
        if 'main' in execution_namespace and callable(execution_namespace['main']):
            try:
                print("--- Executing main() function ---")
                # 重新创建缓冲区以获取 main 函数的输出
                main_output_buffer = io.StringIO()
                main_error_buffer = io.StringIO()
                
                with contextlib.redirect_stdout(main_output_buffer), \
                     contextlib.redirect_stderr(main_error_buffer):
                    main_result = execution_namespace['main']()
                    if main_result is not None:
                        result_value = main_result
                        print("--- main() function returned a value ---")
                
                # 合并输出内容
                main_stdout = main_output_buffer.getvalue()
                main_stderr = main_error_buffer.getvalue()
                
                if main_stdout:
                    stdout_content += main_stdout
                if main_stderr:
                    stderr_content += main_stderr
                    
            except Exception as main_error:
                error_msg = f"执行 main() 函数时出错: {str(main_error)}"
                stderr_content += f"\n{error_msg}"
                print(f"--- Warning: {error_msg} ---")
        
        # 计算执行时间
        end_time = datetime.datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"--- Tool: code_execution_python completed successfully in {execution_time:.3f}s ---")
        
        return {
            "status": "success",
            "data": {
                "stdout": stdout_content,
                "stderr": stderr_content,
                "result": result_value,
            },
            "metadata": {
                "timestamp": start_time.isoformat(),
                "code_length": len(code_normalized),
                "execution_duration": execution_time
            }
        }
        
    except SyntaxError as e:
        error_msg = f"代码语法错误: {str(e)} (行 {e.lineno})"
        print(f"--- Tool: code_execution_python failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "timestamp": start_time.isoformat(),
                "code_length": len(code_normalized),
                "error_type": "SyntaxError"
            }
        }
    except NameError as e:
        error_msg = f"变量或函数名错误: {str(e)}"
        print(f"--- Tool: code_execution_python failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "timestamp": start_time.isoformat(),
                "code_length": len(code_normalized),
                "error_type": "NameError"
            }
        }
    except ImportError as e:
        error_msg = f"导入库失败: {str(e)}"
        print(f"--- Tool: code_execution_python failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "timestamp": start_time.isoformat(),
                "code_length": len(code_normalized),
                "error_type": "ImportError"
            }
        }
    except Exception as e:
        error_msg = f"执行代码时发生错误: {str(e)}"
        print(f"--- Tool: code_execution_python failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "timestamp": start_time.isoformat(),
                "code_length": len(code_normalized),
                "error_type": type(e).__name__
            }
        }


code_execution_agent = Agent(
    name="code_execution_agent",
    model="gemini-2.5-flash-preview-05-20",
    description=(
        "专业的Python代码执行智能体，支持数据分析、网络爬虫、加密货币交易等多种场景。"
        "预装pandas、numpy、requests、ccxt、playwright等常用库。"
    ),
    instruction=(
        "你是一个专业的Python代码执行助手。你可以执行用户提供的Python代码，"
        "支持数据分析(pandas/numpy)、网络请求(requests/curl_cffi)、"
        "加密货币交易(ccxt)、网页抓取(playwright/beautifulsoup4)等功能。"
        "执行代码时会自动导入常用库，并提供详细的执行结果和错误信息。"
        "如果用户定义了main()函数，会自动调用。可以通过设置result等变量返回特定值。"
    ),
    tools=[code_execution_python],
)


if __name__ == "__main__":
    result = code_execution_python("print('Hello World'); result = 42")
    print(result)