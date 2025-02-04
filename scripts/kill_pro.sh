#!/bin/bash

sudo_password=$(yq -r '.sudo_password' ~/.config/config.yml)
# echo $sudo_password

# 获取 atop 进程的 PID，排除自身的 grep 进程
atop_pids=$(ps aux | grep '[a]top' | awk '{print $2}')

# 获取 monitor.sh 进程的 PID，排除自身的 grep 进程
monitor_pids=$(ps aux | grep '[m]onitor.sh' | awk '{print $2}')

# 检查是否获取到 PID
if [ -z "$atop_pids" ]; then
    echo "未找到 atop 进程。"
else
    echo "找到 atop 进程，PID(s): $atop_pids"
fi

if [ -z "$monitor_pids" ]; then
    echo "未找到 monitor.sh 进程。"
else
    echo "找到 monitor.sh 进程，PID(s): $monitor_pids"
fi

# 延时 60 分钟（3600 秒）
sleep 7200

# 使用 sudo 杀死进程
if [ -n "$atop_pids" ]; then
    echo "正在杀死 atop 进程..."
    echo "$sudo_password" | sudo -S kill -15 $atop_pids
fi

if [ -n "$monitor_pids" ]; then
    echo "正在杀死 monitor.sh 进程..."
    echo "$sudo_password" | sudo -S kill -15 $monitor_pids
fi
