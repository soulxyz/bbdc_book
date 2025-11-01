//! BBDC Word Tool - 不背单词词书制作工具
//! 
//! 主程序入口

use bbdc_word_tool::cli::Cli;

fn main() {
    // 运行CLI
    if let Err(e) = Cli::run() {
        eprintln!("❌ 错误: {}", e);
        std::process::exit(1);
    }
}
