//! 不背单词词书核对模块
//! 
//! 调用不背单词 API 检查单词是否被识别

use crate::{Error, Result, Word};
use reqwest::blocking::{Client, multipart};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

/// 不背单词核对器
pub struct BBDCChecker {
    client: Client,
    submit_url: String,
}

/// 核对结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckResult {
    pub recognized_words: Vec<String>,
    pub unrecognized_words: Vec<String>,
    pub recognized_count: usize,
    pub unrecognized_count: usize,
    pub total_count: usize,
}

/// API 响应结构
#[derive(Debug, Deserialize)]
struct ApiResponse {
    #[serde(rename = "data_body")]
    data_body: Option<DataBody>,
}

#[derive(Debug, Deserialize)]
struct DataBody {
    #[serde(rename = "knowList", default)]
    know_list: String,
    #[serde(rename = "unknowList", default)]
    unknow_list: String,
}

impl BBDCChecker {
    /// 创建新的核对器
    pub fn new() -> Result<Self> {
        let client = Client::builder()
            .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .build()?;
        
        Ok(Self {
            client,
            submit_url: "https://bbdc.cn/lexis/book/file/submit".to_string(),
        })
    }
    
    /// 上传单词文件进行核对
    pub fn check_words_file<P: AsRef<Path>>(&self, file_path: P) -> Result<CheckResult> {
        let file_path = file_path.as_ref();
        
        if !file_path.exists() {
            return Err(Error::Other(format!("文件不存在: {:?}", file_path)));
        }
        
        let file_name = file_path
            .file_name()
            .and_then(|n| n.to_str())
            .ok_or_else(|| Error::Other("无效的文件名".to_string()))?;
        
        let file_content = fs::read(file_path)?;
        
        log::info!("正在上传文件到不背单词API: {}", file_name);
        
        // 构建 multipart 表单
        let form = multipart::Form::new()
            .part(
                "file",
                multipart::Part::bytes(file_content)
                    .file_name(file_name.to_string())
                    .mime_str("text/plain")?,
            );
        
        // 发送请求
        let response = self
            .client
            .post(&self.submit_url)
            .header("Accept", "application/json, text/javascript, */*; q=0.01")
            .header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
            .header("Origin", "https://bbdc.cn")
            .header("Referer", "https://bbdc.cn/lexis_book_index")
            .header("X-Requested-With", "XMLHttpRequest")
            .multipart(form)
            .send()?;
        
        if !response.status().is_success() {
            return Err(Error::Other(format!(
                "API 请求失败: HTTP {}",
                response.status()
            )));
        }
        
        let api_response: ApiResponse = response.json()?;
        
        let data_body = api_response
            .data_body
            .ok_or_else(|| Error::Other("API 响应中没有 data_body".to_string()))?;
        
        let recognized_words: Vec<String> = data_body
            .know_list
            .split(',')
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.trim().to_string())
            .collect();
        
        let unrecognized_words: Vec<String> = data_body
            .unknow_list
            .split(',')
            .filter(|s| !s.trim().is_empty())
            .map(|s| s.trim().to_string())
            .collect();
        
        let recognized_count = recognized_words.len();
        let unrecognized_count = unrecognized_words.len();
        let total_count = recognized_count + unrecognized_count;
        
        log::info!(
            "核对完成: 识别 {}/{} ({:.1}%)",
            recognized_count,
            total_count,
            if total_count > 0 {
                recognized_count as f64 / total_count as f64 * 100.0
            } else {
                0.0
            }
        );
        
        Ok(CheckResult {
            recognized_words,
            unrecognized_words,
            recognized_count,
            unrecognized_count,
            total_count,
        })
    }
    
    /// 直接核对单词列表（创建临时文件）
    pub fn check_words(&self, words: &[String]) -> Result<CheckResult> {
        let temp_file = "temp_words_check.txt";
        let content = words.join("\n");
        fs::write(temp_file, content)?;
        
        let result = self.check_words_file(temp_file);
        
        // 清理临时文件
        let _ = fs::remove_file(temp_file);
        
        result
    }
    
    /// 核对 Word 结构体列表
    pub fn check_word_structs(&self, words: &[Word]) -> Result<CheckResult> {
        let word_list: Vec<String> = words.iter().map(|w| w.word.clone()).collect();
        self.check_words(&word_list)
    }
}

impl Default for BBDCChecker {
    fn default() -> Self {
        Self::new().expect("创建 BBDCChecker 失败")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_checker_creation() {
        let checker = BBDCChecker::new();
        assert!(checker.is_ok());
    }
}

