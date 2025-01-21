use std::env; // 引入标准库中的env模块
use std::process::exit; // 引入标准库中的Command和exit模块

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 8 {
        // 如果参数数量少于8，打印用法信息并退出
        eprintln!("Usage: {} <hisat3n_bin> <index> <threads> <summary_file> <input_fq> <unmapped_output> <mapped_output>", args[0]);
        exit(1);
    }

    // 提取参数
    let hisat3n_bin = &args[1];
    let index = &args[2];
    let threads = &args[3];
    let summary_file = &args[4];
    let input_fq = &args[5];
    let samtools_bin = &args[6];
    let unmapped_output = &args[7];
    let mapped_output = &args[8];

    // 构建命令字符串
    let command = format!(
        "{} --index {} -p {} --summary-file {} --new-summary -q -U {} --directional-mapping --all --norc --base-change C,T --mp 8,2 --no-spliced-alignment | {} view -@ {} -e '!flag.unmap' -O BAM -U {} -o {}",
        hisat3n_bin, index, threads, summary_file, input_fq, samtools_bin, threads, unmapped_output, mapped_output
    );

    // 打印命令字符串
    println!("{}", command);
}
