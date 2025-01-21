use std::process::{Command, exit};
use std::env;
use std::fs;
use std::path::Path;
use std::thread;
use std::sync::Arc;
use std::sync::Mutex;

fn main() {
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    if args.len() < 7 {
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

    // 设置资源限制
    let ulimit_output = Command::new("ulimit")
        .arg("-v")
        .arg("14000000") // 14GB内存限制
        .output();

    if let Err(e) = ulimit_output {
        eprintln!("Failed to set ulimit: {}", e);
        exit(1);
    }

    // 拆分输入文件
    let split_prefix = "part_";
    let input_fq_path = Path::new(input_fq);
    let num_chunks = 4; // 假设拆分成4块
    split_input_file(input_fq_path, split_prefix, num_chunks);

    // 并行处理每个拆分文件
    let handles: Vec<_> = (0..num_chunks).map(|i| {
        let hisat2_index = hisat2_index.clone();
        let threads = threads.clone();
        let summary_output = summary_output.clone();
        let input_file = format!("{}{}", split_prefix, i);
        let unmapped_output = format!("{}{}", unmapped_output, i);
        let mapped_output = format!("{}{}", mapped_output, i);

        thread::spawn(move || {
            // 执行 hisat2
            let hisat2_output = Command::new("hisat3n")
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

            if let Err(e) = hisat2_output {
                eprintln!("Failed to execute hisat2: {}", e);
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
        eprintln!("Failed to merge BAM files: {}", e);
        exit(1);
    }

    println!("Commands executed successfully.");
}

// 拆分输入文件
fn split_input_file(input_fq: &Path, prefix: &str, num_chunks: usize) {
    let file = fs::File::open(input_fq).expect("Failed to open input file.");
    let reader = std::io::BufReader::new(file);

    let lines: Vec<String> = reader.lines().collect::<Result<_, _>>().expect("Failed to read input file.");

    let chunk_size = lines.len() / num_chunks;

    for i in 0..num_chunks {
        let chunk_start = i * chunk_size;
        let chunk_end = if i == num_chunks - 1 { lines.len() } else { (i + 1) * chunk_size };
        let chunk_lines = &lines[chunk_start..chunk_end];

        let chunk_file = format!("{}{}", prefix, i);
        let mut writer = fs::File::create(chunk_file).expect("Failed to create chunk file.");
        for line in chunk_lines {
            writeln!(writer, "{}", line).expect("Failed to write to chunk file.");
        }
    }
}
