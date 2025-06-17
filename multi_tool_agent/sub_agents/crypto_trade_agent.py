"""
加密货币交易代理 - 严格遵守ADK最佳实践

核心特性：
1. ✅ 移除所有默认参数值 - LLM无法理解默认值
2. ✅ 统一日志记录格式 - "--- Tool: function_name called/completed/failed ---"
3. ✅ 标准化返回值格式 - status/data/error_message/metadata结构
4. ✅ 完善错误处理和用户友好的错误消息
5. ✅ 详细的文档字符串，包含示例和参数说明
6. ✅ 输入验证和参数标准化

优化的交易工具函数：
- get_spot_balance(exchange_name) - 获取现货账户余额
- place_spot_order(symbol, side, amount, price, exchange_name) - 下现货订单
- get_spot_orders(symbol, exchange_name) - 获取现货订单历史
- cancel_spot_order(order_id, symbol, exchange_name) - 撤销现货订单
- get_futures_balance(exchange_name) - 获取合约账户余额
- get_futures_positions(symbol, exchange_name) - 获取合约持仓
- place_futures_order(symbol, side, amount, price, exchange_name) - 下合约订单
- get_savings_products(exchange_name) - 获取余币宝产品
- purchase_savings_product(asset, amount, exchange_name) - 申购余币宝
- get_savings_balance(exchange_name) - 获取余币宝持仓
"""
import math
import ccxt
import time
import logging
import os
from typing import List, Dict, Any, Optional, Union
from google.adk.agents import Agent
import dotenv

# 设置日志
logger = logging.getLogger(__name__)

def _get_api_credentials(exchange_name: str) -> Dict[str, str]:
    """从环境变量获取API凭据
    
    Args:
        exchange_name (str): 交易所名称
        
    Returns:
        Dict[str, str]: 包含API凭据的字典
    """
    dotenv.load_dotenv()
    exchange_upper = exchange_name.upper()
    
    api_key = os.getenv(f'{exchange_upper}_API_KEY', '')
    secret = os.getenv(f'{exchange_upper}_SECRET', '')
    password = os.getenv(f'{exchange_upper}_PASSWORD', '')  # 主要用于OKX
    
    return {
        'api_key': api_key,
        'secret': secret,
        'password': password
    }

# 支持的交易所列表
SUPPORTED_EXCHANGES = {
    'binance': ccxt.binance,
    'okx': ccxt.okx,
}

def _get_exchange(exchange_name: str, api_key: str, secret: str, password: str) -> ccxt.Exchange:
    """获取交易所实例
    
    Args:
        exchange_name (str): 交易所名称
        api_key (str): API密钥
        secret (str): API密钥的秘钥
        password (str): 某些交易所需要的密码（如OKX）
        
    Returns:
        ccxt.Exchange: 交易所实例
        
    Raises:
        ValueError: 如果交易所不支持
    """
    if exchange_name.lower() not in SUPPORTED_EXCHANGES:
        raise ValueError(f"不支持的交易所: {exchange_name}. 支持的交易所: {list(SUPPORTED_EXCHANGES.keys())}")
    
    exchange_class = SUPPORTED_EXCHANGES[exchange_name.lower()]
    config = {
        'apiKey': api_key,
        'secret': secret,
        'timeout': 30000,
        'enableRateLimit': True,
    }
    
    # OKX需要passphrase
    if exchange_name.lower() == 'okx' and password:
        config['password'] = password
    
    # 添加代理支持
    http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
    if http_proxy or https_proxy:
        proxy_url = https_proxy or http_proxy
        config['proxies'] = {
            'http': proxy_url,
            'https': proxy_url
        }
    
    exchange = exchange_class(config)
    exchange.load_markets()
    return exchange

# ========== 现货交易功能 ==========

