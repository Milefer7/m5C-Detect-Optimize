import re
from datetime import datetime
from collections import defaultdict
import os

def parse_snakemake_log():
    # 初始化路径
    log_dir = os.path.expanduser("~/myRes/ASC25-m5C/workspace/.snakemake/log/")
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
    
    if not log_files:
        raise FileNotFoundError("未找到任何日志文件")
    
    log_path = os.path.join(log_dir, log_files[-1])
    summary_path = f"{log_path}_summary.md"  # 输出为Markdown文件
    
    # 数据结构初始化
    jobs = {}
    rule_stats = defaultdict(lambda: {
        'durations': [], 
        'threads': None,
        'job_count': 0,
        'total_time': 0.0
    })

    # 正则模式编译
    patterns = {
        'timestamp': re.compile(r'^\[(.*?)\]'),
        'rule': re.compile(r'^\s*(?:local)?rule (\w+):'),
        'jobid': re.compile(r'jobid:\s*(\d+)'),
        'threads': re.compile(r'threads:\s*(\d+)'),
        'endjob': re.compile(r'Finished job (\d+)\.')
    }

    # 日志解析
    with open(log_path) as f:
        current_block = {}
        for line in f:
            line = line.strip()
            
            # 解析时间戳
            if ts_match := patterns['timestamp'].match(line):
                current_block['timestamp'] = datetime.strptime(ts_match.group(1), '%a %b %d %H:%M:%S %Y')
                continue
                
            # 解析规则
            if rule_match := patterns['rule'].match(line):
                current_block['rule'] = rule_match.group(1)
                continue
                
            # 组合job信息
            if jobid_match := patterns['jobid'].search(line):
                current_block['jobid'] = jobid_match.group(1)
                
            if threads_match := patterns['threads'].search(line):
                current_block['threads'] = int(threads_match.group(1))
                
                if all(k in current_block for k in ['timestamp', 'rule', 'jobid', 'threads']):
                    jobs[current_block['jobid']] = {
                        'rule': current_block['rule'],
                        'start': current_block['timestamp'],
                        'threads': current_block['threads'],
                        'end': None,
                        'duration': None
                    }
                    current_block.clear()
                continue
                
            # 记录结束时间
            if end_match := patterns['endjob'].search(line):
                jobid = end_match.group(1)
                if jobid in jobs:
                    end_time = current_block.get('timestamp', jobs[jobid]['start'])
                    duration = (end_time - jobs[jobid]['start']).total_seconds()
                    
                    jobs[jobid].update({
                        'end': end_time,
                        'duration': duration
                    })
                    
                    rule = jobs[jobid]['rule']
                    rule_stats[rule]['durations'].append(duration)
                    rule_stats[rule]['total_time'] += duration
                    rule_stats[rule]['job_count'] += 1
                    if rule_stats[rule]['threads'] is None:
                        rule_stats[rule]['threads'] = jobs[jobid]['threads']

    # 生成报告
    with open(summary_path, 'w', encoding='utf-8') as f:
        # 写入元数据（注释行）
        f.write(f"# Log analysis for: {os.path.basename(log_path)}\n")
        f.write("# Generated at: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        # 写入表头（Markdown格式的表格）
        f.write("\n| rule_name | job_count | avg_time_min | total_time_min | threads |\n")
        f.write("|-----------|-----------|--------------|-----------------|---------|\n")  # 分隔线
        
        # 数据行
        for rule in sorted(rule_stats.keys()):
            stats = rule_stats[rule]
            if stats['job_count'] == 0:
                continue
                
            avg = stats['total_time'] / stats['job_count'] / 60
            total = stats['total_time'] / 60
            
            # 处理字段中的竖线字符
            rule_name = f'"{rule}"' if '|' in rule else rule
            # 使用Markdown的表格语法
            f.write(f"| {rule_name} | {stats['job_count']} | {avg:.2f} | {total:.2f} | {stats['threads']} |\n")
        
        # 统计摘要
        total_cpu = sum(s['total_time'] for s in rule_stats.values()) / 3600
        f.write("\n# === Summary ===\n")
        f.write(f"# Total CPU Time: {total_cpu:.2f} hours\n")
        
        # 计算实际耗时
        valid_jobs = [j for j in jobs.values() if j['start'] and j['end']]
        if valid_jobs:
            start = min(j['start'] for j in valid_jobs)
            end = max(j['end'] for j in valid_jobs)
            delta = end - start
            f.write(f"# Wall Time: {delta.days*24 + delta.seconds//3600:02d}:{(delta.seconds//60)%60:02d}:{delta.seconds%60:02d} hours\n")
        else:
            f.write("# Wall Time: N/A\n")

    print(f"分析报告已生成：{os.path.abspath(summary_path)}")

if __name__ == "__main__":
    parse_snakemake_log()