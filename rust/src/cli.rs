//! 命令行界面模块

use crate::{BBDCChecker, EnvLoader, LLMCorrector, WordExtractor, Result, Error};
use clap::{Parser, Subcommand};
use std::path::PathBuf;
use std::io::{self, Write};

/// 不背单词词书制作工具
#[derive(Parser)]
#[command(name = "bbdc_word_tool")]
#[command(author = "BBDC Tool Contributors")]
#[command(version = "1.0.0")]
#[command(about = "从 Markdown 提取单词并自动核对", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Option<Commands>,
    
    /// 输入文件路径（交互模式）
    #[arg(short, long, value_name = "FILE")]
    pub input: Option<PathBuf>,
    
    /// 输出文件路径
    #[arg(short, long, value_name = "FILE")]
    pub output: Option<PathBuf>,
    
    /// 是否去重
    #[arg(short, long, default_value_t = true)]
    pub unique: bool,
    
    /// 是否自动核对
    #[arg(short = 'c', long, default_value_t = true)]
    pub auto_check: bool,
    
    /// 是否包含短语
    #[arg(short = 'p', long, default_value_t = false)]
    pub include_phrases: bool,
}

#[derive(Subcommand)]
pub enum Commands {
    /// 提取单词
    Extract {
        /// 输入文件
        input: PathBuf,
        
        /// 输出文件
        #[arg(short, long)]
        output: Option<PathBuf>,
        
        /// 是否去重
        #[arg(short, long, default_value_t = true)]
        unique: bool,
        
        /// 是否自动核对
        #[arg(short = 'c', long, default_value_t = true)]
        auto_check: bool,
        
        /// 提取模式：words_only, with_meaning, full
        #[arg(short, long, default_value = "words_only")]
        mode: String,
    },
    
    /// 核对单词
    Check {
        /// 单词文件
        input: PathBuf,
    },
    
    /// 检查环境配置
    Env,
}

impl Cli {
    /// 运行CLI
    pub fn run() -> Result<()> {
        // 初始化日志
        env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
            .format_timestamp(None)
            .init();
        
        // 加载环境变量
        EnvLoader::init()?;
        
        let cli = Cli::parse();
        
        match cli.command {
            Some(Commands::Extract {
                input,
                output,
                unique,
                auto_check,
                mode,
            }) => {
                Self::handle_extract(input, output, unique, auto_check, &mode)?;
            }
            Some(Commands::Check { input }) => {
                Self::handle_check(input)?;
            }
            Some(Commands::Env) => {
                Self::handle_env_check()?;
            }
            None => {
                // 交互模式
                Self::interactive_mode(cli)?;
            }
        }
        
        Ok(())
    }
    
    /// 处理提取命令
    fn handle_extract(
        input: PathBuf,
        output: Option<PathBuf>,
        unique: bool,
        auto_check: bool,
        mode: &str,
    ) -> Result<()> {
        println!("📝 开始提取单词...");
        
        let include_phrases = mode == "full";
        let extractor = WordExtractor::new(unique, include_phrases);
        let result = extractor.extract_from_file(&input)?;
        
        println!("✅ 提取完成！");
        println!("   单词数: {}", result.total_words);
        if include_phrases {
            println!("   短语数: {}", result.total_phrases);
        }
        
        // 确定输出文件名
        let output_file = output.unwrap_or_else(|| {
            let base = input.file_stem().unwrap().to_str().unwrap();
            let suffix = match mode {
                "words_only" => "_单词.txt",
                "with_meaning" => "_单词词义.txt",
                _ => "_完整.txt",
            };
            PathBuf::from(format!("{}{}", base, suffix))
        });
        
        // 保存文件
        if mode == "words_only" {
            extractor.save_words_only(&result.words, &output_file)?;
        } else {
            extractor.save_with_meaning(&result, &output_file)?;
        }
        
        println!("💾 已保存到: {:?}", output_file);
        
        // 自动核对
        if auto_check && mode == "words_only" {
            println!("\n🔍 开始自动核对...");
            let checker = BBDCChecker::new()?;
            let check_result = checker.check_words_file(&output_file)?;
            
            Self::print_check_result(&check_result);
            
            // LLM 自动更正
            if check_result.unrecognized_count > 0 {
                let llm = LLMCorrector::new()?;
                if llm.is_enabled() {
                    println!("\n🤖 开始 LLM 自动更正...");
                    Self::handle_llm_correction(&check_result, &llm)?;
                }
            }
        }
        
        Ok(())
    }
    
    /// 处理核对命令
    fn handle_check(input: PathBuf) -> Result<()> {
        println!("🔍 开始核对单词...");
        
        let checker = BBDCChecker::new()?;
        let result = checker.check_words_file(&input)?;
        
        Self::print_check_result(&result);
        
        Ok(())
    }
    
