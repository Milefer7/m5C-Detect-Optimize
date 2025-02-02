import re
from datetime import datetime
from collections import defaultdict
import os

log_dir = os.path.expanduser("~/myRes/ASC25-m5C/workspace/.snakemake/log/")
log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
log_files.sort()  # Sort to get the latest log file if needed
logPath = os.path.join(log_dir, log_files[-1]) if log_files else None

if not logPath:
    raise FileNotFoundError("No log files found in the specified directory.")
summaryPath = f"{logPath}_summary.csv"
file = open(summaryPath, 'w', encoding="utf-8")

file.write(f"{logPath}\n")

# 增强版正则表达式
timestamp_pattern = re.compile(r'^\[(.*?)\]')
rule_pattern = re.compile(r'^\s*(?:local)?rule (\w+):')
jobid_pattern = re.compile(r'jobid:\s*(\d+)')
threads_pattern = re.compile(r'threads:\s*(\d+)')
endjob_pattern = re.compile(r'Finished job (\d+)\.')

# 数据结构
jobs = {}  # {jobid: {rule, start, threads, end, duration}}
rule_stats = defaultdict(lambda: {
    'durations': [],
    'threads': None,
    'job_count': 0,
    'total_time': 0.0
})

# 状态跟踪变量
current_block = {}

def parse_log(log_path):
    with open(log_path) as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip('\n')
        
        # 解析时间戳
        if timestamp_match := timestamp_pattern.match(line):
            current_block['timestamp'] = datetime.strptime(
                timestamp_match.group(1), 
                '%a %b %d %H:%M:%S %Y'
            )
            continue
            
        # 解析规则声明
        if rule_match := rule_pattern.match(line):
            current_block['rule'] = rule_match.group(1)
            continue
            
        # 解析jobid
        if jobid_match := jobid_pattern.search(line):
            current_block['jobid'] = jobid_match.group(1)
            continue
            
        # 解析线程数
        if threads_match := threads_pattern.search(line):
            current_block['threads'] = int(threads_match.group(1))
            
            # 当收集齐必要字段时记录job
            if all(k in current_block for k in ['timestamp', 'rule', 'jobid', 'threads']):
                jobs[current_block['jobid']] = {
                    'rule': current_block['rule'],
                    'start': current_block['timestamp'],
                    'threads': current_block['threads']
                }
                current_block.clear()
            continue
            
        # 解析完成job
        if end_match := endjob_pattern.search(line):
            jobid = end_match.group(1)
            if jobid not in jobs:
                continue
                
            end_time = current_block.get('timestamp', jobs[jobid]['start'])
            duration = (end_time - jobs[jobid]['start']).total_seconds()
            
            # 更新统计信息
            rule = jobs[jobid]['rule']
            rule_stats[rule]['durations'].append(duration)
            rule_stats[rule]['total_time'] += duration
            rule_stats[rule]['job_count'] += 1
            
            # 记录首次出现的threads值
            if rule_stats[rule]['threads'] is None:
                rule_stats[rule]['threads'] = jobs[jobid]['threads']
                
            # 添加结束时间和持续时间到作业信息
            jobs[jobid]['end'] = end_time
            jobs[jobid]['duration'] = duration
            continue

def format_time(seconds):
    """将秒转换为易读格式"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02d}:{seconds:06.3f}"

# 执行解析
parse_log(logPath)

# 准备报告数据
report = []
for rule, stats in rule_stats.items():
    avg_time = stats['total_time'] / stats['job_count'] if stats['job_count'] else 0
    report.append((
        rule,
        avg_time,
        stats['total_time'],
        stats['threads'],
        stats['job_count']
    ))

# 按规则名称排序
report.sort(key=lambda x: x[0])

# 生成格式化输出
header = f"{'Rule':<40},{'Jobs':>8},{'Avg Time/min':>16},{'Total Time/min':>16},{'Threads':>10}\n"
file.write(header)

for entry in report:
    rule, avg, total, threads, count = entry
    file.write(f"{rule:<40},{count:>8},{avg / 60:>16.2f},{total / 60:>16.2f},{threads:>10}\n")

# 打印统计摘要
total_cpu_time = sum(stats['total_time'] for stats in rule_stats.values())
file.write(f"\n累计CPU时间: {total_cpu_time/3600:.2f} hours\n")

# 新增部分：计算total_wall_time
# 修改后的时间统计部分（修复多个关键问题）

# 新增：正确获取实际流程耗时
def get_job_time(jobid, time_type):
    """安全获取指定作业的时间"""
    job = jobs.get(str(jobid), {})
    time_value = job.get(time_type)
    if not time_value:
        print(f"警告: 作业{jobid}缺少{time_type}时间")
    return time_value

# 获取关键节点时间
first_job_start = min(
    (job['start'] for job in jobs.values() if 'start' in job),
    default=None
)
last_job_end = max(
    (job['end'] for job in jobs.values() if 'end' in job),
    default=None
)

# 计算实际流程耗时（首选全流程时间）
if first_job_start and last_job_end:
    pipeline_duration = (last_job_end - first_job_start).total_seconds()
    hours = int(pipeline_duration // 3600)
    minutes = int((pipeline_duration % 3600) // 60)
    seconds = pipeline_duration % 60
    file.write(f"实际流程耗时（全流程）: {hours:02d}:{minutes:02d}:{int(seconds):02d}小时\n")
else:
    # 备用方案：使用job18和job0的时间
    job18_start = get_job_time(18, 'start')
    job0_end = get_job_time(0, 'end')
    
    if job18_start and job0_end:
        time_diff = (job0_end - job18_start).total_seconds()
        if time_diff < 0:
            file.write("\n警告: job0结束时间早于job18开始时间，时序异常\n")
        hours = int(abs(time_diff) // 3600)
        minutes = int((abs(time_diff) % 3600) // 60)
        seconds = abs(time_diff) % 60
        file.write(f"实际流程耗时（job18开始→job0结束）: {hours:02d}:{minutes:02d}:{int(seconds):02d}小时\n")
    else:
        missing = []
        if not job18_start: missing.append("job18开始时间")
        if not job0_end: missing.append("job0结束时间")
        file.write(f"\n无法计算耗时，缺失数据: {', '.join(missing)}\n")

file.close()
print("统计时间文件路径：", os.path.abspath(summaryPath))