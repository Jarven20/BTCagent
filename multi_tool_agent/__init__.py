"""
Multi-Tool Agent 包
一个基于 Google ADK 的多功能代理系统
"""

__version__ = "1.0.0"
__author__ = "Multi-Tool Agent Team"

# 导入主要组件
from .agent import root_agent, coordinator

__all__ = ['root_agent', 'coordinator']
