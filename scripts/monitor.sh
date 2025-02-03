#!/bin/bash

# 读取config.yml中的密码(python version)
sudo_password=$(yq -r '.sudo_password' ~/.config/config.yml)
# echo "sudo_password: $sudo_password"

# 定义保存快照的目录
snapshot_dir="$HOME/myRes/ASC25-m5C/workspace/.snakemake/log/atop_snapshots"

# 如果目录不存在，则创建它
mkdir -p "$snapshot_dir"

# 定义快照文件名，使用日期时间戳作为文件名的一部分
timestamp=$(date "+%Y-%m-%d_%H-%M-%S")
snapshot_file="$snapshot_dir/atop_$timestamp"

# 运行 atop 并将数据保存到指定的文件
echo "开启atop监控，输入'q'退出..."
sudo atop -w "$snapshot_file" -d 60 &

# 获取 atop 的进程ID
sleep 1  # 给 atop 进程时间启动
atop_pid=$(ps aux | grep '[a]top -w' | awk '{print $2}')
# echo "atop_pid: $atop_pid"

# 捕获用户输入的q来退出脚本
while true; do
    # 等待用户输入
    read -n 1 -s key
    if [[ $key == "q" ]]; then
        echo -e "\n接收 'q', 退出..."
        echo -n "$sudo_password" | sudo -S kill -15 $atop_pid 2>&1
        # 等待确认进程已退出
        wait $atop_pid 2>/dev/null
        echo "\n快照已保存为: $snapshot_file" # 输出完成信息
        exit
    fi
done
