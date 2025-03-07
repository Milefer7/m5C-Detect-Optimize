<h1 align="center">m<sup>5</sup>C-UBSseq</h1>

RNA molecules undergo various chemical modifications that play key roles in regulating gene expression, post-transcriptional processes, and protein synthesis. Among these modifications, 5-methylcytosine (m^5^C) is particularly important, influencing a wide range of RNA species and impacting numerous biological functions. The primary challenge in m^5^C detection lies in balancing the need for accuracy and reliability with the goal of minimizing false positives and increasing processing speed. This repository serves as a comprehensive record of optimization efforts, ensuring the reliable identification of high-confidence m^5^C candidate sites with minimal false-positive rates, while also minimizing overall processing time.

## Branch Description

Use git for version management and conda for environment management. The final optimization results are stored in branch v0.25 which is also the final result submission.

```mermaid
graph LR
    template((template)) --> I(Intermediate Test)
    template --> F(Final Test)
    
    subgraph Intermediate
        I --> 1(v1.x)
        1 --> v1.1
        1 --> v1.2
        1 --> v1.3
        1 --> v1.4
        1 --> v1.5
        1 --> v1.6
        
        I --> 2(v2.x)
        2 --> v2.0
        2 --> v2.1
    end
    
    subgraph Final
        F --> v0.0(v0.0 without customized_genes)
        F --> v0.1(v0.1 with customized_genes)
        
        v0.1 --> v0.2
        subgraph v0.2_versions[" "]
            v0.2 --> v0.21
            v0.2 --> v0.22
            v0.2 --> v0.23
            v0.2 --> v0.24
            v0.2 --> v0.25
        end
        
        v0.1 --> v0.3
        v0.1 --> v0.4
        
        v0.1 --> v0.5
        subgraph v0.5_versions[" "]
            v0.5 --> v0.51
            v0.5 --> v0.52
        end
        
        v0.1 --> v0.6
    end

    %% 增加连接线间隔
    linkStyle 6,7,8,9,10 stroke-width:1px;
    linkStyle 11,12 stroke-width:1px;
    linkStyle 13,14,15,16,17 stroke-width:1px;
    linkStyle 18,19 stroke-width:1px;
    linkStyle 20,21 stroke-width:1px;
```

### **Final Test**  

> **v0.25 will be submitted as the final result. **

- **v0.0**: Baseline test **without** `customized_genes`.  
- **v0.1**: Baseline test **with** `customized_genes`.  
  - **v0.2x**: Parallelization optimization. It should be noted that v0.25 is the result branch of the final optimization and will be submitted as the final result. 
  - **v0.3**: Testing **O3** optimization.  
    - Parallelization of this branch is not fully implemented yet.  
  - **v0.4**: Optimizing `filter_sites` and testing its impact.  
  - **v0.5x**: Testing **O3** optimization with refined parallelization.  
    - **v0.50**: Aggressive optimization strategy.  
    - **v0.51**: Simplified **O3** optimization strategy.  
  - **v0.6**: Attempt to optimize hisat2_3n_calling_unfiltered_unique by adding tmpdir="/dev/shm"

---

### **Intermediate Test**  

> These versions are **intermediate tests**, not part of the final evaluation, as they use a different reference.  

- **v1.x**: Focused on **parallelization testing**.  
- **v2.x**: Focused on **O3 optimization testing**.  

## Reproduction instructions

* Check if you are on the exact branch

  ```shell
  $ git branch # The * mark should belong to v0.25. If not, switch to that branch
  
  # You can switch to any branch mentioned above to check the optimization process data
  $ git switch v0.25 # final result
  $ git switch v0.1  # Benchmark
  ```

* Configure conda environment

  ```conda
  conda env create -f environment.yml
  ```

<p align="center">
<img
  src="https://raw.githubusercontent.com/y9c/y9c/master/resource/footer_line.svg?sanitize=true"
/>
</p>
<p align="center">
Fork the respository of https://github.com/y9c/m5C-UBSseq
<a href="https://github.com/y9c" target="_blank">Chang Y</a>
</p>
<p align="center">