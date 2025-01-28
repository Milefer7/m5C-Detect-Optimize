#!/bin/bash

# ----------------- 配置项 -----------------
LOG_DIR="log"
LOG_FILE="${LOG_DIR}/monitor_$(date +'%Y-%m-%d_%H-%M').log" # 分钟级日志

# ----------------- 初始化 -----------------
mkdir -p "${LOG_DIR}"