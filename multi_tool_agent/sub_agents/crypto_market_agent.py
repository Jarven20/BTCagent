"""
加密货币市场数据代理 - 严格遵守ADK最佳实践

核心特性：
1. ✅ 移除所有默认参数值 - LLM无法理解默认值
2. ✅ 统一日志记录格式 - "--- Tool: function_name called/completed/failed ---"
3. ✅ 标准化返回值格式 - status/data/error_message/metadata结构
4. ✅ 完善错误处理和用户友好的错误消息
5. ✅ 详细的文档字符串，包含示例和参数说明
6. ✅ 输入验证和参数标准化
7. ✅ 移除复杂的批量函数，专注核心功能

核心工具函数（严格无默认参数）：
- get_ticker_data(symbol, exchange_name) - 获取实时价格数据
- get_orderbook_data(symbol, exchange_name, limit) - 获取订单簿深度
- get_kline_data(symbol, timeframe, exchange_name) - 获取K线数据
- get_market_overview(exchange_name) - 获取市场概览
- get_supported_exchanges() - 获取支持的交易所
- get_symbol_info(symbol, exchange_name) - 获取交易对信息
- get_trades_data(symbol, exchange_name, limit) - 获取市场公开最新成交记录


"""

import ccxt
import time
import logging
import os
import requests
import curl_cffi
import json
from typing import List, Dict, Any, Optional, Union
from google.adk.agents import Agent
from bs4 import BeautifulSoup
import dotenv
from datetime import datetime
# 设置日志
logger = logging.getLogger(__name__)


# 支持的交易所列表
SUPPORTED_EXCHANGES = {
    'binance': ccxt.binance,
    'okx': ccxt.okx
}