    /// 处理环境检查
    fn handle_env_check() -> Result<()> {
        println!("🔍 检查环境配置...\n");
        
        let (exists, path) = EnvLoader::check_env_file();
        
        if exists {
            println!("✅ 找到 .env 文件: {:?}", path.unwrap());
        } else {
            println!("❌ 未找到 .env 文件");
            println!("💡 请在以下位置之一创建 .env 文件：");
            println!("   - 可执行文件所在目录");
            println!("   - 当前工作目录");
        }
        
        println!("\n环境变量状态：");
        
        // 检查 SiliconFlow API
        if EnvLoader::exists("SILICONFLOW_API_KEY") {
            println!("✅ SILICONFLOW_API_KEY: 已设置");
        } else {
            println!("❌ SILICONFLOW_API_KEY: 未设置（LLM 功能将禁用）");
        }
        
        // 检查其他配置
        if let Ok(url) = EnvLoader::get("SILICONFLOW_BASE_URL", Some("default")) {
            println!("   SILICONFLOW_BASE_URL: {}", url);
        }
        
        if let Ok(model) = EnvLoader::get("SILICONFLOW_MODEL", Some("default")) {
            println!("   SILICONFLOW_MODEL: {}", model);
        }
        
        Ok(())
    }
    
    /// 交互模式
    fn interactive_mode(cli: Cli) -> Result<()> {
        println!("\n{}", "=".repeat(60));
        println!("           📚 单词提取工具 - Word Extractor");
        println!("           支持 Markdown 文件");
        println!("{}\n", "=".repeat(60));
        
        // 获取输入文件
        let input_file = if let Some(input) = cli.input {
            input
        } else {
            println!("📂 请输入 Markdown 文件路径:");
            let mut input = String::new();
            io::stdin().read_line(&mut input)?;
            PathBuf::from(input.trim().trim_matches('"'))
        };
        
        if !input_file.exists() {
            return Err(Error::Other(format!("文件不存在: {:?}", input_file)));
        }
        
        // 确定输出文件
        let output_file = if let Some(output) = cli.output {
            output
        } else {
            let base = input_file.file_stem().unwrap().to_str().unwrap();
            PathBuf::from(format!("{}_单词.txt", base))
        };
        
        println!("\n🔄 正在提取单词...");
        
        let extractor = WordExtractor::new(cli.unique, cli.include_phrases);
        let result = extractor.extract_from_file(&input_file)?;
        
        println!("✅ 提取完成！共 {} 个单词", result.total_words);
        
        extractor.save_words_only(&result.words, &output_file)?;
        println!("💾 已保存到: {:?}", output_file);
        
        // 自动核对
        if cli.auto_check {
            println!("\n🔍 正在自动核对...");
            let checker = BBDCChecker::new()?;
            let check_result = checker.check_words_file(&output_file)?;
            
            Self::print_check_result(&check_result);
        }
        
        println!("\n✨ 完成！");
        
        Ok(())
    }
    
    /// 打印核对结果
    fn print_check_result(result: &crate::bbdc_checker::CheckResult) {
        println!("\n{}", "=".repeat(60));
        println!("📊 不背单词词书核对结果");
        println!("{}", "=".repeat(60));
        
        println!("\n📈 统计信息:");
        println!("  总单词数: {}", result.total_count);
        println!("  识别成功: {}", result.recognized_count);
        println!("  识别失败: {}", result.unrecognized_count);
        
        if result.total_count > 0 {
            let success_rate = result.recognized_count as f64 / result.total_count as f64 * 100.0;
            println!("  识别成功率: {:.1}%", success_rate);
        }
        
        if !result.unrecognized_words.is_empty() {
            println!("\n❌ 识别失败的单词（前10个）:");
            for (i, word) in result.unrecognized_words.iter().take(10).enumerate() {
                println!("  {:2}. {}", i + 1, word);
            }
            if result.unrecognized_words.len() > 10 {
                println!("  ... 还有 {} 个", result.unrecognized_words.len() - 10);
            }
        }
    }
    
    /// 处理 LLM 自动更正
    fn handle_llm_correction(
        check_result: &crate::bbdc_checker::CheckResult,
        llm: &LLMCorrector,
    ) -> Result<()> {
        println!("正在处理 {} 个识别失败的单词...", check_result.unrecognized_count);
        
        let mut corrections = Vec::new();
        
        for (i, word) in check_result.unrecognized_words.iter().enumerate() {
            print!("[{}/{}] 处理: {} ... ", 
                i + 1, check_result.unrecognized_count, word);
            io::stdout().flush()?;
            
            let result = llm.correct_word(word, "")?;
            
            if result.success && result.corrected != result.original {
                println!("✓ → {}", result.corrected);
                corrections.push(result);
            } else {
                println!("×");
            }
            
            std::thread::sleep(std::time::Duration::from_millis(500));
        }
        
        if !corrections.is_empty() {
            println!("\n✅ 成功更正 {} 个单词", corrections.len());
            for corr in &corrections {
                println!("  {} → {} ({})", corr.original, corr.corrected, corr.confidence);
            }
        } else {
            println!("\n⚠️  未能自动更正任何单词");
        }
        
        Ok(())
    }
}

