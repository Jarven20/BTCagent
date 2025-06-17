#!/bin/bash

# 激活Python虚拟环境
echo "正在激活虚拟环境..."
source .venv/bin/activate

# 设置代理环境变量
echo "正在设置代理..."
export https_proxy=http://127.0.0.1:7890 
export http_proxy=http://127.0.0.1:7890 
export all_proxy=socks5://127.0.0.1:7890

# 启动adk web
echo "正在启动adk web..."
adk web 