def _get_exchange(exchange_name: str, api_key: str = '', secret: str = '', password: str = '') -> ccxt.Exchange:
    """获取交易所实例
    
    Args:
        exchange_name (str): 交易所名称
        api_key (str): API密钥，用于私有操作
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
    
    exchange = exchange_class(config)
    return exchange

def get_ticker_data(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取指定交易对的实时价格数据。
    
    获取包括最新价格、买卖价差、24小时高低价、成交量等完整的ticker信息。
    适用于实时价格监控、价格提醒、市场分析等场景。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'、'ETH/USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含ticker数据的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含价格数据
                - last (float): 最新成交价格
                - bid (float): 买一价
                - ask (float): 卖一价  
                - high (float): 24小时最高价
                - low (float): 24小时最低价
                - volume (float): 24小时成交量
                - change (float): 24小时价格变化
                - percentage (float): 24小时涨跌幅百分比
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息，包含交易所和时间戳
    
    示例:
        >>> result = get_ticker_data("BTC/USDT", "binance")
        >>> if result["status"] == "success":
        ...     price = result["data"]["last"]
        ...     print(f"BTC当前价格: ${price}")
    """
    print(f"--- Tool: get_ticker_data called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
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
    
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        ticker = exchange.fetch_ticker(symbol_normalized)
        
        print(f"--- Tool: get_ticker_data completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "last": ticker['last'],
                "bid": ticker['bid'],
                "ask": ticker['ask'],
                "high": ticker['high'],
                "low": ticker['low'],
                "open": ticker['open'],
                "close": ticker['close'],
                "volume": ticker['baseVolume'],
                "quoteVolume": ticker['quoteVolume'],
                "change": ticker['change'],
                "percentage": ticker['percentage'],
                "timestamp": ticker['timestamp'],
                "datetime": ticker['datetime']
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或交易对: {str(e)}"
        print(f"--- Tool: get_ticker_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取价格数据失败: {str(e)}"
        print(f"--- Tool: get_ticker_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_orderbook_data(symbol: str, exchange_name: str, limit: int) -> Dict[str, Any]:
    """获取指定交易对的订单簿深度数据。
    
    获取买卖盘深度信息，用于分析市场流动性、支撑阻力位、价格影响等。
    深度数据显示不同价位的挂单数量，帮助判断市场买卖力量对比。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'、'ETH/USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        limit (int): 深度档位数量，建议10-100档，过多会影响响应速度
        
    Returns:
        dict: 包含订单簿数据的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含深度数据
                - bids (list): 买单深度，格式[[价格, 数量], ...]，按价格从高到低排序
                - asks (list): 卖单深度，格式[[价格, 数量], ...]，按价格从低到高排序
                - timestamp (int): 数据时间戳
                - datetime (str): 格式化时间
            - summary (dict): 深度摘要信息
                - sum_bid (float): 买单总数量
                - sum_ask (float): 卖单总数量
                - spread (float): 买卖价差
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_orderbook_data("BTC/USDT", "binance", 10)
        >>> if result["status"] == "success":
        ...     spread = result["summary"]["spread"]
        ...     print(f"当前买卖价差: ${spread}")
    """
    print(f"--- Tool: get_orderbook_data called with symbol={symbol}, exchange_name={exchange_name}, limit={limit} ---")
    
    # 输入验证
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
    
    if not isinstance(limit, int) or limit <= 0:
        return {
            "status": "error",
            "error_message": "深度档位数量必须是大于0的整数"
        }
    
    if limit > 100:
        return {
            "status": "error",
            "error_message": "深度档位数量不能超过100，建议使用5-50档"
        }
    
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        orderbook = exchange.fetch_order_book(symbol_normalized, limit)
        
        # 计算买卖价差
        spread = None
        if orderbook['bids'] and orderbook['asks']:
            spread = orderbook['asks'][0][0] - orderbook['bids'][0][0]
        
        print(f"--- Tool: get_orderbook_data completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "bids": orderbook['bids'][:limit],
                "asks": orderbook['asks'][:limit],
                "timestamp": orderbook['timestamp'],
                "datetime": orderbook['datetime'],
                "nonce": orderbook['nonce']
            },
            "summary": {
                "sum_bid": sum(bid[1] for bid in orderbook['bids']),
                "sum_ask": sum(ask[1] for ask in orderbook['asks']),
                "spread": spread
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "limit": limit,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或交易对: {str(e)}"
        print(f"--- Tool: get_orderbook_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取订单簿数据失败: {str(e)}"
        print(f"--- Tool: get_orderbook_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_trades_data(symbol: str, exchange_name: str, limit: int) -> Dict[str, Any]:
    """获取指定交易对的最近交易数据
    
    Args:
        symbol (str): 交易对符号，如 'BTC/USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        limit (int): 交易记录数量，建议10-100条
        
    Returns:
        Dict[str, Any]: 包含交易数据的字典
    """
    try:
        exchange = _get_exchange(exchange_name)
        trades = exchange.fetch_trades(symbol, limit=limit)
        
        # 处理交易数据
        processed_trades = []
        for trade in trades:
            processed_trades.append({
                "id": trade['id'],
                "price": trade['price'],
                "amount": trade['amount'],
                "side": trade['side'],  # 'buy' or 'sell'
                "timestamp": datetime.fromtimestamp(int(trade['timestamp'])/1000).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "status": "success",
            "exchange": exchange_name,
            "symbol": symbol,
            "data": {
                "trades": processed_trades,
                "count": len(processed_trades)
            },
            "summary": {
                "latest_price": processed_trades[0]['price'] if processed_trades else None,
                "latest_side": processed_trades[0]['side'] if processed_trades else None,
                "sum_buy": sum(trade['amount'] for trade in processed_trades if trade['side'] == 'buy'),
                "sum_sell": sum(trade['amount'] for trade in processed_trades if trade['side'] == 'sell'),
                "sum_volume": sum(trade['amount'] for trade in processed_trades)
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取 {exchange_name} 的 {symbol} 交易数据失败: {str(e)}")
        return {
            "status": "error",
            "exchange": exchange_name,
            "symbol": symbol,
            "error": str(e),
            "timestamp": time.time()
        }

def get_market_overview(exchange_name: str) -> Dict[str, Any]:
    """获取交易所市场概览信息。
    
    获取指定交易所的热门交易对和整体市场状况，用于了解市场趋势和热点。
    返回按成交额排序的前10个热门交易对及其基本信息。
    
    Args:
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含市场概览数据的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含市场数据
                - top_pairs (list): 热门交易对列表，每个元素包含：
                    - symbol (str): 交易对符号
                    - price (float): 当前价格
                    - change (float): 24小时价格变化
                    - percentage (float): 24小时涨跌幅百分比
                    - volume (float): 24小时成交量
                    - quoteVolume (float): 24小时成交额
                - total_pairs (int): 交易所总交易对数量
                - market_cap (float): 总市值（成交额总和）
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_market_overview("binance")
        >>> if result["status"] == "success":
        ...     top_pairs = result["data"]["top_pairs"]
        ...     for pair in top_pairs[:3]:
        ...         print(f"{pair['symbol']}: ${pair['price']} ({pair['percentage']}%)")
    """
    print(f"--- Tool: get_market_overview called with exchange_name={exchange_name} ---")
    
    # 输入验证
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        
        # 获取所有tickers
        tickers = exchange.fetch_tickers()
        
        # 按24h成交额排序，获取前10个热门交易对，仅包含USDT交易对
        sorted_tickers = sorted(
            [(symbol, ticker) for symbol, ticker in tickers.items() if symbol.endswith('/USDT')], 
            key=lambda x: x[1]['quoteVolume'] or 0, 
            reverse=True
        )[:10]
        
        market_data = []
        for symbol, ticker in sorted_tickers:
            market_data.append({
                "symbol": symbol,
                "price": ticker['last'],
                "change": ticker['change'],
                "percentage": ticker['percentage'],
                "volume": ticker['baseVolume'],
                "quoteVolume": ticker['quoteVolume']
            })
        
        # 计算总市值
        total_market_cap = sum(ticker.get('quoteVolume', 0) or 0 for ticker in tickers.values())
        
        print(f"--- Tool: get_market_overview completed successfully for {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "top_pairs": market_data,
                "total_pairs": len(tickers),
                "market_cap": total_market_cap
            },
            "metadata": {
                "exchange": exchange_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_market_overview failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取市场概览失败: {str(e)}"
        print(f"--- Tool: get_market_overview failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized
            }
        }

def get_supported_exchanges() -> Dict[str, Any]:
    """获取支持的交易所列表和功能信息。
    
    查询当前支持的所有交易所及其功能特性，帮助用户了解可用的交易所选项。
    包含每个交易所支持的API功能、速率限制等详细信息。
    
    Returns:
        dict: 包含支持的交易所信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含交易所信息
                - supported_exchanges (dict): 交易所详细信息，键为交易所名称
                    - name (str): 交易所全名
                    - id (str): 交易所标识符
                    - has_fetch_ticker (bool): 是否支持获取ticker数据
                    - has_fetch_order_book (bool): 是否支持获取订单簿
                    - has_fetch_trades (bool): 是否支持获取交易记录
                    - has_fetch_ohlcv (bool): 是否支持获取K线数据
                    - rate_limit (int): 请求速率限制（毫秒）
                - total_count (int): 支持的交易所总数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_supported_exchanges()
        >>> if result["status"] == "success":
        ...     exchanges = result["data"]["supported_exchanges"]
        ...     for name, info in exchanges.items():
        ...         print(f"{name}: {info['name']}")
    """
    print("--- Tool: get_supported_exchanges called ---")
    
    try:
        exchange_info = {}
        for name, exchange_class in SUPPORTED_EXCHANGES.items():
            try:
                exchange = exchange_class()
                exchange_info[name] = {
                    "name": exchange.name,
                    "id": exchange.id,
                    "has_fetch_ticker": exchange.has['fetchTicker'],
                    "has_fetch_order_book": exchange.has['fetchOrderBook'],
                    "has_fetch_trades": exchange.has['fetchTrades'],
                    "has_fetch_ohlcv": exchange.has.get('fetchOHLCV', False),
                    "rate_limit": exchange.rateLimit
                }
            except Exception as e:
                exchange_info[name] = {
                    "error": f"初始化失败: {str(e)}"
                }
        
        print("--- Tool: get_supported_exchanges completed successfully ---")
        
        return {
            "status": "success",
            "data": {
                "supported_exchanges": exchange_info,
                "total_count": len(SUPPORTED_EXCHANGES)
            },
            "metadata": {
                "timestamp": time.time()
            }
        }
    except Exception as e:
        error_msg = f"获取支持的交易所列表失败: {str(e)}"
        print(f"--- Tool: get_supported_exchanges failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "timestamp": time.time()
            }
        }

def get_symbol_info(symbol: str, exchange_name: str) -> Dict[str, Any]:
    """获取交易对的详细信息和交易规则。
    
    查询指定交易对在交易所的详细配置信息，包括交易精度、最小交易量、
    手续费率等重要参数，用于下单前的参数验证和风险控制。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'、'ETH/USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含交易对信息的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含交易对详细信息
                - id (str): 交易所内部标识符
                - base (str): 基础货币，如'BTC'
                - quote (str): 计价货币，如'USDT'
                - active (bool): 是否可交易
                - type (str): 市场类型，如'spot'
                - precision (dict): 价格和数量精度
                - limits (dict): 交易限制，包含最小/最大交易量
                - fees (dict): 手续费信息
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_symbol_info("BTC/USDT", "binance")
        >>> if result["status"] == "success":
        ...     precision = result["data"]["precision"]
        ...     print(f"价格精度: {precision['price']}位小数")
    """
    print(f"--- Tool: get_symbol_info called with symbol={symbol}, exchange_name={exchange_name} ---")
    
    # 输入验证
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
    
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        markets = exchange.load_markets()
        
        if symbol_normalized not in markets:
            return {
                "status": "error",
                "error_message": f"交易对 {symbol_normalized} 在 {exchange_normalized} 交易所不存在或已下线",
                "metadata": {
                    "exchange": exchange_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        market = markets[symbol_normalized]
        
        print(f"--- Tool: get_symbol_info completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "id": market['id'],
                "base": market['base'],
                "quote": market['quote'],
                "active": market['active'],
                "type": market['type'],
                "spot": market['spot'],
                "margin": market.get('margin', False),
                "future": market.get('future', False),
                "precision": market['precision'],
                "limits": market['limits'],
                "fees": market.get('fees', {}),
                "info": market.get('info', {})
            },
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所: {str(e)}"
        print(f"--- Tool: get_symbol_info failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取交易对信息失败: {str(e)}"
        print(f"--- Tool: get_symbol_info failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_kline_data(symbol: str, timeframe: str, exchange_name: str) -> Dict[str, Any]:
    """获取指定交易对的K线图表数据。
    
    获取OHLCV（开高低收量）数据，用于技术分析、趋势判断、图表绘制等。
    K线数据是技术分析的基础，包含价格走势和成交量信息。
    
    Args:
        symbol (str): 交易对符号，格式为'BASE/QUOTE'，如'BTC/USDT'、'ETH/USDT'
        timeframe (str): 时间周期，如'1m'、'5m'、'15m'、'1h'、'4h'、'1d'、'1w'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        
    Returns:
        dict: 包含K线数据的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含K线数据
                - klines (list): K线数据列表，每个元素包含：
                    - datetime (str): 格式化时间
                    - open (float): 开盘价
                    - high (float): 最高价
                    - low (float): 最低价
                    - close (float): 收盘价
                    - volume (float): 成交量
                - count (int): K线数量
            - summary (dict): 统计摘要
                - latest_price (float): 最新价格
                - price_change (float): 价格变化
                - price_change_percent (float): 涨跌幅百分比
                - highest_price (float): 期间最高价
                - lowest_price (float): 期间最低价
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_kline_data("BTC/USDT", "1d", "binance")
        >>> if result["status"] == "success":
        ...     latest = result["summary"]["latest_price"]
        ...     change = result["summary"]["price_change_percent"]
        ...     print(f"BTC价格: ${latest}, 涨跌幅: {change}%")
    """
    print(f"--- Tool: get_kline_data called with symbol={symbol}, timeframe={timeframe}, exchange_name={exchange_name} ---")
    
    # 输入验证
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "交易对符号不能为空，请提供如'BTC/USDT'格式的交易对"
        }
    
    if not timeframe or not timeframe.strip():
        return {
            "status": "error",
            "error_message": "时间周期不能为空，请提供如'1d'、'1h'等时间周期"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    symbol_normalized = symbol.strip().upper()
    timeframe_normalized = timeframe.strip().lower()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        
        # 检查交易所是否支持获取OHLCV数据
        if not exchange.has['fetchOHLCV']:
            return {
                "status": "error",
                "error_message": f"交易所 {exchange_normalized} 不支持获取K线数据",
                "metadata": {
                    "exchange": exchange_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        # 获取最近100条K线数据
        ohlcv = exchange.fetch_ohlcv(symbol_normalized, timeframe_normalized, None, 100)
        
        # 处理K线数据
        klines = []
        for candle in ohlcv:
            klines.append({
                # "timestamp": candle[0],
                "datetime": datetime.fromtimestamp(candle[0]/1000).strftime("%Y-%m-%d %H:%M:%S"),
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5]
            })
        
        # 计算统计数据
        summary = {}
        if klines:
            latest = klines[-1]
            first = klines[0]
            price_change = latest['close'] - first['open']
            price_change_percent = (price_change / first['open']) * 100 if first['open'] != 0 else 0
            
            summary = {
                "latest_price": latest['close'],
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "highest_price": max(k['high'] for k in klines),
                "lowest_price": min(k['low'] for k in klines),
                "total_volume": sum(k['volume'] for k in klines),
                "period_start": first['datetime'],
                "period_end": latest['datetime']
            }
        
        print(f"--- Tool: get_kline_data completed successfully for {symbol_normalized} {timeframe_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "klines": klines,
                "count": len(klines)
            },
            "summary": summary,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timeframe": timeframe_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或参数: {str(e)}"
        print(f"--- Tool: get_kline_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取K线数据失败: {str(e)}"
        print(f"--- Tool: get_kline_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_funding_rate(symbol: str, exchange_name: str, limit: int) -> Dict[str, Any]:
    """获取合约资金费率数据。
    
    获取永续合约的资金费率历史记录，用于分析市场情绪和多空力量对比。
    资金费率反映了多空双方的力量对比，正费率表示多头支付空头，负费率相反。
    
    Args:
        symbol (str): 合约交易对符号，格式为'BASE/QUOTE:SETTLE'，如'BTC/USDT:USDT'、'ETH/USDT:USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        limit (int): 获取的历史记录数量，建议10-100条，过多会影响响应速度
        
    Returns:
        dict: 包含资金费率数据的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含资金费率数据
                - funding_rates (list): 资金费率历史记录，每个元素包含：
                    - timestamp (int): 时间戳
                    - datetime (str): 格式化时间
                    - rate (float): 资金费率（小数形式，如0.0001表示0.01%）
                    - rate_percentage (float): 资金费率百分比形式
                - count (int): 记录数量
            - summary (dict): 统计摘要
                - current_rate (float): 当前资金费率
                - current_rate_percentage (float): 当前资金费率百分比
                - avg_rate (float): 平均资金费率
                - max_rate (float): 最高资金费率
                - min_rate (float): 最低资金费率
                - positive_count (int): 正费率次数
                - negative_count (int): 负费率次数
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_funding_rate_history("BTC/USDT:USDT", "binance", 24)
        >>> if result["status"] == "success":
        ...     current_rate = result["summary"]["current_rate_percentage"]
        ...     print(f"BTC当前资金费率: {current_rate}%")
    """
    print(f"--- Tool: get_funding_rate_history called with symbol={symbol}, exchange_name={exchange_name}, limit={limit} ---")
    
    # 输入验证
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "合约交易对符号不能为空，请提供如'BTC/USDT:USDT'格式的合约交易对"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    if not isinstance(limit, int) or limit <= 0:
        return {
            "status": "error",
            "error_message": "历史记录数量必须是大于0的整数"
        }
    
    if limit > 100:
        return {
            "status": "error",
            "error_message": "历史记录数量不能超过100，建议使用10-50条"
        }
    
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        
        # 检查交易所是否支持获取资金费率
        if not exchange.has.get('fetchFundingRateHistory', False):
            return {
                "status": "error",
                "error_message": f"交易所 {exchange_normalized} 不支持获取资金费率历史数据",
                "metadata": {
                    "exchange": exchange_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        # 获取资金费率历史
        funding_rates = exchange.fetch_funding_rate_history(symbol_normalized, None, limit)
        
        # 处理资金费率数据
        processed_rates = []
        for rate in funding_rates:
            rate_value = rate['fundingRate'] if rate['fundingRate'] is not None else 0
            processed_rates.append({
                "timestamp": rate['timestamp'],
                "datetime": rate['datetime'],
                "rate": rate_value,
                "rate_percentage": rate_value * 100
            })
        
        # 计算统计数据
        summary = {}
        if processed_rates:
            rates = [r['rate'] for r in processed_rates if r['rate'] is not None]
            if rates:
                current_rate = processed_rates[-1]['rate']
                summary = {
                    "current_rate": current_rate,
                    "current_rate_percentage": current_rate * 100,
                    "avg_rate": sum(rates) / len(rates),
                    "max_rate": max(rates),
                    "min_rate": min(rates),
                    "positive_count": len([r for r in rates if r > 0]),
                    "negative_count": len([r for r in rates if r < 0]),
                    "zero_count": len([r for r in rates if r == 0])
                }
        
        print(f"--- Tool: get_funding_rate_history completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "funding_rates": processed_rates,
                "count": len(processed_rates)
            },
            "summary": summary,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "limit": limit,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或合约交易对: {str(e)}"
        print(f"--- Tool: get_funding_rate_history failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取资金费率历史失败: {str(e)}"
        print(f"--- Tool: get_funding_rate_history failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_open_interest_data(symbol: str, exchange_name: str, timeframe: str) -> Dict[str, Any]:
    """获取合约持仓量数据。
    
    获取永续合约或期货合约的未平仓合约数量历史数据，用于分析市场参与度和趋势强度。
    持仓量增加通常表示新资金进入，持仓量减少可能表示获利了结或止损。
    
    Args:
        symbol (str): 合约交易对符号，格式为'BASE/QUOTE:SETTLE'，如'BTC/USDT:USDT'、'ETH/USDT:USDT'
        exchange_name (str): 交易所名称，支持'binance'、'okx'
        timeframe (str): 时间周期，如'5m'、'15m'、'1h'、'4h'、'1d'
        
    Returns:
        dict: 包含持仓量数据的字典
            - status (str): 'success'表示成功，'error'表示失败
            - data (dict): 成功时包含持仓量数据
                - open_interest_history (list): 持仓量历史记录，每个元素包含：
                    - timestamp (int): 时间戳
                    - datetime (str): 格式化时间
                    - open_interest (float): 持仓量（合约张数或币数）
                    - open_interest_value (float): 持仓量价值（USDT）
                - count (int): 记录数量
            - summary (dict): 统计摘要
                - current_oi (float): 当前持仓量
                - current_oi_value (float): 当前持仓量价值
                - oi_change (float): 持仓量变化
                - oi_change_percentage (float): 持仓量变化百分比
                - max_oi (float): 最大持仓量
                - min_oi (float): 最小持仓量
                - avg_oi (float): 平均持仓量
            - error_message (str): 失败时的错误说明
            - metadata (dict): 元信息
    
    示例:
        >>> result = get_open_interest_data("BTC/USDT:USDT", "binance", "1h")
        >>> if result["status"] == "success":
        ...     current_oi = result["summary"]["current_oi"]
        ...     change_pct = result["summary"]["oi_change_percentage"]
        ...     print(f"BTC持仓量: {current_oi}, 变化: {change_pct}%")
    """
    print(f"--- Tool: get_open_interest_data called with symbol={symbol}, exchange_name={exchange_name}, timeframe={timeframe} ---")
    
    # 输入验证
    if not symbol or not symbol.strip():
        return {
            "status": "error",
            "error_message": "合约交易对符号不能为空，请提供如'BTC/USDT:USDT'格式的合约交易对"
        }
    
    if not exchange_name or not exchange_name.strip():
        return {
            "status": "error",
            "error_message": "交易所名称不能为空，请提供支持的交易所名称"
        }
    
    if not timeframe or not timeframe.strip():
        return {
            "status": "error",
            "error_message": "时间周期不能为空，请提供如'1h'、'4h'等时间周期"
        }
    
    symbol_normalized = symbol.strip().upper()
    exchange_normalized = exchange_name.strip().lower()
    timeframe_normalized = timeframe.strip().lower()
    
    try:
        exchange = _get_exchange(exchange_normalized)
        
        # 检查交易所是否支持获取持仓量历史
        if not exchange.has.get('fetchOpenInterestHistory', False):
            return {
                "status": "error",
                "error_message": f"交易所 {exchange_normalized} 不支持获取持仓量历史数据",
                "metadata": {
                    "exchange": exchange_normalized,
                    "symbol": symbol_normalized
                }
            }
        
        # 获取持仓量历史数据（最近100条）
        oi_history = exchange.fetch_open_interest_history(symbol_normalized, timeframe_normalized, None, 100)
        
        # 处理持仓量数据
        processed_oi = []
        for oi in oi_history:
            processed_oi.append({
                "timestamp": oi['timestamp'],
                "datetime": oi['datetime'],
                "open_interest": oi['openInterestAmount'],
                "open_interest_value": oi['openInterestValue']
            })
        
        # 计算统计数据
        summary = {}
        if processed_oi:
            oi_amounts = [oi['open_interest'] for oi in processed_oi if oi['open_interest'] is not None]
            if oi_amounts and len(oi_amounts) >= 2:
                current_oi = processed_oi[-1]['open_interest']
                previous_oi = processed_oi[0]['open_interest']
                oi_change = current_oi - previous_oi
                oi_change_percentage = (oi_change / previous_oi) * 100 if previous_oi != 0 else 0
                
                summary = {
                    "current_oi": current_oi,
                    "current_oi_value": processed_oi[-1]['open_interest_value'],
                    "oi_change": oi_change,
                    "oi_change_percentage": oi_change_percentage,
                    "max_oi": max(oi_amounts),
                    "min_oi": min(oi_amounts),
                    "avg_oi": sum(oi_amounts) / len(oi_amounts),
                    "period_start": processed_oi[0]['datetime'],
                    "period_end": processed_oi[-1]['datetime']
                }
        
        print(f"--- Tool: get_open_interest_data completed successfully for {symbol_normalized} on {exchange_normalized} ---")
        
        return {
            "status": "success",
            "data": {
                "open_interest_history": processed_oi,
                "count": len(processed_oi)
            },
            "summary": summary,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized,
                "timeframe": timeframe_normalized,
                "timestamp": time.time()
            }
        }
    except ValueError as e:
        error_msg = f"不支持的交易所或合约交易对: {str(e)}"
        print(f"--- Tool: get_open_interest_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }
    except Exception as e:
        error_msg = f"获取持仓量数据失败: {str(e)}"
        print(f"--- Tool: get_open_interest_data failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
            "metadata": {
                "exchange": exchange_normalized,
                "symbol": symbol_normalized
            }
        }

def get_coin_introduction_by_whitepaper(coin_name: str) -> dict:
    """获取指定币种的深入分析信息（白皮书摘要）。

    通过白皮书摘要获取币种的深入分析信息，包括技术特点、团队背景、
    代币经济模型、发展路线图等专业分析内容。适用于需要了解币种基本面、项目背景、
    技术特点和发展历程的深度研究场景。

    Args:
        coin_name (str): 币种名称，使用英文名称（如"bitcoin"、"ethereum"）

    Returns:
        dict: 包含币种深度分析信息的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含币种深度分析信息
                - tldr (str): 专家分析内容
                - technology (str): 技术特点
                - team (str): 团队背景
                - tokenomics (str): 代币经济模型
                - roadmap (str): 发展路线图
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含数据来源、获取时间等

    示例:
        >>> result = get_coin_introduction_by_whitepaper("bitcoin")
        >>> if result["status"] == "success":
        ...     tldr = result["data"]["tldr"]
        ...     print(f"比特币专家分析: {tldr[:100]}...")
    """
    # 记录工具调用
    print(f"--- Tool: get_coin_introduction_by_whitepaper called with coin_name={coin_name} ---")
    
    # 输入验证和标准化
    if not coin_name or not isinstance(coin_name, str):
        return {
            "status": "error",
            "error_message": "币种名称不能为空且必须是字符串"
        }
    
    coin_name_normalized = coin_name.strip().lower()
    
    if not coin_name_normalized:
        return {
            "status": "error",
            "error_message": "币种名称不能为空"
        }
    
    print(f"--- Tool: get_coin_introduction_by_whitepaper normalized coin_name: {coin_name_normalized} ---")
    
    try:
        # 构建API URL
        url = f"https://s3.coinmarketcap.com/whitepaper/summaries/{coin_name_normalized}/en.json"
        
        print(f"--- Tool: get_coin_introduction_by_whitepaper making request to: {url} ---")
        
        # 发送请求
        response = curl_cffi.get(url, timeout=30, verify=True, impersonate='chrome')
        
        # 检查HTTP状态码
        if response.status_code == 404:
            return {
                "status": "error",
                "error_message": f"未找到币种 '{coin_name}' 的白皮书摘要信息，请检查币种名称是否正确"
            }
        elif response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"获取币种白皮书信息失败，HTTP状态码: {response.status_code}"
            }
        
        # 解析JSON响应
        try:
            api_data = response.json()
        except ValueError as e:
            return {
                "status": "error",
                "error_message": f"解析API响应失败: {str(e)}"
            }
        
        # 提取专家分析数据
        expert_data = api_data.get('expert', {})
        
        if not expert_data:
            return {
                "status": "error",
                "error_message": f"币种 '{coin_name}' 暂无白皮书摘要分析数据"
            }
        
        # 构建币种深度分析数据
        coin_analysis = {
            "coin_name": coin_name_normalized,
            "tldr": expert_data.get('tldr', ''),
            "technology": expert_data.get('technology', ''),
            "team": expert_data.get('team', ''),
            "tokenomics": expert_data.get('tokenomics', ''),
            "roadmap": expert_data.get('roadmap', ''),
        }
        
        # 构建元数据
        metadata = {
            "timestamp": time.time(),
            "data_source": "CoinMarketCap Whitepaper Summaries API",
            "source_url": url,
            "requested_coin": coin_name,
            "response_status_code": response.status_code,
            "data_completeness": {
                "has_tldr": bool(coin_analysis["tldr"]),
                "has_technology": bool(coin_analysis["technology"]),
                "has_team": bool(coin_analysis["team"]),
                "has_tokenomics": bool(coin_analysis["tokenomics"]),
                "has_roadmap": bool(coin_analysis["roadmap"])
            }
        }
        
        # 记录成功结果
        print(f"--- Tool: get_coin_introduction_by_whitepaper completed successfully - coin='{coin_name_normalized}' ---")
        
        return {
            "status": "success",
            "data": coin_analysis,
            "metadata": metadata
        }
        
    except requests.exceptions.Timeout:
        error_msg = "请求超时（30秒），请稍后重试"
        print(f"--- Tool: get_coin_introduction_by_whitepaper failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except requests.exceptions.ConnectionError:
        error_msg = "无法连接到CoinMarketCap API，请检查网络连接"
        print(f"--- Tool: get_coin_introduction_by_whitepaper failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except Exception as e:
        error_msg = f"获取币种白皮书摘要时发生未知错误: {str(e)}"
        print(f"--- Tool: get_coin_introduction_by_whitepaper failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

def get_coin_introduction(coin_name: str) -> dict:
    """获取指定币种的基本介绍信息。

    获取币种的基本信息和项目介绍。
    适用于快速了解币种基本概念、项目背景和核心特点的场景。

    Args:
        coin_name (str): 币种名称，使用英文名称（如"bitcoin"、"ethereum"）

    Returns:
        dict: 包含币种介绍信息的字典，具有以下结构：
            - status (str): 'success' 或 'error'
            - data (dict): 成功时包含币种详细信息
                - coin_name (str): 币种名称
                - introduction (str): 项目介绍
            - error_message (str): 错误时的详细说明
            - metadata (dict): 元信息，包含数据来源、获取时间等

    示例:
        >>> result = get_coin_introduction("bitcoin")
        >>> if result["status"] == "success":
        ...     intro = result["data"]["introduction"]
        ...     print(f"比特币介绍: {intro[:100]}...")
    """
    # 记录工具调用
    print(f"--- Tool: get_coin_introduction called with coin_name={coin_name} ---")
    
    # 输入验证和标准化
    if not coin_name or not isinstance(coin_name, str):
        return {
            "status": "error",
            "error_message": "币种名称不能为空且必须是字符串"
        }
    
    coin_name_normalized = coin_name.strip().lower()
    
    if not coin_name_normalized:
        return {
            "status": "error",
            "error_message": "币种名称不能为空"
        }
    
    print(f"--- Tool: get_coin_introduction normalized coin_name: {coin_name_normalized} ---")
    
    try:
        # 构建URL
        url = f"https://www.coinmarketcap.com/currencies/{coin_name_normalized}/"
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"--- Tool: get_coin_introduction making request to: {url} ---")
        
        # 发送请求
        response = curl_cffi.get(url, headers=headers, timeout=30, verify=True, impersonate='chrome')
        
        # 检查HTTP状态码
        if response.status_code == 404:
            return {
                "status": "error",
                "error_message": f"未找到币种 '{coin_name}' 的信息，请检查币种名称是否正确"
            }
        elif response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"获取币种信息失败，HTTP状态码: {response.status_code}"
            }
        
        # 解析HTML - 处理编码问题
        try:
            # 尝试检测和设置正确的编码
            response.encoding = response.apparent_encoding or 'utf-8'
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            # 如果编码有问题，尝试使用原始字节内容
            try:
                soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            except Exception as e2:
                return {
                    "status": "error",
                    "error_message": f"解析网页内容失败: {str(e2)}"
                }
        
        # 提取币种基本信息
        coin_data = {
            "coin_name": coin_name_normalized,
            "introduction": "",
        }
        
        try:
            # 查找包含 __NEXT_DATA__ 的script标签
            scripts = soup.find_all('script')
            next_data = None
            
            for script in scripts:
                if script.get('id') == '__NEXT_DATA__':
                    next_data = json.loads(script.string)
                    page_props = next_data.get('props', {}).get('pageProps', {})
                    faq_data = page_props.get('cdpFaqData', {})
                    coin_data["introduction"] = faq_data.get('faqDescription', '')
                    break
        except Exception as e:
            print(f"--- Tool: get_coin_introduction warning - failed to extract NEXT_DATA: {str(e)} ---")
 
        # 构建元数据
        metadata = {
            "timestamp": time.time(),
            "data_source": "CoinMarketCap (coinmarketcap.com)",
            "source_url": url,
            "requested_coin": coin_name,
            "response_status_code": response.status_code,
            "data_completeness": {
                "has_introduction": bool(coin_data["introduction"]),
            }
        }
        
        # 记录成功结果
        print(f"--- Tool: get_coin_introduction completed successfully - coin='{coin_data.get('coin_name', coin_name)}' ---")
        
        return {
            "status": "success",
            "data": coin_data,
            "metadata": metadata
        }
        
    except requests.exceptions.Timeout:
        error_msg = "请求超时（30秒），请稍后重试"
        print(f"--- Tool: get_coin_introduction failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except requests.exceptions.ConnectionError:
        error_msg = "无法连接到CoinMarketCap网站，请检查网络连接"
        print(f"--- Tool: get_coin_introduction failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except Exception as e:
        error_msg = f"获取币种介绍时发生未知错误: {str(e)}"
        print(f"--- Tool: get_coin_introduction failed - {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg
        }

# 创建加密货币市场数据 agent
crypto_market_agent = Agent(
    name="crypto_market_agent",
    model="gemini-2.5-flash-preview-05-20",
    description=(
        "专业的加密货币市场数据分析代理，专注于从各大交易所获取实时市场数据并提供深度技术分析。"
        "支持获取价格数据、深度订单簿、交易记录、K线图表、市场概览、合约资金费率、持仓量等多维度数据。"
        "同时提供币种基本面信息查询，包括项目介绍和白皮书摘要分析。"
        "能够进行技术分析，识别支撑阻力位、图表形态、趋势分析等，为交易决策提供数据支持。"
        "支持的交易所：Binance、OKX、Bybit、Bitget、Gate.io等主流交易所。"
    ),
    instruction=(
        "你是一个专业的加密货币市场数据分析师，专门负责获取和分析市场数据。你的核心能力包括：\n\n"
        
        "## 实时价格数据获取\n"
        "- **get_ticker_data(symbol, exchange_name)**: 获取指定交易对的实时价格数据\n"
        "  - 包含：最新价、买一卖一价、24h高低价、成交量、涨跌幅等\n"
        "  - 示例: get_ticker_data('BTC/USDT', 'binance')\n"
        "  - 如需多个交易对数据，请多次调用此函数\n\n"
        
        "## 深度数据分析\n"
        "- **get_orderbook_data(symbol, exchange_name, limit)**: 获取订单簿深度数据\n"
        "  - 分析买卖盘力量对比，识别支撑阻力位\n"
        "  - 计算买卖价差，评估流动性\n"
        "  - limit建议使用10-100档\n\n"

        "## 市场最新成交记录\n"
        "- **get_trades_data(symbol, exchange_name, limit)**: 获取市场公开最新成交记录\n"
        "  - 包含：成交时间、价格、数量、方向等\n"
        "  - 示例: get_trades_data('BTC/USDT', 'binance', 100)\n"
        "  - 如需多个交易对数据，请多次调用此函数\n\n"
        
        "## K线图表分析\n"
        "- **get_kline_data(symbol, timeframe, exchange_name)**: 获取K线数据\n"
        "  - 支持时间周期：1m, 5m, 15m, 1h, 4h, 1d, 1w等\n"
        "  - 包含OHLCV数据：开盘价、最高价、最低价、收盘价、成交量\n"
        "  - 自动计算价格变化和统计数据\n"
        "  - 返回最近100条K线数据\n\n"
        
        "## 合约数据分析\n"
        "- **get_funding_rate_history(symbol, exchange_name, limit)**: 获取合约资金费率历史\n"
        "  - 分析多空力量对比和市场情绪\n"
        "  - 包含当前和历史资金费率数据\n"
        "  - 示例: get_funding_rate_history('BTC/USDT:USDT', 'binance', 24)\n"
        "- **get_open_interest_data(symbol, exchange_name, timeframe)**: 获取合约持仓量数据\n"
        "  - 分析市场参与度和趋势强度\n"
        "  - 持仓量变化反映资金流入流出\n"
        "  - 示例: get_open_interest_data('BTC/USDT:USDT', 'binance', '1h')\n\n"
        
        "## 币种基本面信息查询\n"
        "- **get_coin_introduction(coin_name)**: 获取币种基本介绍信息\n"
        "  - 获取项目基本介绍\n"
        "  - 适用于快速了解币种基本概念和背景\n"
        "  - 示例: get_coin_introduction('bitcoin')\n"
        "- **get_coin_introduction_by_whitepaper(coin_name)**: 获取币种深度分析信息\n"
        "  - 通过白皮书摘要获取专业分析内容\n"
        "  - 包含技术特点、团队背景、代币经济模型、发展路线图等\n"
        "  - 适用于深度研究和基本面分析\n"
        "  - 示例: get_coin_introduction_by_whitepaper('ethereum')\n\n"
        
        "## 市场概览分析\n"
        "- **get_market_overview(exchange_name)**: 获取交易所市场概览信息\n"
        "  - 获取指定交易所的热门交易对和整体市场状况\n"
        "  - 返回按成交额排序的前10个热门交易对\n"
        "- **get_symbol_info(symbol, exchange_name)**: 获取交易对详细信息\n"
        "  - 交易精度、最小交易量、手续费等\n"
        "- **get_supported_exchanges()**: 查看支持的交易所列表和功能\n\n"
        
        "## 技术分析能力\n"
        "基于获取的数据，你能够进行：\n"
        "1. **趋势分析**: 识别上升、下降或横盘趋势\n"
        "2. **支撑阻力位分析**: 从K线和深度数据识别关键价位\n"
        "3. **图表形态识别**: 头肩顶底、双顶双底、三角形等经典形态\n"
        "4. **成交量分析**: 量价关系分析，确认趋势强度\n"
        "5. **市场情绪分析**: 从订单簿和交易数据判断市场情绪\n"
        "6. **合约分析**: 资金费率和持仓量分析，判断多空力量对比\n"
        "7. **基本面分析**: 结合项目介绍和白皮书分析，评估长期价值\n"
        "8. **币种名称**: 币种查询使用英文小写名称，如'bitcoin'、'ethereum'\n\n"
        
        "## 使用示例\n"
        "- 获取BTC价格: get_ticker_data('BTC/USDT', 'binance')\n"
        "- 分析4h线趋势: get_kline_data('ETH/USDT', '4h', 'binance')\n"
        "- 查看市场深度: get_orderbook_data('BTC/USDT', 'binance', 20)\n"
        "- 获取市场概览: get_market_overview('binance')\n"
        "- 获取市场最新成交记录: get_trades_data('BTC/USDT', 'binance', 100)\n"
        "- 分析资金费率: get_funding_rate_history('BTC/USDT:USDT', 'binance', 24)\n"
        "- 查看持仓量: get_open_interest_data('BTC/USDT:USDT', 'binance', '1h')\n"
        "- 了解项目基础: get_coin_introduction('bitcoin')\n"
        "- 深度项目分析: get_coin_introduction_by_whitepaper('ethereum')\n\n"
        
        "## 重要提醒\n"
        "1. **参数要求**: 所有函数都需要明确指定所有参数，不使用默认值\n"
        "2. **数据驱动**: 基于真实市场数据进行分析\n"
        "3. **多维度分析**: 结合价格、成交量、深度、资金费率、持仓量、基本面等多个维度\n"
        "4. **风险提示**: 技术分析仅供参考，投资需谨慎\n"
        "5. **及时更新**: 市场变化快速，建议获取最新数据\n"
        "6. **合约注意**: 合约交易对格式为'BASE/QUOTE:SETTLE'，如'BTC/USDT:USDT'\n"
        "7. **币种名称**: 币种查询使用英文小写名称，如'bitcoin'、'ethereum'\n\n"
        
        "你应该根据用户的需求，选择合适的数据获取工具，并提供专业的技术分析和市场洞察。"
        "对于投资决策，建议结合技术分析和基本面分析，提供全面的市场视角。"
    ),
    tools=[
        get_ticker_data,
        get_orderbook_data,
        get_kline_data,
        get_market_overview,
        get_trades_data,
        get_supported_exchanges,
        get_symbol_info,
        get_funding_rate,
        get_open_interest_data,
        get_coin_introduction_by_whitepaper,
        get_coin_introduction,
    ],
) 

if __name__ == "__main__":
    for name in SUPPORTED_EXCHANGES.keys():
    #     r1 = get_ticker_data("BTC/USDT", name)
    #     print(r1)
    #     r2 = get_orderbook_data("BTC/USDT", name, 10)
    #     print(r2)
        # r3 = get_trades_data("BTC/USDT", name, 10)
        # print(r3)
        r4 = get_kline_data("BTC/USDT", "4h", name)
        print(r4)
    #     r5 = get_market_overview(name)
    #     print(r5)
    #     r6 = get_supported_exchanges()
    #     print(r6)
    #     r7 = get_symbol_info("BTC/USDT", name)
    #     print(r7)
    #     r8 = get_funding_rate("BTC/USDT:USDT", name, 24)
    #     print(r8)
    #     r9 = get_open_interest_data("BTC/USDT:USDT", name, "1h")
    #     print(r9)

    # 测试币种信息获取函数
    # print("\n=== 测试币种信息获取函数 ===")
    # r10 = get_coin_introduction("bitcoin")
    # print("Bitcoin Introduction:", r10)
    
    # r11 = get_coin_introduction_by_whitepaper("bitcoin")
    # print("Bitcoin Whitepaper Analysis:", r11)
