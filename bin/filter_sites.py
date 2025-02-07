#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2021 Ye Chang yech1990@gmail.com
# Distributed under terms of the MIT license.
#
# Created: 2021-10-06 01:53


import argparse
from scipy.stats import binomtest
import polars as pl

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-i", "--input-file", help="Input site file")
arg_parser.add_argument("-m", "--mask-file", help="mask file")
arg_parser.add_argument("-b", "--background-file", help="background file")
arg_parser.add_argument("-o", "--output-file", help="output file")


args = arg_parser.parse_args()

# 惰性加载数据：使用 scan_ipc 优化大数据加载，并在最后调用 collect() 触发计算
df_site = (
    pl.scan_ipc(args.input_file) # 将read_ipc替换为scan_ipc，优化大数据加载
    .with_columns(
        u=pl.col("unconvertedBaseCount_filtered_uniq"),
        d=pl.col("convertedBaseCount_filtered_uniq") + pl.col("unconvertedBaseCount_filtered_uniq"),
    )
    .with_columns(ur=pl.col("u") / pl.col("d"))
    .collect()  # 触发计算
)

# 读取 mask 文件
df_pre = pl.read_csv(
    args.mask_file,
    separator="\t",
    has_header=False,
    new_columns=["ref", "pos", "strand"],
    schema_overrides={"ref": pl.Utf8, "pos": pl.Int64, "strand": pl.Utf8},  # 修改此行
)

# 计算背景比率：选择不在 mask 中的数据，计算 ur 列均值
bg_ratio = (
    df_site.join(df_pre, on=["ref", "pos", "strand"], how="anti")
    .get_column("ur")
    .drop_nans()
    .mean()
)
with open(args.background_file, "w") as f:
    f.write(f"{bg_ratio}\n")

# 修改calculate_pval函数，使用struct和map_elements
def calculate_pval(u: pl.Expr, d: pl.Expr, p: float) -> pl.Expr:
    return (
        pl.struct([u, d])
        .map_elements(
            lambda x: binomtest(x['u'], x['d'], p, alternative="greater").pvalue
            if x['u'] != 0 and x['d'] != 0
            else 1.0,
            return_dtype=pl.Float64,
        )
    )

# 根据 mask 文件与 site 数据进行左连接，并计算 p 值及过滤条件
df_filter = (
    df_pre.join(df_site, on=["ref", "pos", "strand"], how="left")
    .with_columns(
        pl.col("u").fill_null(0),
        pl.col("d").fill_null(0)
    )
    .with_columns(
        pval=calculate_pval(pl.col("u"), pl.col("d"), bg_ratio)
    )
    .with_columns(
        passed=(
            (pl.col("pval") < 0.001) &
            (pl.col("u") >= 2) &
            (pl.col("d") >= 10) &
            (pl.col("ur") > 0.02)
        )
    )
)

# 输出结果到文件
df_filter.write_csv(args.output_file, separator="\t", include_header=True)
