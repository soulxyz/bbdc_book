//! BBDC Word Tool - 不背单词词书制作工具
//! 
//! 这是一个从 Markdown 文件中提取单词并自动核对的工具

pub mod env_loader;
pub mod word_extractor;
pub mod bbdc_checker;
pub mod llm_corrector;
pub mod cli;

// 重新导出常用类型
pub use env_loader::EnvLoader;
pub use word_extractor::{WordExtractor, Word, ExtractResult};
pub use bbdc_checker::{BBDCChecker, CheckResult};
pub use llm_corrector::{LLMCorrector, CorrectionResult};

/// 错误类型
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("文件读取错误: {0}")]
    FileRead(#[from] std::io::Error),
    
    #[error("HTTP请求错误: {0}")]
    Http(#[from] reqwest::Error),
    
    #[error("JSON解析错误: {0}")]
    JsonParse(#[from] serde_json::Error),
    
    #[error("环境变量错误: {0}")]
    EnvVar(String),
    
    #[error("解析错误: {0}")]
    Parse(String),
    
    #[error("其他错误: {0}")]
    Other(String),
}

pub type Result<T> = std::result::Result<T, Error>;

