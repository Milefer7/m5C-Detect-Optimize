#!/bin/bash

max_runtime=10800

# 定义保存快照的目录
snapshot_dir="$HOME/myRes/ASC25-m5C/workspace/.snakemake/log/atop_snapshots"

# 如果目录不存在，则创建它
mkdir -p "$snapshot_dir"

# 定义快照文件名，使用日期时间戳作为文件名的一部分
timestamp=$(date "+%Y-%m-%d_%H-%M-%S")
snapshot_file="$snapshot_dir/atop_$timestamp"

# 运行 atop 并将数据保存到指定的文件
echo "开启atop监控，输入'q'退出..."
timeout $max_runtime atop -w "$snapshot_file" -d 60 &

# 获取 atop 的进程ID
atop_pid=$!

# 捕获用户输入的q来退出脚本
while true; do
    # 等待用户输入
    read -n 1 -s key
    if [[ $key == "q" ]]; then
        echo -e "\n接收 'q', 退出..."
        kill $atop_pid
        # 等待确认进程已退出
        wait $atop_pid 2>/dev/null
        echo "快照已保存为: $snapshot_file" # 输出完成信息
        exit
    fi
done
