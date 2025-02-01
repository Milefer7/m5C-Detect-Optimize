import re
from datetime import datetime
from collections import defaultdict
import os

logPath = os.path.expanduser("~/myRes/ASC25-m5C/workspace/.snakemake/log/2025-01-30T083926.690412.snakemake.log")
summaryPath = f"{logPath}_summary.csv"
file = open(summaryPath, 'w', encoding="utf-8")

file.write(f"{logPath}\n")
# print(logPath)

# 增强版正则表达式
timestamp_pattern = re.compile(r'^\[(.*?)\]')
rule_pattern = re.compile(r'^\s*(?:local)?rule (\w+):')
jobid_pattern = re.compile(r'jobid:\s*(\d+)')
threads_pattern = re.compile(r'threads:\s*(\d+)')
endjob_pattern = re.compile(r'Finished job (\d+)\.')

# 数据结构
jobs = {}  # {jobid: (rule, start_time, threads)}
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
                
            del jobs[jobid]

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

# 生成格式化输出（加宽版）
header = f"{'Rule':<40},{'Jobs':>8},{'Avg Time/min':>16},{'Total Time/min':>16},{'Threads':>10}\n"
separator = '-' * 100 + "\n" # 分隔线加宽
# print(header)
# print(separator)
file.write(header)
# file.write(separator)

for entry in report:
    rule, avg, total, threads, count = entry
    file.write(f"{rule:<40},{count:>8},{avg / 60:>16.2f},{total / 60:>16.2f},{threads:>10}\n")
    # print(f"{rule:<40} {count:>8} {avg / 60:>16.2f}min {total / 60:>16.2f}min {threads:>10}")

# 打印统计摘要
total_runtime = sum(stats['total_time'] for stats in rule_stats.values())
# print(f"\nTotal pipeline runtime: {total_runtime/3600:.2f} hours")
file.write(f"\nTotal pipeline runtime: {total_runtime/3600:.2f} hours\n")
if file:
    file.close()
print("统计时间文件路径：", os.path.abspath(summaryPath))