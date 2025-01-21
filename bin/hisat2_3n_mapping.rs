use std::process::{Command, exit}; // 引入标准库中的Command和exit模块
use std::env; // 引入标准库中的env模块
use std::fs; // 引入标准库中的fs模块
use std::path::Path; // 引入标准库中的Path模块
use std::thread; // 引入标准库中的thread模块
use std::sync::Arc; // 引入标准库中的Arc模块
use std::sync::Mutex; // 引入标准库中的Mutex模块

fn main() {
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    if args.len() < 7 {
        // 如果参数数量少于7，打印用法信息并退出
        eprintln!("Usage: {} <hisat2_index> <threads> <summary_output> <input_fq> <unmapped_output> <mapped_output>", args[0]);
        exit(1);
    }

    // 提取参数
    let hisat2_index = &args[1];
    let threads = &args[2];
    let summary_output = &args[3];
    let input_fq = &args[4];
    let unmapped_output = &args[5];
    let mapped_output = &args[6];



    // 拆分输入文件
    let split_prefix = "part_"; // 拆分文件的前缀
    let input_fq_path = Path::new(input_fq); // 输入文件的路径
    let num_chunks = 4; // 假设拆分成4块
    split_input_file(input_fq_path, split_prefix, num_chunks); // 调用拆分函数

    // 并行处理每个拆分文件
    let handles: Vec<_> = (0..num_chunks).map(|i| {
        let hisat2_index = hisat2_index.clone(); // 克隆hisat2_index
        let threads = threads.clone(); // 克隆threads
        let summary_output = summary_output.clone(); // 克隆summary_output
        let input_file = format!("{}{}", split_prefix, i); // 生成拆分文件名
        let unmapped_output = format!("{}{}", unmapped_output, i); // 生成未映射输出文件名
        let mapped_output = format!("{}{}", mapped_output, i); // 生成已映射输出文件名

        thread::spawn(move || {
            // 使用 cgroups 限制内存
            let cgexec_output = Command::new("cgexec")
                .arg("-g")
                .arg("memory:hisat2_group")
                .arg("hisat3n")
                .arg("--index")
                .arg(hisat2_index)
                .arg("-p")
                .arg(threads)
                .arg("--summary-file")
                .arg(summary_output)
                .arg("--new-summary")
                .arg("-q")
                .arg("-U")
                .arg(input_file)
                .arg("--directional-mapping")
                .arg("--all")
                .arg("--norc")
                .arg("--base-change")
                .arg("C,T")
                .arg("--mp")
                .arg("8,2")
                .arg("--no-spliced-alignment")
                .output();

            if let Err(e) = cgexec_output {
                // 如果执行失败，打印错误信息并退出
                eprintln!("Failed to execute cgexec: {}", e);
                exit(1);
            }

            // 执行 samtools
            let samtools_output = Command::new("samtools")
                .arg("view")
                .arg("-@")
                .arg(threads)
                .arg("-e")
                .arg("!flag.unmap")
                .arg("-O")
                .arg("BAM")
                .arg("-U")
                .arg(unmapped_output)
                .arg("-o")
                .arg(mapped_output)
                .output();

            if let Err(e) = samtools_output {
                // 如果执行失败，打印错误信息并退出
                eprintln!("Failed to execute samtools: {}", e);
                exit(1);
            }
        })
    }).collect();

    // 等待所有线程完成
    for handle in handles {
        handle.join().expect("Thread failed to execute.");
    }

    // 合并所有输出 BAM 文件
    let merge_command = Command::new("samtools")
        .arg("merge")
        .arg(mapped_output)
        .arg(format!("{}*", mapped_output))
        .output();

    if let Err(e) = merge_command {
        // 如果合并失败，打印错误信息并退出
        eprintln!("Failed to merge BAM files: {}", e);
        exit(1);
    }

    println!("Commands executed successfully."); // 打印成功信息
}

// 拆分输入文件
fn split_input_file(input_fq: &Path, prefix: &str, num_chunks: usize) {
    // 使用外部命令 `split` 来拆分文件
    let split_command = Command::new("split")
        .arg("-l")
        .arg("1000000") // 每块1000000行
        .arg(input_fq)
        .arg(prefix)
        .output()
        .expect("Failed to execute split command.");

    if !split_command.status.success() {
        // 如果拆分失败，打印错误信息并退出
        eprintln!("Failed to split the input file.");
        exit(1);
    }
}

#[test]
fn test_print_args() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 7 {
        // 如果参数数量少于7，打印用法信息并退出
        eprintln!("Usage: {} <hisat2_index> <threads> <summary_output> <input_fq> <unmapped_output> <mapped_output>", args[0]);
        exit(1);
    }

    // 提取参数
    let hisat2_index = &args[1];
    let threads = &args[2];
    let summary_output = &args[3];
    let input_fq = &args[4];
    let unmapped_output = &args[5];
    let mapped_output = &args[6];

    // 打印参数
    println!("hisat2_index: {}", hisat2_index);
    println!("threads: {}", threads);
    println!("summary_output: {}", summary_output);
    println!("input_fq: {}", input_fq);
    println!("unmapped_output: {}", unmapped_output);
    println!("mapped_output: {}", mapped_output);
}
