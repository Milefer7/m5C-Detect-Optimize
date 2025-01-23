#!/bin/bash

# 设置 Conda 环境名称
ENV_NAME="asc04"

# 检查 Conda 环境是否存在
if conda env list | grep -q "$ENV_NAME"; then
    echo "环境 $ENV_NAME 已存在，正在激活..."
else
    echo "环境 $ENV_NAME 不存在，正在创建..."
    # 创建 Conda 环境
    conda env create -f environment.yml -n $ENV_NAME
fi

# 激活 Conda 环境
echo "激活环境 $ENV_NAME..."
source activate $ENV_NAME

# 检查环境是否成功激活
if [ $? -eq 0 ]; then
    echo "环境激活成功！"
else
    echo "环境激活失败！"
    exit 1
fi