def get_spot_balance(exchange_name: str) -> Dict[str, Any]:
    """获取现货账户余额信息。
    
    查询指定交易所的现货账户中各币种的余额情况，包括可用余额、冻结余额和总余额。
    用于了解账户资产状况，为交易决策提供资金基础信息。
    
    Args:
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含账户余额信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含余额数据
                - balances (dict): 各币种余额信息，键为币种名称
                    - free (float): 可用余额
                    - used (float): 冻结余额
                    - total (float): 总余额
                - total_currencies (int): 有余额的币种数量
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息，包含交易所和时间戳
    
    示例:
        >>> result = get_spot_balance("binance")
        >>> if result["status"] == "success":
        ...     balances = result["data"]["balances"]
        ...     for currency, amounts in balances.items():
        ...         print(f"{currency}: {amounts['total']}")
    """
    print(f"--- Tool: get_spot_balance called with exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取账户余额",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        balance = exchange.fetch_balance()
        
        # 过滤非零余额
        non_zero_balances = {}
        for currency, amounts in balance.items():
            if isinstance(amounts, dict) and amounts.get('total', 0) > 0:
                non_zero_balances[currency] = {
                    'free': amounts.get('free', 0),
                    'used': amounts.get('used', 0),
                    'total': amounts.get('total', 0)
                }
        
        print(f"--- Tool: get_spot_balance completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "balances": non_zero_balances,
                "total_currencies": len(non_zero_balances)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_spot_balance failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取现货账户余额失败: {str(e)}"
        print(f"--- Tool: get_spot_balance failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }

def place_spot_order(symbol: str, side: str, amount: float, price: float, exchange_name: str) -> Dict[str, Any]:
    """下现货交易订单。
    
    在指定交易所下现货买卖订单，支持限价单和市价单。
    限价单需要指定价格，市价单按当前市场价格成交。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'、'ETH/USDT'
        side (str): 买卖方向，'buy'表示买入，'sell'表示卖出
        amount (float): 交易数量，基础货币数量
        price (float): 交易价格，限价单时必须提供，市价单时可传0
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含订单信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - order_id (str): 订单ID
                - symbol (str): 交易对符号
                - side (str): 买卖方向
                - amount (float): 交易数量
                - price (float): 交易价格
                - type (str): 订单类型
                - status (str): 订单状态
                - timestamp (int): 下单时间戳
                - datetime (str): 格式化时间
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 限价买入
        >>> result = place_spot_order("BTC/USDT", "buy", 0.001, 50000, "binance")
        >>> # 市价卖出
        >>> result = place_spot_order("ETH/USDT", "sell", 0.1, 0, "binance")
    """
    print(f"--- Tool: place_spot_order called with symbol={symbol}, side={side}, amount={amount}, price={price}, exchange_name={exchange_name} ---")
    
    order_type = 'limit'
    # 输入验证
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT'格式的交易对"
        }
    
    if not side or side.strip().lower() not in ['buy', 'sell']:
        return {
            "status": "error",
            "error_message": "买卖方向必须是'buy'或'sell'"
        }
    
    if not isinstance(amount, (int, float)) or amount <= 0:
        return {
            "status": "error",
            "error_message": "交易数量必须是大于0的数字"
        }
    
    if not order_type or order_type.strip().lower() not in ['limit', 'market']:
        return {
            "status": "error",
            "error_message": "订单类型必须是'limit'或'market'"
        }
    
    if order_type.strip().lower() == 'limit' and (not isinstance(price, (int, float)) or price <= 0):
        return {
            "status": "error",
            "error_message": "限价单必须指定大于0的价格"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper()
    side_normalized = side.strip().lower()
    order_type_normalized = order_type.strip().lower()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能下单",
                "metadata": {
                    "exchange": exchange_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 下单
        if order_type_normalized == 'limit':
            order = exchange.create_limit_order(symbol_normalized, side_normalized, amount, price)
        else:  # market order
            order = exchange.create_market_order(symbol_normalized, side_normalized, amount)
        
        print(f"--- Tool: place_spot_order completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "order_id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "timestamp": order['timestamp'],
                "datetime": order['datetime']
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或参数错误: {str(e)}"
        print(f"--- Tool: place_spot_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"下现货订单失败: {str(e)}"
        print(f"--- Tool: place_spot_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_spot_orders(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取现货订单历史记录。
    
    查询指定交易对或所有交易对的现货订单历史，包括已完成、部分成交、已取消等状态的订单。
    用于跟踪交易记录、分析交易表现、管理订单状态。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'。传入空字符串表示获取所有交易对
        exchange_name (str): 交易所名称，支持'binance'
        
    Returns:
        dict: 包含订单历史信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - orders (list): 订单列表，每个元素包含：
                    - id (str): 订单ID
                    - symbol (str): 交易对符号
                    - side (str): 买卖方向
                    - amount (float): 订单数量
                    - price (float): 订单价格
                    - type (str): 订单类型
                    - status (str): 订单状态
                    - filled (float): 已成交数量
                    - remaining (float): 剩余数量
                    - timestamp (int): 下单时间戳
                    - datetime (str): 格式化时间
                - count (int): 订单总数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 获取BTC/USDT订单历史
        >>> result = get_spot_orders("BTC/USDT", "binance")
        >>> # 获取所有订单历史
        >>> result = get_spot_orders("", "binance")
    """
    print(f"--- Tool: get_spot_orders called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper() if symbol and symbol.strip() else None
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取订单信息",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 获取订单
        if symbol_normalized:
            orders = exchange.fetch_orders(symbol_normalized)
        else:
            orders = exchange.fetch_orders()
        
        # 处理订单数据
        processed_orders = []
        for order in orders:
            processed_orders.append({
                "id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "filled": order['filled'],
                "remaining": order['remaining'],
                "timestamp": order['timestamp'],
                "datetime": order['datetime']
            })
        
        print(f"--- Tool: get_spot_orders completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "orders": processed_orders,
                "count": len(processed_orders)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_spot_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取现货订单历史失败: {str(e)}"
        print(f"--- Tool: get_spot_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def cancel_spot_order(order_id: str, symbol: str, exchange_name: str) -> Dict[str, Any]:
    """撤销现货交易订单。
    
    撤销指定的现货订单，适用于未完全成交的限价单。
    撤单后，未成交的部分将被取消，已成交部分不受影响。
    
    Args:
        order_id (str): 订单ID，从下单或查询订单接口获取
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含撤单结果的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含撤单数据
                - order_id (str): 订单ID
                - symbol (str): 交易对符号
                - status (str): 撤单后的订单状态
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = cancel_spot_order("12345678", "BTC/USDT", "binance")
        >>> if result["status"] == "success":
        ...     print(f"订单 {result['data']['order_id']} 已成功撤销")
    """
    print(f"--- Tool: cancel_spot_order called with order_id={order_id}, symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not order_id or not order_id.strip():
        return {
            "status": "error",
            "error_message": "订单ID不能为空"
        }
    
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT'格式的交易对"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    order_id_normalized = order_id.strip()
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能撤单",
                "metadata": {
                    "exchange": exchange_normalized,
                    "order_id": order_id_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        result = exchange.cancel_order(order_id_normalized, symbol_normalized)
        
        print(f"--- Tool: cancel_spot_order completed successfully for order {order_id_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "order_id": result['id'],
                "symbol": result['symbol'],
                "status": result['status']
            },
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: cancel_spot_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"撤销现货订单失败: {str(e)}"
        print(f"--- Tool: cancel_spot_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }

def get_spot_open_orders(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取现货未成交订单列表。
    
    查询指定交易对或所有交易对的未成交现货订单，包括部分成交和完全未成交的订单。
    用于监控当前活跃订单状态，管理挂单策略。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'。传入空字符串表示获取所有交易对
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含未成交订单信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - orders (list): 未成交订单列表，每个元素包含：
                    - id (str): 订单ID
                    - symbol (str): 交易对符号
                    - side (str): 买卖方向
                    - amount (float): 订单数量
                    - price (float): 订单价格
                    - type (str): 订单类型
                    - status (str): 订单状态
                    - filled (float): 已成交数量
                    - remaining (float): 剩余数量
                    - timestamp (int): 下单时间戳
                    - datetime (str): 格式化时间
                - count (int): 未成交订单总数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 获取BTC/USDT未成交订单
        >>> result = get_spot_open_orders("BTC/USDT", "binance")
        >>> # 获取所有未成交订单
        >>> result = get_spot_open_orders("", "binance")
    """
    print(f"--- Tool: get_spot_open_orders called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper() if symbol and symbol.strip() else None
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取未成交订单",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 获取未成交订单
        if symbol_normalized:
            orders = exchange.fetch_open_orders(symbol_normalized)
        else:
            orders = exchange.fetch_open_orders()
        
        # 处理订单数据
        processed_orders = []
        for order in orders:
            processed_orders.append({
                "id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "filled": order['filled'],
                "remaining": order['remaining'],
                "timestamp": order['timestamp'],
                "datetime": order['datetime']
            })
        
        print(f"--- Tool: get_spot_open_orders completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "orders": processed_orders,
                "count": len(processed_orders)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_spot_open_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取现货未成交订单失败: {str(e)}"
        print(f"--- Tool: get_spot_open_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_spot_closed_orders(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取现货已成交订单列表。
    
    查询指定交易对或所有交易对的已完全成交的现货订单历史。
    用于分析交易记录、计算盈亏、统计交易表现。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'。传入空字符串表示获取所有交易对
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含已成交订单信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - orders (list): 已成交订单列表，每个元素包含：
                    - id (str): 订单ID
                    - symbol (str): 交易对符号
                    - side (str): 买卖方向
                    - amount (float): 订单数量
                    - price (float): 成交价格
                    - type (str): 订单类型
                    - status (str): 订单状态（通常为'closed'）
                    - filled (float): 已成交数量
                    - cost (float): 成交金额
                    - fee (dict): 手续费信息
                    - timestamp (int): 成交时间戳
                    - datetime (str): 格式化时间
                - count (int): 已成交订单总数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 获取BTC/USDT已成交订单
        >>> result = get_spot_closed_orders("BTC/USDT", "binance")
        >>> # 获取所有已成交订单
        >>> result = get_spot_closed_orders("", "binance")
    """
    print(f"--- Tool: get_spot_closed_orders called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper() if symbol and symbol.strip() else None
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取已成交订单",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 获取已成交订单
        if symbol_normalized:
            orders = exchange.fetch_closed_orders(symbol_normalized)
        else:
            orders = exchange.fetch_closed_orders()
        
        # 处理订单数据
        processed_orders = []
        for order in orders:
            processed_orders.append({
                "id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "filled": order['filled'],
                "cost": order['cost'],
                "fee": order.get('fee', {}),
                "timestamp": order['timestamp'],
                "datetime": order['datetime']
            })
        
        print(f"--- Tool: get_spot_closed_orders completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "orders": processed_orders,
                "count": len(processed_orders)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_spot_closed_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取现货已成交订单失败: {str(e)}"
        print(f"--- Tool: get_spot_closed_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_spot_order_detail(order_id: str, symbol: str, exchange_name: str) -> Dict[str, Any]:
    """根据订单ID查询现货订单详情。
    
    查询指定订单ID的详细信息，包括订单状态、成交情况、手续费等完整信息。
    用于跟踪特定订单的执行情况和详细数据。
    
    Args:
        order_id (str): 订单ID，从下单或查询订单接口获取
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含订单详情的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单详细数据
                - id (str): 订单ID
                - symbol (str): 交易对符号
                - side (str): 买卖方向
                - amount (float): 订单数量
                - price (float): 订单价格
                - average (float): 平均成交价格
                - type (str): 订单类型
                - status (str): 订单状态
                - filled (float): 已成交数量
                - remaining (float): 剩余数量
                - cost (float): 成交金额
                - fee (dict): 手续费详情
                - trades (list): 成交明细列表
                - timestamp (int): 下单时间戳
                - datetime (str): 格式化时间
                - lastTradeTimestamp (int): 最后成交时间戳
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_spot_order_detail("12345678", "BTC/USDT", "binance")
        >>> if result["status"] == "success":
        ...     order = result["data"]
        ...     print(f"订单状态: {order['status']}, 成交比例: {order['filled']}/{order['amount']}")
    """
    print(f"--- Tool: get_spot_order_detail called with order_id={order_id}, symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not order_id or not order_id.strip():
        return {
            "status": "error",
            "error_message": "订单ID不能为空"
        }
    
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT'格式的交易对"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    order_id_normalized = order_id.strip()
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能查询订单详情",
                "metadata": {
                    "exchange": exchange_normalized,
                    "order_id": order_id_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        order = exchange.fetch_order(order_id_normalized, symbol_normalized)
        
        # 处理订单数据
        order_detail = {
            "id": order['id'],
            "symbol": order['symbol'],
            "side": order['side'],
            "amount": order['amount'],
            "price": order['price'],
            "average": order.get('average'),
            "type": order['type'],
            "status": order['status'],
            "filled": order['filled'],
            "remaining": order['remaining'],
            "cost": order['cost'],
            "fee": order.get('fee', {}),
            "trades": order.get('trades', []),
            "timestamp": order['timestamp'],
            "datetime": order['datetime'],
            "lastTradeTimestamp": order.get('lastTradeTimestamp')
        }
        
        print(f"--- Tool: get_spot_order_detail completed successfully for order {order_id_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": order_detail,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_spot_order_detail failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"查询现货订单详情失败: {str(e)}"
        print(f"--- Tool: get_spot_order_detail failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }

# ========== 合约交易功能 ==========

def get_futures_balance(exchange_name: str) -> Dict[str, Any]:
    """获取合约账户余额和保证金信息。
    
    查询指定交易所的合约账户余额，包括可用保证金、已用保证金、总权益等信息。
    用于了解合约账户资金状况，评估可开仓规模和风险控制。
    
    Args:
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含合约账户余额信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含余额数据
                - balance (dict): 完整余额信息
                - free (dict): 可用余额，按币种分类
                - used (dict): 已用余额（保证金），按币种分类
                - total (dict): 总余额，按币种分类
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息，包含交易所和时间戳
    
    示例:
        >>> result = get_futures_balance("binance")
        >>> if result["status"] == "success":
        ...     total_usdt = result["data"]["total"].get("USDT", 0)
        ...     print(f"合约账户USDT总余额: {total_usdt}")
    """
    print(f"--- Tool: get_futures_balance called with exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取合约账户余额",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        # positionSide: 'LONG',
        # portfolioMargin: true // 启用组合保证金
        # exchange.options['defaultType'] = 'portfolioMargin'
        
        if exchange_normalized == 'binance':
            balance = exchange.fetch_balance({'type': 'papi'})
        else:
            balance = exchange.fetch_balance({'type': 'trading'})
        
        print(f"--- Tool: get_futures_balance completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "balance": balance,
                "free": balance.get('free', {}),
                "used": balance.get('used', {}),
                "total": balance.get('total', {})
            },
            "metadata": {
                "exchange": exchange_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_futures_balance failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取合约账户余额失败: {str(e)}"
        print(f"--- Tool: get_futures_balance failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }

def get_futures_positions(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取合约持仓信息。
    
    查询指定交易对或所有交易对的合约持仓情况，包括仓位大小、未实现盈亏、
    进入价格、标记价格等关键信息。用于监控持仓状态和风险管理。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE:QUOTE' 或 'BASE/QUOTE:BASE'，如'BTC/USDT:BTC'、'BTC/USDT:USDT'。传入空字符串表示获取所有持仓。'BTC/USDT:BTC'：指的是币本位合约，'BTC/USDT:USDT'：指的是U本位合约。
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含持仓信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含持仓数据
                - positions (list): 活跃持仓列表，每个元素包含：
                    - symbol (str): 交易对符号
                    - side (str): 持仓方向（'long'或'short'）
                    - size (float): 持仓数量
                    - notional (float): 持仓名义价值
                    - unrealized_pnl (float): 未实现盈亏
                    - percentage (float): 盈亏百分比
                    - entry_price (float): 平均进入价格
                    - mark_price (float): 标记价格
                    - timestamp (int): 时间戳
                - count (int): 活跃持仓数量
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 获取BTC/USDT:USDT持仓
        >>> result = get_futures_positions("BTC/USDT:USDT", "binance")
        >>> # 获取所有持仓
        >>> result = get_futures_positions("", "binance")
    """
    print(f"--- Tool: get_futures_positions called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper() if symbol and symbol.strip() else ''
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取持仓信息",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        exchange.options['defaultType'] = 'future'
        
        params = {}
        if exchange_normalized == 'binance':
            params['portfolioMargin'] = True
            params['method'] = 'account'
        else:
            params['instType'] = 'SWAP'

        if symbol_normalized:
            positions = exchange.fetch_positions([symbol_normalized], params=params)
        else:
            positions = exchange.fetch_positions(params=params)
        
        # 过滤非零持仓
        active_positions = []
        for position in positions:
            if position['contracts'] and position['contracts'] != 0:
                active_positions.append({
                    "symbol": position['symbol'],
                    "side": position['side'],
                    "size": position['contracts'],
                    "notional": position['notional'],
                    "unrealized_pnl": position['unrealizedPnl'],
                    "percentage": position['percentage'],
                    "entry_price": position['entryPrice'],
                    "mark_price": position['markPrice'],
                    "timestamp": position['timestamp']
                })
        
        print(f"--- Tool: get_futures_positions completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "positions": active_positions,
                "count": len(active_positions)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_futures_positions failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取合约持仓失败: {str(e)}"
        print(f"--- Tool: get_futures_positions failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def place_futures_order(symbol: str, side: str, amount: float, price: float, exchange_name: str) -> Dict[str, Any]:
    """下合约交易订单。
    
    在指定交易所下合约买卖订单，支持开多、开空、平多、平空操作。
    支持限价单和市价单，用于建立或调整合约持仓。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE:QUOTE' 或 'BASE/QUOTE:BASE'，如'BTC/USDT:BTC'、'BTC/USDT:USDT'。传入空字符串表示获取所有持仓。'BTC/USDT:BTC'：指的是币本位合约，'BTC/USDT:USDT'：指的是U本位合约。
        side (str): 买卖方向，'open_long'表示开多，'open_short'表示开空, 'close_long'表示平多, 'close_short'表示平空
        amount (float): 交易数量，单纯的币种数量，不是合约张数
        price (float): 交易价格，限价单时必须提供，市价单时可传0
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含订单信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - order_id (str): 订单ID
                - symbol (str): 交易对符号
                - side (str): 买卖方向
                - amount (float): 交易数量
                - price (float): 交易价格
                - type (str): 订单类型
                - status (str): 订单状态
                - timestamp (int): 下单时间戳
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 限价开多
        >>> result = place_futures_order("BTC/USDT:USDT", "open_long", 0.001, 50000, "binance")
        >>> # 限价平空
        >>> result = place_futures_order("ETH/USDT:USDT", "close_short", 0.1, 0, "binance")
    """
    print(f"--- Tool: place_futures_order called with symbol={symbol}, side={side}, amount={amount}, price={price}, exchange_name={exchange_name} ---")
    
    order_type = 'limit'
    # 输入验证
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT:USDT'或'BTC/USDT:BTC'格式的交易对"
        }
    
    if ':' not in symbol:
        return {
            "status": "error",
            "error_message": "交易对符号格式错误，请提供如'BTC/USDT:USDT'或'BTC/USDT:BTC'格式的交易对"
        }
    
    if not side or side.strip().lower() not in ['open_long', 'open_short', 'close_long', 'close_short']:
        return {
            "status": "error",
            "error_message": "买卖方向必须是'open_long'或'open_short'或'close_long'或'close_short'"
        }
    
    if not isinstance(amount, (int, float)) or amount <= 0:
        return {
            "status": "error",
            "error_message": "交易数量必须是大于0的数字"
        }
    
    if not order_type or order_type.strip().lower() not in ['limit', 'market']:
        return {
            "status": "error",
            "error_message": "订单类型必须是'limit'或'market'"
        }
    
    if order_type.strip().lower() == 'limit' and (not isinstance(price, (int, float)) or price <= 0):
        return {
            "status": "error",
            "error_message": "限价单必须指定大于0的价格"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper()
    side_normalized = side.strip().lower()
    order_type_normalized = order_type.strip().lower()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能下合约订单",
                "metadata": {
                    "exchange": exchange_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        params = {}
        if exchange_normalized == 'binance':
            params['portfolioMargin'] = True
            params['positionSide'] = 'LONG' if side_normalized == 'open_long' else 'SHORT' if side_normalized == 'open_short' else 'LONG' if side_normalized == 'close_long' else 'SHORT' if side_normalized == 'close_short' else None
        else:
            params['hedged'] = True
            params['positionSide'] = 'long' if side_normalized == 'open_long' else 'short' if side_normalized == 'open_short' else 'long' if side_normalized == 'close_long' else 'short' if side_normalized == 'close_short' else None
        
        sheet = amount / exchange.markets[symbol_normalized]['contractSize']
        amount_precision = str(exchange.markets[symbol_normalized]['precision']['amount'])
        if '.' in amount_precision:
            amountPrecisionDigits = len(amount_precision.split('.')[1]) 
            sheet = math.floor(sheet * 10 ** amountPrecisionDigits) / 10 ** amountPrecisionDigits
        else:
            sheet = math.floor(sheet)

        price_precision = str(exchange.markets[symbol_normalized]['precision']['price'])
        if '.' in price_precision:
            pricePrecisionDigits = len(price_precision.split('.')[1]) 
            price = math.floor(price * 10 ** pricePrecisionDigits) / 10 ** pricePrecisionDigits
        else:
            price = math.floor(price)

        # if 'close' in side_normalized:
        #     params['reduceOnly'] = True
        
        new_side = ''
        if 'open_long' in side_normalized:
            new_side = 'buy'
        elif 'open_short' in side_normalized:
            new_side = 'sell'
        elif 'close_long' in side_normalized:
            new_side = 'sell'
        elif 'close_short' in side_normalized:
            new_side = 'buy'

        # 下单
        if order_type_normalized == 'limit':
            order = exchange.create_limit_order(symbol_normalized, new_side, sheet, price, params=params)
        else:  # market order
            order = exchange.create_market_order(symbol_normalized, new_side, sheet, params=params)
        
        print(f"--- Tool: place_futures_order completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "order_id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "timestamp": order['timestamp']
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或参数错误: {str(e)}"
        print(f"--- Tool: place_futures_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"下合约订单失败: {str(e)}"
        print(f"--- Tool: place_futures_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_futures_open_orders(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取合约未成交订单列表。
    
    查询指定交易对或所有交易对的未成交合约订单，包括部分成交和完全未成交的订单。
    用于监控当前活跃的合约订单状态，管理持仓策略。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE:QUOTE' 或 'BASE/QUOTE:BASE'，如'BTC/USDT:BTC'、'BTC/USDT:USDT'。传入空字符串表示获取所有持仓。'BTC/USDT:BTC'：指的是币本位合约，'BTC/USDT:USDT'：指的是U本位合约。
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含未成交订单信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - orders (list): 未成交订单列表，每个元素包含：
                    - id (str): 订单ID
                    - symbol (str): 交易对符号
                    - side (str): 买卖方向
                    - amount (float): 订单数量
                    - price (float): 订单价格
                    - type (str): 订单类型
                    - status (str): 订单状态
                    - filled (float): 已成交数量
                    - remaining (float): 剩余数量
                    - timestamp (int): 下单时间戳
                    - datetime (str): 格式化时间
                - count (int): 未成交订单总数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 获取BTC/USDT:USDT未成交合约订单
        >>> result = get_futures_open_orders("BTC/USDT:USDT", "binance")
        >>> # 获取所有未成交合约订单
        >>> result = get_futures_open_orders("", "binance")
    """
    print(f"--- Tool: get_futures_open_orders called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper() if symbol and symbol.strip() else None
    if ':' not in symbol_normalized:
        return {
            "status": "error",
            "error_message": "交易对符号格式错误，请提供如'BTC/USDT:USDT'或'BTC/USDT:BTC'格式的交易对"
        }
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取合约未成交订单",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        params = {}
        if exchange_normalized == 'binance':
            params['portfolioMargin'] = True
        else:
            params['instType'] = 'SWAP'
        
        # 获取未成交订单
        if symbol_normalized:
            orders = exchange.fetch_open_orders(symbol_normalized, params=params)
        else:
            orders = exchange.fetch_open_orders(params=params)
        
        # 处理订单数据
        processed_orders = []
        for order in orders:
            processed_orders.append({
                "id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "filled": order['filled'],
                "remaining": order['remaining'],
                "timestamp": order['timestamp'],
                "datetime": order['datetime']
            })
        
        print(f"--- Tool: get_futures_open_orders completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "orders": processed_orders,
                "count": len(processed_orders)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_futures_open_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取合约未成交订单失败: {str(e)}"
        print(f"--- Tool: get_futures_open_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_futures_closed_orders(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取合约已成交订单列表。
    
    查询指定交易对或所有交易对的已完全成交的合约订单历史。
    用于分析合约交易记录、计算盈亏、统计交易表现。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE:QUOTE' 或 'BASE/QUOTE:BASE'，如'BTC/USDT:BTC'、'BTC/USDT:USDT'。传入空字符串表示获取所有持仓。'BTC/USDT:BTC'：指的是币本位合约，'BTC/USDT:USDT'：指的是U本位合约。
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含已成交订单信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单数据
                - orders (list): 已成交订单列表，每个元素包含：
                    - id (str): 订单ID
                    - symbol (str): 交易对符号
                    - side (str): 买卖方向
                    - amount (float): 订单数量
                    - price (float): 成交价格
                    - type (str): 订单类型
                    - status (str): 订单状态（通常为'closed'）
                    - filled (float): 已成交数量
                    - cost (float): 成交金额
                    - fee (dict): 手续费信息
                    - timestamp (int): 成交时间戳
                    - datetime (str): 格式化时间
                - count (int): 已成交订单总数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 获取BTC/USDT:USDT已成交合约订单
        >>> result = get_futures_closed_orders("BTC/USDT:USDT", "binance")
        >>> # 获取所有已成交合约订单
        >>> result = get_futures_closed_orders("", "binance")
    """
    print(f"--- Tool: get_futures_closed_orders called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper() if symbol and symbol.strip() else None
    if ':' not in symbol_normalized:
        return {
            "status": "error",
            "error_message": "交易对符号格式错误，请提供如'BTC/USDT:USDT'或'BTC/USDT:BTC'格式的交易对"
        }
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取合约已成交订单",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        params = {}
        if exchange_normalized == 'binance':
            params['portfolioMargin'] = True
        else:
            params['instType'] = 'SWAP'
        
        # 获取已成交订单
        if symbol_normalized:
            orders = exchange.fetch_closed_orders(symbol_normalized, params=params)
        else:
            orders = exchange.fetch_closed_orders(params=params)
        
        # 处理订单数据
        processed_orders = []
        for order in orders:
            processed_orders.append({
                "id": order['id'],
                "symbol": order['symbol'],
                "side": order['side'],
                "amount": order['amount'],
                "price": order['price'],
                "type": order['type'],
                "status": order['status'],
                "filled": order['filled'],
                "cost": order['cost'],
                "fee": order.get('fee', {}),
                "timestamp": order['timestamp'],
                "datetime": order['datetime']
            })
        
        print(f"--- Tool: get_futures_closed_orders completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "orders": processed_orders,
                "count": len(processed_orders)
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_futures_closed_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取合约已成交订单失败: {str(e)}"
        print(f"--- Tool: get_futures_closed_orders failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_futures_order_detail(order_id: str, symbol: str, exchange_name: str) -> Dict[str, Any]:
    """根据订单ID查询合约订单详情。
    
    查询指定订单ID的详细信息，包括订单状态、成交情况、手续费等完整信息。
    用于跟踪特定合约订单的执行情况和详细数据。
    
    Args:
        order_id (str): 订单ID，从下单或查询订单接口获取
        symbol (str): 交易对符号，格式为'BASE/QUOTE:QUOTE' 或 'BASE/QUOTE:BASE'，如'BTC/USDT:BTC'、'BTC/USDT:USDT'。传入空字符串表示获取所有持仓。'BTC/USDT:BTC'：指的是币本位合约，'BTC/USDT:USDT'：指的是U本位合约。
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含订单详情的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含订单详细数据
                - id (str): 订单ID
                - symbol (str): 交易对符号
                - side (str): 买卖方向
                - amount (float): 订单数量
                - price (float): 订单价格
                - average (float): 平均成交价格
                - type (str): 订单类型
                - status (str): 订单状态
                - filled (float): 已成交数量
                - remaining (float): 剩余数量
                - cost (float): 成交金额
                - fee (dict): 手续费详情
                - trades (list): 成交明细列表
                - timestamp (int): 下单时间戳
                - datetime (str): 格式化时间
                - lastTradeTimestamp (int): 最后成交时间戳
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_futures_order_detail("12345678", "BTC/USDT:USDT", "binance")
        >>> if result["status"] == "success":
        ...     order = result["data"]
        ...     print(f"合约订单状态: {order['status']}, 成交比例: {order['filled']}/{order['amount']}")
    """
    print(f"--- Tool: get_futures_order_detail called with order_id={order_id}, symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not order_id or not order_id.strip():
        return {
            "status": "error",
            "error_message": "订单ID不能为空"
        }
    
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT'格式的交易对"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    order_id_normalized = order_id.strip()
    symbol_normalized = symbol.strip().upper()
    if ':' not in symbol_normalized:
        return {
            "status": "error",
            "error_message": "交易对符号格式错误，请提供如'BTC/USDT:USDT'或'BTC/USDT:BTC'格式的交易对"
        }
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能查询合约订单详情",
                "metadata": {
                    "exchange": exchange_normalized,
                    "order_id": order_id_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        params = {}
        if exchange_normalized == 'binance':
            params['portfolioMargin'] = True
        else:
            pass
        
        order = exchange.fetch_order(order_id_normalized, symbol_normalized, params=params)
        
        # 处理订单数据
        order_detail = {
            "id": order['id'],
            "symbol": order['symbol'],
            "side": order['side'],
            "amount": order['amount'],
            "price": order['price'],
            "average": order.get('average'),
            "type": order['type'],
            "status": order['status'],
            "filled": order['filled'],
            "remaining": order['remaining'],
            "cost": order['cost'],
            "fee": order.get('fee', {}),
            "trades": order.get('trades', []),
            "timestamp": order['timestamp'],
            "datetime": order['datetime'],
            "lastTradeTimestamp": order.get('lastTradeTimestamp')
        }
        
        print(f"--- Tool: get_futures_order_detail completed successfully for order {order_id_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": order_detail,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_futures_order_detail failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"查询合约订单详情失败: {str(e)}"
        print(f"--- Tool: get_futures_order_detail failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }

def cancel_futures_order(order_id: str, symbol: str, exchange_name: str) -> Dict[str, Any]:
    """撤销合约交易订单。
    
    撤销指定的合约订单，适用于未完全成交的限价单。
    撤单后，未成交的部分将被取消，已成交部分不受影响。
    
    Args:
        order_id (str): 订单ID，从下单或查询订单接口获取
        symbol (str): 交易对符号，格式为'BASE/QUOTE:QUOTE' 或 'BASE/QUOTE:BASE'，如'BTC/USDT:BTC'、'BTC/USDT:USDT'。传入空字符串表示获取所有持仓。'BTC/USDT:BTC'：指的是币本位合约，'BTC/USDT:USDT'：指的是U本位合约。
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含撤单结果的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含撤单数据
                - order_id (str): 订单ID
                - symbol (str): 交易对符号
                - status (str): 撤单后的订单状态
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = cancel_futures_order("12345678", "BTC/USDT:USDT", "binance")
        >>> if result["status"] == "success":
        ...     print(f"合约订单 {result['data']['order_id']} 已成功撤销")
    """
    print(f"--- Tool: cancel_futures_order called with order_id={order_id}, symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not order_id or not order_id.strip():
        return {
            "status": "error",
            "error_message": "订单ID不能为空"
        }
    
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT'格式的交易对"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    order_id_normalized = order_id.strip()
    symbol_normalized = symbol.strip().upper()
    if ':' not in symbol_normalized:
        return {
            "status": "error",
            "error_message": "交易对符号格式错误，请提供如'BTC/USDT:USDT'或'BTC/USDT:BTC'格式的交易对"
        }
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能撤销合约订单",
                "metadata": {
                    "exchange": exchange_normalized,
                    "order_id": order_id_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        # 设置为合约模式
        params = {}
        if exchange_normalized == 'binance':
            params['portfolioMargin'] = True
        else:
            pass
        
        result = exchange.cancel_order(order_id_normalized, symbol_normalized, params=params)
        
        print(f"--- Tool: cancel_futures_order completed successfully for order {order_id_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "order_id": result['id'],
                "symbol": result['symbol'],
                "status": result['status']
            },
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: cancel_futures_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"撤销合约订单失败: {str(e)}"
        print(f"--- Tool: cancel_futures_order failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "order_id": order_id_normalized,
                "symbol": symbol_normalized
            }
        }

# ========== 余币宝理财功能 ==========

def get_savings_yield_by_asset(asset: str, exchange_name: str) -> Dict[str, Any]:
    """获取指定币种的余币宝年化收益率。
    
    查询指定交易所的指定币种的余币宝年化收益率。
    仅支持币安(Binance)和OKX交易所的余币宝功能。
    
    Args:
        asset (str): 币种名称，如'USDT'、'BTC'、'ETH'
        exchange_name (str): 交易所名称，仅支持'binance'和'okx'
    
    Returns:
        dict: 包含指定币种的余币宝年化收益率信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含年化收益率数据
                - yield (float): 年化收益率(小数形式)
            - error_message (str): 失败时的错误说明
    """
    print(f"--- Tool: get_savings_yield_by_asset called with asset={asset}, exchange_name={exchange_name} ---")
    
    result  = get_savings_products(exchange_name)

    if result["status"] == "success":
        for product in result["data"]["products"]:
            if product["asset"].upper() == asset.upper():
                return {
                    "status": "success",
                    "data": {"yield": product["rate"]}
                }
    return {
        "status": "error",
        "error_message": "获取余币宝年化收益率失败"
    }

def get_savings_products(exchange_name: str) -> Dict[str, Any]:
    """获取余币宝理财产品列表。
    
    查询指定交易所的可申购余币宝产品，包括年化收益率、申购限额等信息。
    仅支持币安(Binance)和OKX交易所的余币宝功能。
    
    Args:
        exchange_name (str): 交易所名称，仅支持'binance'和'okx'
        
    Returns:
        dict: 包含余币宝产品信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含产品数据
                - products (list): 产品列表，每个元素包含：
                    - asset/ccy (str): 币种名称
                    - avgAnnualInterestRate/rate (float): 年化收益率(小数形式)
                    - canPurchase (bool): 是否可申购（仅币安）
                    - canRedeem (bool): 是否可赎回（仅币安）
                    - minPurchaseAmount (float): 最小申购金额（仅币安）
                    - quota (float): 申购限额（仅OKX）
                - count (int): 产品数量
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_savings_products("binance")
        >>> if result["status"] == "success":
        ...     for product in result["data"]["products"]:
        ...         print(f"{product['asset']}: {product['avgAnnualInterestRate']}%")
    """
    print(f"--- Tool: get_savings_products called with exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    exchange_normalized = exchange_name.strip().lower()
    
    if exchange_normalized not in ['binance', 'okx']:
        return {
            "status": "error",
            "error_message": "余币宝功能仅支持币安(binance)和OKX(okx)交易所",
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取余币宝产品",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        if exchange_normalized == 'binance':
            try:
                # 币安余币宝产品
                products = exchange.sapi_get_simple_earn_flexible_list()

                processed_products = []
                for product in products['rows']:
                    processed_products.append({
                        "asset": product['asset'],
                        "rate": product.get('latestAnnualPercentageRate', 0),
                        "productId": product.get('productId', ''),
                    })
                
                print(f"--- Tool: get_savings_products completed successfully for {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "products": processed_products,
                        "count": len(processed_products)
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持币安余币宝API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized
                    }
                }
                
        elif exchange_normalized == 'okx':
            try:
                # OKX余币宝产品
                products = exchange.public_get_finance_savings_lending_rate_summary()
                
                processed_products = []
                for product in products.get('data', []):
                    processed_products.append({
                        "asset": product.get('ccy', ''),
                        "rate": product.get('preRate', 0),
                        "productId": product.get('ccy', '')
                    })
                
                print(f"--- Tool: get_savings_products completed successfully for {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "products": processed_products,
                        "count": len(processed_products)
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持OKX余币宝API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized
                    }
                }
        
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_savings_products failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取余币宝产品失败: {str(e)}"
        print(f"--- Tool: get_savings_products failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }

def redeem_savings_product(asset: str, amount: float, exchange_name: str) -> Dict[str, Any]:
    """赎回余币宝理财产品。
    
    在指定交易所赎回余币宝产品，将指定数量的币种从理财中取出。
    仅支持OKX交易所的余币宝功能。
    
    Args:
        asset (str): 币种名称，如'USDT'、'BTC'、'ETH'
        amount (float): 赎回金额，必须大于0且符合最小赎回限额
        exchange_name (str): 交易所名称，仅支持'okx'
        
    Returns:
        dict: 包含赎回结果的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含赎回数据
                - asset/ccy (str): 币种名称
                - amount/amt (float): 赎回金额
                - redeemId (str): 赎回ID（仅币安）
                - success (bool): 赎回是否成功（仅币安）
                - code (str): 响应代码（仅OKX）
                - msg (str): 响应消息（仅OKX）
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 赎回100 USDT余币宝
        >>> result = redeem_savings_product("USDT", 100, "binance")
        >>> if result["status"] == "success":
        ...     print(f"成功赎回 {result['data']['amount']} {result['data']['asset']}")
    """
    print(f"--- Tool: redeem_savings_product called with asset={asset}, amount={amount}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not asset or not asset.strip():
        return {
            "status": "error",
            "error_message": "币种名称不能为空，请提供如'USDT'、'BTC'等币种"
        }
    
    if not isinstance(amount, (int, float)) or amount <= 0: 
        return {
            "status": "error",
            "error_message": "赎回金额必须是大于0的数字"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    asset_normalized = asset.strip().upper()
    exchange_normalized = exchange_name.strip().lower()

    if exchange_normalized not in ['binance', 'okx']:
        return {
            "status": "error",
            "error_message": "余币宝功能仅支持币安(binance)和OKX(okx)交易所",
            "metadata": {
                "exchange": exchange_normalized,
                "asset": asset_normalized
            }
        }
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized) 
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能赎回余币宝",
                "metadata": {
                    "exchange": exchange_normalized,
                    "asset": asset_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        if exchange_normalized == 'binance':
            try:
                # 币安余币宝赎回
                # simple-earn/flexible/redeem
                result = exchange.sapi_post_simple_earn_flexible_redeem({
                    'productId': asset_normalized,
                    'amount': amount,
                    'autoSubscribe': False
                })

                print(f"--- Tool: redeem_savings_product completed successfully for {asset_normalized} on {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "asset": asset_normalized,  
                        "amount": amount,
                        "redeemId": result.get('redeemId', ''),
                        "success": result.get('success', False)
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持币安余币宝赎回API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized
                    }
                }
        
        elif exchange_normalized == 'okx':
            try:
                # OKX余币宝赎回
                # finance/savings/purchase-redempt
                result = exchange.private_post_finance_savings_purchase_redempt({
                    'ccy': asset_normalized,
                    'amt': str(amount),
                    'side': 'redempt'
                })
                
                print(f"--- Tool: redeem_savings_product completed successfully for {asset_normalized} on {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "ccy": asset_normalized,
                        "amt": amount,
                        "code": result.get('code', ''),
                        "msg": result.get('msg', ''),
                        "data": result.get('data', [])
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持币安余币宝赎回API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized
                    }
                }
        
    except ValueError as e: 
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: redeem_savings_product failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {   
                "exchange": exchange_normalized,
                "asset": asset_normalized
            }
        }
    except Exception as e:
        error_msg = f"赎回余币宝产品失败: {str(e)}" 
        print(f"--- Tool: redeem_savings_product failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "asset": asset_normalized
            }
        }

def purchase_savings_product(asset: str, amount: float, exchange_name: str) -> Dict[str, Any]:
    """申购余币宝理财产品。
    
    在指定交易所申购余币宝产品，将指定数量的币种投入理财获取收益。
    仅支持OKX交易所的余币宝功能。
    
    Args:
        asset (str): 币种名称，如'USDT'、'BTC'、'ETH'
        amount (float): 申购金额，必须大于0且符合最小申购限额
        exchange_name (str): 交易所名称，仅支持'okx'
        
    Returns:
        dict: 包含申购结果的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含申购数据
                - asset/ccy (str): 币种名称
                - amount/amt (float): 申购金额
                - purchaseId (str): 申购ID（仅币安）
                - success (bool): 申购是否成功（仅币安）
                - code (str): 响应代码（仅OKX）
                - msg (str): 响应消息（仅OKX）
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> # 申购100 USDT余币宝
        >>> result = purchase_savings_product("USDT", 100, "binance")
        >>> if result["status"] == "success":
        ...     print(f"成功申购 {result['data']['amount']} {result['data']['asset']}")
    """
    print(f"--- Tool: purchase_savings_product called with asset={asset}, amount={amount}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not asset or not asset.strip():
        return {
            "status": "error",
            "error_message": "币种名称不能为空，请提供如'USDT'、'BTC'等币种"
        }
    
    if not isinstance(amount, (int, float)) or amount <= 0:
        return {
            "status": "error",
            "error_message": "申购金额必须是大于0的数字"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    asset_normalized = asset.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    if exchange_normalized not in ['binance', 'okx']:
        return {
            "status": "error",
            "error_message": "余币宝功能仅支持币安(binance)和OKX(okx)交易所",
            "metadata": {
                "exchange": exchange_normalized,
                "asset": asset_normalized
            }
        }
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能申购余币宝",
                "metadata": {
                    "exchange": exchange_normalized,
                    "asset": asset_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        if exchange_normalized == 'binance':
            try:
                # 币安余币宝申购
                # simple-earn/flexible/subscribe
                # simple-earn/flexible/redeem
                result = exchange.sapi_post_simple_earn_flexible_subscribe({
                    'productId': asset_normalized,
                    'amount': amount,
                    'autoSubscribe': False
                })
                
                print(f"--- Tool: purchase_savings_product completed successfully for {asset_normalized} on {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "asset": asset_normalized,
                        "amount": amount,
                        "purchaseId": result.get('purchaseId', ''),
                        "success": result.get('success', False)
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持币安余币宝申购API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized
                    }
                }
                
        elif exchange_normalized == 'okx':
            try:
                # OKX余币宝申购
                # finance/savings/purchase-redempt
                result = exchange.private_post_finance_savings_purchase_redempt({
                    'ccy': asset_normalized,
                    'amt': str(amount),
                    'side': 'purchase',
                    'rate': 0.01,
                })
                
                print(f"--- Tool: purchase_savings_product completed successfully for {asset_normalized} on {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "ccy": asset_normalized,
                        "amt": amount,
                        "code": result.get('code', ''),
                        "msg": result.get('msg', ''),
                        "data": result.get('data', [])
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持OKX余币宝申购API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized,
                        "asset": asset_normalized
                    }
                }
        
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: purchase_savings_product failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "asset": asset_normalized
            }
        }
    except Exception as e:
        error_msg = f"申购余币宝产品失败: {str(e)}"
        print(f"--- Tool: purchase_savings_product failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "asset": asset_normalized
            }
        }

def get_savings_balance(exchange_name: str) -> Dict[str, Any]:
    """获取余币宝持仓情况。
    
    查询指定交易所的余币宝持仓详情，包括持有金额、累计收益等信息。
    仅支持币安(Binance)和OKX交易所的余币宝功能。
    
    Args:
        exchange_name (str): 交易所名称，仅支持'binance'和'okx'
        
    Returns:
        dict: 包含余币宝持仓信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含持仓数据
                - positions (list): 持仓列表，每个元素包含：
                    - asset/ccy (str): 币种名称
                    - productName (str): 产品名称（仅币安）
                    - totalAmount/amt (float): 持有总金额
                    - todayPurchasedAmount (float): 今日申购金额（仅币安）
                    - avgAnnualInterestRate/rate (float): 年化收益率
                    - earnings (float): 累计收益（仅OKX）
                    - canRedeem (bool): 是否可赎回（仅币安）
                - count (int): 持仓数量
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_savings_balance("binance")
        >>> if result["status"] == "success":
        ...     for position in result["data"]["positions"]:
        ...         print(f"{position['asset']}: {position['totalAmount']}")
    """
    print(f"--- Tool: get_savings_balance called with exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    exchange_normalized = exchange_name.strip().lower()
    
    if exchange_normalized not in ['binance', 'okx']:
        return {
            "status": "error",
            "error_message": "余币宝功能仅支持币安(binance)和OKX(okx)交易所",
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    
    try:
        # 从环境变量获取API凭据
        credentials = _get_api_credentials(exchange_normalized)
        api_key = credentials['api_key']
        secret = credentials['secret']
        password = credentials['password']
        
        if not api_key or not secret:
            return {
                "status": "error",
                "error_message": f"需要设置环境变量 {exchange_normalized.upper()}_API_KEY 和 {exchange_normalized.upper()}_SECRET 才能获取余币宝持仓",
                "metadata": {
                    "exchange": exchange_normalized
                }
            }
        
        exchange = _get_exchange(exchange_normalized, api_key, secret, password)
        
        if exchange_normalized == 'binance':
            try:
                # 币安余币宝持仓
                # simple-earn/flexible/position
                positions = exchange.sapi_get_simple_earn_flexible_position()
                
                processed_positions = []
                for position in positions['rows']:
                    processed_positions.append({
                        "asset": position.get('asset', ''),
                        "amount": position.get('totalAmount', 0),
                    })
                
                print(f"--- Tool: get_savings_balance completed successfully for {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "positions": processed_positions,
                        "count": len(processed_positions)
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持币安余币宝查询API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized
                    }
                }
                
        elif exchange_normalized == 'okx':
            try:
                # OKX余币宝持仓
                positions = exchange.private_get_finance_savings_balance()
                
                processed_positions = []
                for position in positions.get('data', []):
                    processed_positions.append({
                        "asset": position.get('ccy', ''),
                        "amount": position.get('amt', 0),
                        "total_earn": position.get('earnings', 0),
                        "rate": position.get('rate', 0)
                    })
                
                print(f"--- Tool: get_savings_balance completed successfully for {exchange_normalized} ---")
                
                return {
                    "status": "success",
                    "data": {
                        "positions": processed_positions,
                        "count": len(processed_positions)
                    },
                    "metadata": {
                        "exchange": exchange_normalized,
                        "timestamp": time.time()
                    }
                }
            except AttributeError:
                return {
                    "status": "error",
                    "error_message": "当前CCXT版本不支持OKX余币宝查询API，请使用官方API或升级CCXT版本",
                    "metadata": {
                        "exchange": exchange_normalized
                    }
                }
        
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_savings_balance failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取余币宝持仓失败: {str(e)}"
        print(f"--- Tool: get_savings_balance failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }

# ========== Agent 定义 ==========

crypto_trade_agent = Agent(
    name="crypto_trade_agent",
    model="gemini-2.5-flash-preview-05-20",
    description=(
        "专业的加密货币交易执行代理，负责在各大交易所执行具体的交易操作。支持现货交易、合约交易和理财产品管理。"
        "支持的交易所包括：Binance、OKX等主流交易所。"
        "核心功能：现货买卖、合约开仓平仓、订单管理、账户余额查询、余币宝理财产品操作。"
    ),
    instruction=(
        "你是一个专业的加密货币交易执行代理，专门负责执行各种交易操作。你的核心职责包括：\n\n"
        
        "## 现货交易功能\n"
        "- **get_spot_balance(exchange_name)**: 查询现货账户余额，显示各币种的可用、冻结和总余额\n"
        "- **place_spot_order(symbol, side, amount, price, exchange_name)**: 下现货订单\n"
        "  - symbol: 交易对如'BTC/USDT'\n"
        "  - side: 'buy'或'sell'\n"
        "  - amount: 交易数量\n"
        "  - price: 价格\n"
        "  - exchange_name: 交易所名称\n"
        "- **get_spot_orders(symbol, exchange_name)**: 查询现货订单历史，symbol传空字符串查询全部（仅 binance）\n"
        "- **get_spot_open_orders(symbol, exchange_name)**: 查询现货未成交订单\n"
        "- **get_spot_closed_orders(symbol, exchange_name)**: 查询现货已成交订单\n"
        "- **get_spot_order_detail(order_id, symbol, exchange_name)**: 查询现货订单详情\n"
        "- **cancel_spot_order(order_id, symbol, exchange_name)**: 撤销指定的现货订单\n\n"
        
        "## 合约交易功能\n"
        "- **get_futures_balance(exchange_name)**: 查询合约账户余额和保证金信息\n"
        "- **get_futures_positions(symbol, exchange_name)**: 查询合约持仓，symbol传空字符串查询全部\n"
        "- **place_futures_order(symbol, side, amount, price, exchange_name)**: 下合约订单，amount为币种数量\n"
        "  - symbol: 交易对如'BTC/USDT:USDT'\n"
        "  - side: 'open_long'或'open_short'或'close_long'或'close_short'\n"
        "  - amount: 币种数量\n"
        "  - price: 价格\n"
        "  - exchange_name: 交易所名称\n"
        "- **get_futures_open_orders(symbol, exchange_name)**: 查询合约未成交订单\n"
        "- **get_futures_closed_orders(symbol, exchange_name)**: 查询合约已成交订单\n"
        "- **get_futures_order_detail(order_id, symbol, exchange_name)**: 查询合约订单详情\n"
        "- **cancel_futures_order(order_id, symbol, exchange_name)**: 撤销指定的合约订单\n\n"
        
        "## 余币宝理财功能(仅支持Binance和OKX)\n"
        "- **get_savings_products(exchange_name)**: 获取可申购的余币宝理财产品列表，包括年化收益率\n"
        "- **purchase_savings_product(asset, amount, exchange_name)**: 申购余币宝理财产品，如申购USDT理财(仅OKX)\n"
        "- **redeem_savings_product(asset, amount, exchange_name)**: 赎回余币宝理财产品，如赎回USDT理财(仅OKX)\n"
        "- **get_savings_yield_by_asset(asset, exchange_name)**: 查询指定币种的余币宝理财年化收益率\n"
        "- **get_savings_balance(exchange_name)**: 查询当前余币宝理财持仓情况\n\n"
        
        "## 重要提醒\n"
        "1. **API凭据要求**: 所有交易操作都需要有效的API密钥，需要设置环境变量：\n"
        "2. **参数要求**: 所有函数都必须明确指定所有参数，不使用默认值\n"
        "3. **风险提示**: 执行交易前务必确认参数正确，交易有风险\n"
        "4. **错误处理**: 如遇到API错误，会返回详细的错误信息\n"
        "5. **支持的交易所**: binance、okx\n\n"
        
        "## 使用示例\n"
        "- 查询余额: get_spot_balance('binance')\n"
        "- 限价买入: place_spot_order('BTC/USDT', 'buy', 0.001, 30000, 'binance')\n"
        "- 限价卖出: place_spot_order('ETH/USDT', 'sell', 0.1, 3000, 'binance')\n"
        "- 申购理财: purchase_savings_product('USDT', 100, 'binance')\n"
        "- 查询所有现货订单（仅 binance）: get_spot_orders('', 'binance')\n"
        "- 查询未成交现货订单: get_spot_open_orders('', 'binance')\n"
        "- 查询已成交现货订单: get_spot_closed_orders('', 'binance')\n"
        "- 查询现货订单详情: get_spot_order_detail('12345678', 'BTC/USDT', 'binance')\n"
        "- 查询所有持仓: get_futures_positions('', 'binance')\n"
        "- 查询未成交合约订单: get_futures_open_orders('', 'binance')\n"
        "- 查询已成交合约订单: get_futures_closed_orders('', 'binance')\n"
        "- 查询合约订单详情: get_futures_order_detail('12345678', 'BTC/USDT:USDT', 'binance')\n"
        "- 撤销合约订单: cancel_futures_order('12345678', 'BTC/USDT:USDT', 'binance')\n\n"
        "- 合约开多: place_futures_order('ETH/USDT:USDT', 'open_long', 0.01, 2720, 'okx')\n"
        "- 合约平多: place_futures_order('ETH/USDT:USDT', 'close_long', 0.01, 2720, 'okx')\n"
        "- 合约开空: place_futures_order('ETH/USDT:USDT', 'open_short', 0.01, 2720, 'okx')\n"
        "- 合约平空: place_futures_order('ETH/USDT:USDT', 'close_short', 0.01, 2720, 'okx')\n"
        
        "你应该根据用户的交易需求，选择合适的工具执行操作，并清晰地解释每个操作的结果和风险。"
    ),
    tools=[
        # 现货交易功能
        get_spot_balance,
        place_spot_order,
        get_spot_orders,
        cancel_spot_order,
        get_spot_open_orders,
        get_spot_closed_orders,
        get_spot_order_detail,
        # 合约交易功能
        get_futures_balance,
        get_futures_positions,
        place_futures_order,
        get_futures_open_orders,
        get_futures_closed_orders,
        get_futures_order_detail,
        cancel_futures_order,
        # 余币宝功能
        get_savings_products,
        purchase_savings_product,
        redeem_savings_product,
        get_savings_yield_by_asset,
        get_savings_balance
    ]
) 

if __name__ == "__main__":
    for name in SUPPORTED_EXCHANGES.keys():
        r1 = get_spot_balance(name)
        print(r1)
        r2 = place_spot_order("ETH/USDT", "buy", 0.01, 2500, name)
        print(r2)
        r3 = get_spot_orders("ETH/USDT", name)
        print(r3)
        r4 = get_spot_open_orders("ETH/USDT", name)
        print(r4)
        r5 = get_spot_closed_orders("ETH/USDT", name)
        print(r5)
        r6 = get_spot_order_detail(r2['data']['order_id'], "ETH/USDT", name)
        print(r6)
        r7 = cancel_spot_order(r2['data']['order_id'], "ETH/USDT", name)
        print(r7)
    for name in SUPPORTED_EXCHANGES.keys():
        r1 = get_savings_balance(name)
        print(r1)
    for name in SUPPORTED_EXCHANGES.keys():
        r2 = get_savings_products(name)
        print(r2)
    for name in SUPPORTED_EXCHANGES.keys():
        r3 = get_savings_yield_by_asset('USDT', name)
        print(r3)
    r4 = purchase_savings_product("USDT", 100, 'okx')
    print(r4)
    r5 = redeem_savings_product('USDT', 100, 'okx')
    print(r5)
    for name in ['binance','okx']:
        r1 = get_futures_balance(name)
        print(r1)
        r2 = get_futures_positions("ETH/USDT:USDT", name)
        print(r2)
        r3 = place_futures_order("ETH/USDT:USDT", "open_long", 0.01, 2500, name)
        print(r3)
        r4 = get_futures_open_orders("ETH/USDT:USDT", name)
        print(r4)
        r5 = get_futures_closed_orders("ETH/USDT:USDT", name)
        print(r5)
        r6 = get_futures_order_detail(r3['data']['order_id'], "ETH/USDT:USDT", name)
        print(r6)
        r7 = cancel_futures_order(r3['data']['order_id'], "ETH/USDT:USDT", name)
        print(r7)
