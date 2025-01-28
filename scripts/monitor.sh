#!/bin/bash

# ----------------- 配置项 -----------------
export LC_NUMERIC=C  # 确保数字格式使用点号
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${BASE_DIR}/scripts/log"
MAX_CMD_LENGTH=40
REFRESH_INTERVAL=10
SEPARATOR="▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁"
MAX_LOG_DAYS=7

# ----------------- 初始化 -----------------
mkdir -p "${LOG_DIR}" || {
    echo "无法创建日志目录: ${LOG_DIR}" >&2
    exit 1
}

# 检查依赖项
REQUIRED_CMDS=(pidstat ps awk tput find)
for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command -v "${cmd}" &> /dev/null; then
        echo "错误：需要安装 ${cmd} 命令" | tee -a "${LOG_FILE}"
        exit 1
    fi
done

# 自动清理旧日志
find "${LOG_DIR}" -name "monitor_*.log" -mtime +${MAX_LOG_DAYS} -delete 2>/dev/null

# 主循环变量
last_hour=""

# ----------------- 主循环 -----------------
while :; do
    current_time=$(date +"%Y-%m-%d %H:%M:%S")
    current_hour=$(date +"%Y-%m-%d_%H")

    # 动态更新日志文件路径（每小时一个文件）
    if [[ "${current_hour}" != "${last_hour}" ]]; then
        LOG_FILE="${LOG_DIR}/monitor_${current_hour}.log"
        # 初始化新日志文件
        if [[ ! -f "${LOG_FILE}" ]]; then
            echo -ne "\xEF\xBB\xBF" > "${LOG_FILE}" 2>/dev/null || {
                echo "无法写入日志文件: ${LOG_FILE}" >&2
                exit 1
            }
            echo -e "记录时间\tPID\t进程名\t内存%\tCPU%\tI/O读(KB/s)\tI/O写(KB/s)\t完整命令行" >> "${LOG_FILE}" || {
                echo "无法写入日志文件: ${LOG_FILE}" >&2
                exit 1
            }
        fi
        last_hour="${current_hour}"
    fi

    # ================= 数据采集 =================
    {
        # 进程数据（按内存排序）
        processes=$(ps --no-headers -eo pid,%mem,%cpu,comm,args --sort=-%mem | head -n 6)
        
        # I/O数据采集（两次采样取平均）
        io_stats=$(pidstat -dlh 1 2 | awk '
        /^Average:/ && NF>=7 {
            pid=$4
            read[pid] += $6
            write[pid] += $7
            cnt[pid]++
        } 
        END {
            for (pid in read) {
                if (cnt[pid] > 0) {
                    printf "%s %.1f %.1f\n", pid, read[pid]/cnt[pid], write[pid]/cnt[pid]
                }
            }
        }')
    } 2>>"${LOG_FILE}"

    # ================= 日志记录 =================
    {
        printf "\n🕒 记录时间: %s\n" "${current_time}"
        echo "${SEPARATOR}"
        awk -v current_time="${current_time}" -v io_data="${io_stats}" '
        BEGIN {
            split(io_data, io_lines, "\n")
            for (i in io_lines) {
                split(io_lines[i], fields, " ")
                if (length(fields)>=3) {
                    pid=fields[1]
                    io_read[pid] = fields[2]
                    io_write[pid] = fields[3]
                }
            }
        }
        {
            pid = $1
            mem = $2
            cpu = $3
            comm = $4
            cmd_full = $5
            for (i=6; i<=NF; i++) cmd_full = cmd_full " " $i
            
            printf "%s\t%s\t%s\t%.1f\t%.1f\t%s\t%s\t%s\n", 
                current_time,
                pid, 
                comm,
                mem, 
                cpu, 
                (pid in io_read ? io_read[pid] : "N/A"), 
                (pid in io_write ? io_write[pid] : "N/A"), 
                cmd_full
        }' <<< "${processes}"
    } >> "${LOG_FILE}" 2>/dev/null

    sleep "${REFRESH_INTERVAL}"
done