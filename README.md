[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11046885.svg)](https://doi.org/10.5281/zenodo.11046885)

# m `<sup>`5 `</sup>`C-UBSseq

## 优化策略

### 1. 线程重分配

```
rule               原线程 → 新线程 | 优化依据
-------------------------------------------------
hisat2_3n_calling* 18 → 24        | 单任务加速，减少总耗时
hisat2_mapping_*   35 → 22        | 平衡并行度和单任务效率
cutadapt_SE        35 → 10        | I/O瓶颈显著，降线程提吞吐
dedup_mapping      18 → 12        | JVM内存限制，避免GC停顿
join_pileup        6 → 12         | 启用Python多进程优化
```

### 2. 资源组策略升级

```
snakemake --cores 110 --resources 
  heavy=2 medium=4 light=8  # 三级控制
```

* **heavy组** （hisat2_calling*）: 24线程/任务，并行2个 → 48核
* **medium组** （mapping/sort）: 22线程，并行4个 → 88核
* **light组** （预处理）: 10线程，并行8个 → 80核

## Changelog

- 4/23/2024: rewrite code using polars

## workflow

[![](./docs/flow.svg)](https://github.com/y9c/m5C-UBSseq)

## Citation

- cite this software

  ```BibTex
  @software{chang_y_2024_11046885,
      author    = {Chang Y},
      title     = {y9c/m5C-UBSseq: V0.1},
      publisher = {Zenodo},
      version   = {v0.1},
      doi       = {10.5281/zenodo.11046885},
      url       = {https://doi.org/10.5281/zenodo.11046885}
  }
  ```
- cite the method

  ```BibTex
  @article{dai_ultrafast_2024,
      title = {Ultrafast bisulfite sequencing detection of 5-methylcytosine in {DNA} and {RNA}},
      url = {https://www.nature.com/articles/s41587-023-02034-w},
      doi = {10.1038/s41587-023-02034-w},
      author = {Dai, Qing and Ye, Chang and Irkliyenko, Iryna and Wang, Yiding and Sun, Hui-Lung and Gao, Yun and Liu, Yushuai and Beadell, Alana and Perea, José and Goel, Ajay and He, Chuan},
      date = {2024-01-02},
  }
  ```

&nbsp;

<p align="center">
<img
  src="https://raw.githubusercontent.com/y9c/y9c/master/resource/footer_line.svg?sanitize=true"
/>
</p>
<p align="center">
Copyright © 2021-present
<a href="https://github.com/y9c" target="_blank">Chang Y</a>
</p>
<p align="center">
