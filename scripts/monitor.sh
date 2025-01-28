#!/bin/bash

# ----------------- 配置项 -----------------
LOG_DIR="log"
LOG_FILE="${LOG_DIR}/monitor_$(date +'%Y-%m-%d_%H-%M').log" # 分钟级日志
MAX_CMD_LENGTH=40
REFRESH_INTERVAL=10
SEPARATOR="▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁"
MAX_LOG_DAYS=7  # 自动清理7天前日志

# ----------------- 初始化 -----------------
mkdir -p "${LOG_DIR}"

# 检查依赖项
if ! command -v pidstat &> /dev/null; then
    echo "错误：需要安装sysstat工具包"
    echo "Ubuntu/Debian: sudo apt install sysstat"
    echo "CentOS/RHEL: sudo yum install sysstat"
    exit 1
fi

# 自动清理旧日志
find "${LOG_DIR}" -name "monitor_*.log" -mtime +${MAX_LOG_DAYS} -delete

# 初始化日志文件
if [ ! -f "${LOG_FILE}" ]; then
    echo -ne "\xEF\xBB\xBF" > "${LOG_FILE}"
    echo -e "记录时间\tPID\t进程名\t内存%\tCPU%\tI/O读(KB/s)\tI/O写(KB/s)\t完整命令行" >> "${LOG_FILE}"
fi

# ----------------- 主循环 -----------------
while true; do
    clear
    current_time=$(date +'%Y-%m-%d %H:%M:%S')
    term_width=$(tput cols)
    
    # 获取进程数据
    processes=$(ps aux --sort=-%mem | awk 'NR<=6 && NR>1')
    
    # 获取I/O数据（两次采样取平均）
    io_stats=$(pidstat -dlh 1 2 | awk '
    BEGIN {count=0} 
    /^Average:/ && NF>=7 {
        pid=$4
        read[pid] += $6
        write[pid] += $7
        count[pid]++
    } 
    END {
        for (pid in read) {
            if (count[pid] > 0) {
                printf "%s %.1f %.1f\n", pid, read[pid]/count[pid], write[pid]/count[pid]
            }
        }
    }')

    # ================= 终端显示 =================
    echo "🔄 进程监控 | 刷新间隔: ${REFRESH_INTERVAL}秒 | 终端宽度: ${term_width}"
    echo "📅 当前时间: ${current_time}"
    printf "%-7s %-18s %5s %5s %10s %10s %s\n" "PID" "进程名" "内存%" "CPU%" "I/O读" "I/O写" "命令行"
    echo "${SEPARATOR:0:$term_width}"

    echo "${processes}" | awk -v term_w=${term_width} -v io_data="${io_stats}" '
    BEGIN {
        split(io_data, io_lines, "\n")
        for (i in io_lines) {
            split(io_lines[i], fields, " ")
            io_pid[fields[1]] = 1
            io_read[fields[1]] = fields[2]
            io_write[fields[1]] = fields[3]
        }
    }
    {
        pid = $2
        cmd_full = $11
        for (i=12; i<=NF; i++) cmd_full = cmd_full " " $i
        
        # 动态调整显示宽度
        col_width = term_w - 65
        if (col_width < 10) col_width = 10
        cmd_display = length(cmd_full) > col_width ? substr(cmd_full,1,col_width-3) "..." : cmd_full
        
        printf "%-7s %-18s %5.1f %5.1f %10s %10s %s\n", 
            pid, 
            (length($11)>15 ? substr($11,1,15) "..." : $11),
            $4, 
            $3, 
            (pid in io_pid ? sprintf("%.1f", io_read[pid]) : "N/A"),
            (pid in io_pid ? sprintf("%.1f", io_write[pid]) : "N/A"),
            cmd_display
    }'

    # ================= 日志记录 =================
    {
        echo -e "\n🕒 记录时间: ${current_time}"
        echo "${SEPARATOR}"
        echo "${processes}" | awk -v io_data="${io_stats}" '
        BEGIN {
            split(io_data, io_lines, "\n")
            for (i in io_lines) {
                split(io_lines[i], fields, " ")
                io_pid[fields[1]] = 1
                io_read[fields[1]] = fields[2]
                io_write[fields[1]] = fields[3]
            }
        }
        {
            pid = $2
            cmd = $11
            for (i=12; i<=NF; i++) cmd = cmd " " $i
            printf "%s\t%s\t%.1f\t%.1f\t%s\t%s\t%s\n", 
                pid, 
                $11, 
                $4, 
                $3, 
                (pid in io_pid ? io_read[pid] : "N/A"), 
                (pid in io_pid ? io_write[pid] : "N/A"), 
                cmd
        }'
    } >> "${LOG_FILE}"

    sleep ${REFRESH_INTERVAL}
done