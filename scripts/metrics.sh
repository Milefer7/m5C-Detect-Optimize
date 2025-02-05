#!/bin/bash

# 脚本参数说明：
# $1: 标准答案文件 true.tsv 的路径
# $2: 检测结果文件 detected.tsv 的路径
# 使用示例 # 运行脚本 ./metrics.sh true.tsv SRR23538290.filtered.tsv
# ./metrics.sh ../data/standard/SRR23538290.genome.tsv ../workspace/detected_sites/filtered/SRR23538290.genome.tsv
# ./metrics.sh ../data/standard/SRR23538291.genome.tsv ../workspace/detected_sites/filtered/SRR23538291.genome.tsv
# ./metrics.sh ../data/standard/SRR23538292.genome.tsv ../workspace/detected_sites/filtered/SRR23538292.genome.tsv
# 注意：两个文件必须为制表符分隔，且包含 ref, pos, strand 前三列和 ur 列（默认第7列）

if [ $# -ne 2 ]; then
    echo "用法：$0 <true.tsv> <detected.tsv>"
    exit 1
fi

TRUE_FILE=$1
DETECTED_FILE=$2

# 检查文件是否存在
if [ ! -f "$TRUE_FILE" ]; then
    echo "错误：标准答案文件 $TRUE_FILE 不存在"
    exit 1
fi

if [ ! -f "$DETECTED_FILE" ]; then
    echo "错误：检测文件 $DETECTED_FILE 不存在"
    exit 1
fi

# 检查文件列数是否符合要求
if [ $(awk -F'\t' 'NR==1{print NF; exit}' "$TRUE_FILE") -lt 7 ]; then
    echo "错误：true.tsv 至少需要7列（含ur列）"
    exit 1
fi

if [ $(awk -F'\t' 'NR==1{print NF; exit}' "$DETECTED_FILE") -lt 7 ]; then
    echo "错误：detected.tsv 至少需要7列（含ur列）"
    exit 1
fi

# 计算精确度 (Precision)
PRECISION=$(awk '
BEGIN { FS="\t"; OFS="\t"; tp=0; total=0 }
NR == FNR { 
    if (FNR == 1) next;  # 跳过标题行（如果有）
    gsub(/[ \t]+$/, "", $1);  # 清理列数据
    gsub(/[ \t]+$/, "", $2);
    gsub(/[ \t]+$/, "", $3);
    key = $1 "," $2 "," $3;
    true_sites[key] = 1;
    next;
}
{
    if (FNR == 1) next;  # 跳过标题行（如果有）
    gsub(/[ \t]+$/, "", $1);
    gsub(/[ \t]+$/, "", $2);
    gsub(/[ \t]+$/, "", $3);
    key = $1 "," $2 "," $3;
    total++;
    if (key in true_sites) tp++;
}
END {
    if (total == 0) {
        printf "0.00";
    } else {
        printf "%.2f", (tp / total) * 100;
    }
}' "$TRUE_FILE" "$DETECTED_FILE")

echo "精确度 (Precision): $PRECISION%"

# 计算相关性 (Correlation)
# 提取重叠位点的 ur 值（仅比较共同位点）
awk -F'\t' '
BEGIN {
    OFS = "\t";
    # 读取 true.tsv 的位点和 ur
    while (getline < "'"$TRUE_FILE"'" > 0) {
        if (FNR == 1) continue;  # 跳过标题行
        key = $1 "," $2 "," $3;
        ur_true[key] = $7;
    }
    # 读取 detected.tsv 并匹配 ur
    while (getline < "'"$DETECTED_FILE"'" > 0) {
        if (FNR == 1) continue;  # 跳过标题行
        key = $1 "," $2 "," $3;
        if (key in ur_true) {
            n++;
            x = ur_true[key];
            y = $7;
            sumXY += x * y;
            sumX += x;
            sumY += y;
            sumX2 += x * x;
            sumY2 += y * y;
        }
    }
    # 计算皮尔逊相关系数
    if (n == 0) {
        print "相关性 (Correlation): NaN (无重叠位点)";
        exit;
    }
    numerator = n * sumXY - sumX * sumY;
    denom1 = sqrt(n * sumX2 - sumX^2);
    denom2 = sqrt(n * sumY2 - sumY^2);
    if (denom1 * denom2 == 0) {
        print "相关性 (Correlation): NaN (分母为0)";
    } else {
        r = numerator / (denom1 * denom2);
        printf "相关性 (Correlation): %.4f\n", r;
    }
}'