//! LLM 自动更正模块
//! 
//! 使用 SiliconFlow API 自动更正拼写错误的单词

use crate::{Error, Result, EnvLoader};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;

/// LLM 更正器
pub struct LLMCorrector {
    client: Client,
    api_key: Option<String>,
    base_url: String,
    model: String,
}

/// 更正结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrectionResult {
    pub success: bool,
    pub original: String,
    pub corrected: String,
    pub confidence: String,
    pub reason: String,
}

/// 候选词信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Candidate {
    pub word: String,
    pub reason: String,
    pub verified: bool,
}

/// 候选词生成结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CandidatesResult {
    pub success: bool,
    pub original: String,
    pub candidates: Vec<Candidate>,
    pub reason: String,
}

/// API 响应结构
#[derive(Debug, Deserialize)]
struct ApiResponse {
    choices: Vec<Choice>,
}

#[derive(Debug, Deserialize)]
struct Choice {
    message: Message,
}

#[derive(Debug, Deserialize)]
struct Message {
    content: String,
}

/// LLM 响应结构
#[derive(Debug, Deserialize)]
struct LLMCorrectionResponse {
    corrected: String,
    confidence: String,
    reason: String,
}

#[derive(Debug, Deserialize)]
struct LLMCandidatesResponse {
    candidates: Vec<CandidateInfo>,
}

#[derive(Debug, Deserialize)]
struct CandidateInfo {
    word: String,
    reason: String,
}

impl LLMCorrector {
    /// 创建新的 LLM 更正器
    pub fn new() -> Result<Self> {
        let api_key = EnvLoader::get_optional("SILICONFLOW_API_KEY");
        
        if api_key.is_none() {
            log::warn!("⚠️  未设置 SILICONFLOW_API_KEY，LLM自动更正功能将被禁用");
            log::warn!("💡 在 .env 文件中添加: SILICONFLOW_API_KEY=your_key_here");
            log::warn!("   获取地址: https://cloud.siliconflow.cn/");
        }
        
        let base_url = EnvLoader::get(
            "SILICONFLOW_BASE_URL",
            Some("https://api.siliconflow.cn/v1/chat/completions"),
        )?;
        
        let model = EnvLoader::get(
            "SILICONFLOW_MODEL",
            Some("Qwen/Qwen2.5-7B-Instruct"),
        )?;
        
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()?;
        
        Ok(Self {
            client,
            api_key,
            base_url,
            model,
        })
    }
    
    /// 检查 LLM 功能是否启用
    pub fn is_enabled(&self) -> bool {
        self.api_key.is_some()
    }
    
    /// 更正单词
    pub fn correct_word(&self, word: &str, meaning: &str) -> Result<CorrectionResult> {
        if !self.is_enabled() {
            return Ok(CorrectionResult {
                success: false,
                original: word.to_string(),
                corrected: word.to_string(),
                confidence: "none".to_string(),
                reason: "LLM功能未启用".to_string(),
            });
        }
        
        let prompt = format!(
            r#"请检查以下英语单词是否有拼写错误，如果有错误请给出正确的拼写。

原始单词: {}
中文释义: {}

请以JSON格式返回结果，包含以下字段：
- corrected: 更正后的单词（如果没有错误则返回原单词）
- confidence: 置信度，可选值为 "high"（高）、"medium"（中）、"low"（低）
- reason: 简短说明更正的原因或判断没有错误的依据

示例输出：
{{"corrected": "example", "confidence": "high", "reason": "原单词拼写正确"}}
或
{{"corrected": "receive", "confidence": "high", "reason": "修正了i和e的顺序"}}

只返回JSON，不要有其他内容。"#,
            word, meaning
        );
        
        let response = self.call_llm(&prompt)?;
        self.parse_correction_response(word, &response)
    }
    
    /// 生成候选词
    pub fn generate_candidates(&self, word: &str, meaning: &str) -> Result<CandidatesResult> {
        if !self.is_enabled() {
            return Ok(CandidatesResult {
                success: false,
                original: word.to_string(),
                candidates: vec![],
                reason: "LLM功能未启用".to_string(),
            });
        }
        
        let prompt = format!(
            r#"对于无法识别的英语单词"{}"（释义：{}），请生成3-5个可能的候选词。

候选词可以是：
1. 该单词的词根或基础形式
2. 该单词去掉前缀/后缀后的形式
3. 意思相近的常见单词
4. 可能的正确拼写（如果原词有拼写错误）

要求：
- 候选词必须是真实存在的常见英语单词
- 优先选择更基础、更常用的词汇
- 保持与原释义的相关性

请以JSON格式返回，包含：
- candidates: 候选词列表（每个包含word和reason字段）

示例输出：
{{
  "candidates": [
    {{"word": "system", "reason": "supersystem的词根"}},
    {{"word": "efficient", "reason": "ineffectively的反义词根"}},
    {{"word": "finance", "reason": "finanzially的词根"}}
  ]
}}

只返回JSON，不要其他内容。"#,
            word, meaning
        );
        
        let response = self.call_llm(&prompt)?;
        self.parse_candidates_response(word, &response)
    }
    
    /// 调用 LLM API
    fn call_llm(&self, prompt: &str) -> Result<String> {
        let api_key = self.api_key.as_ref().ok_or_else(|| 
            Error::EnvVar("SILICONFLOW_API_KEY 未设置".to_string())
        )?;
        
        let payload = json!({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的英语单词拼写检查助手。你的任务是识别和修正英语单词中的拼写错误。只返回JSON格式的结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 200
        });
        
        let response = self
            .client
            .post(&self.base_url)
            .header("Authorization", format!("Bearer {}", api_key))
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()?;
        
        if !response.status().is_success() {
            return Err(Error::Other(format!(
                "LLM API 请求失败: HTTP {}",
                response.status()
            )));
        }
        
        let api_response: ApiResponse = response.json()?;
        
        api_response
            .choices
            .first()
            .map(|c| c.message.content.clone())
            .ok_or_else(|| Error::Other("LLM 响应为空".to_string()))
    }
    
    /// 解析更正响应
    fn parse_correction_response(&self, original: &str, content: &str) -> Result<CorrectionResult> {
        let content = content.trim();
        
        // 提取 JSON（可能包含在代码块中）
        let json_content = if content.contains("```json") {
            content
                .split("```json")
                .nth(1)
                .and_then(|s| s.split("```").next())
                .unwrap_or(content)
                .trim()
        } else if content.contains("```") {
            content
                .split("```")
                .nth(1)
                .and_then(|s| s.split("```").next())
                .unwrap_or(content)
                .trim()
        } else {
            content
        };
        
        match serde_json::from_str::<LLMCorrectionResponse>(json_content) {
            Ok(resp) => Ok(CorrectionResult {
                success: true,
                original: original.to_string(),
                corrected: resp.corrected,
                confidence: resp.confidence,
                reason: resp.reason,
            }),
            Err(_) => {
                // 尝试从文本中提取单词
                let words: Vec<&str> = content.split_whitespace().collect();
                if let Some(word) = words.first() {
                    Ok(CorrectionResult {
                        success: true,
                        original: original.to_string(),
                        corrected: word.trim_matches(|c: char| !c.is_alphabetic()).to_string(),
                        confidence: "low".to_string(),
                        reason: "从响应中提取的单词".to_string(),
                    })
                } else {
                    Ok(CorrectionResult {
                        success: false,
                        original: original.to_string(),
                        corrected: original.to_string(),
                        confidence: "none".to_string(),
                        reason: "无法解析LLM响应".to_string(),
                    })
                }
            }
        }
    }
    
    /// 解析候选词响应
    fn parse_candidates_response(&self, original: &str, content: &str) -> Result<CandidatesResult> {
        let content = content.trim();
        
        // 提取 JSON
        let json_content = if content.contains("```json") {
            content
                .split("```json")
                .nth(1)
                .and_then(|s| s.split("```").next())
                .unwrap_or(content)
                .trim()
        } else if content.contains("```") {
            content
                .split("```")
                .nth(1)
                .and_then(|s| s.split("```").next())
                .unwrap_or(content)
                .trim()
        } else {
            content
        };
        
        match serde_json::from_str::<LLMCandidatesResponse>(json_content) {
            Ok(resp) => {
                let candidates = resp
                    .candidates
                    .into_iter()
                    .map(|c| Candidate {
                        word: c.word,
                        reason: c.reason,
                        verified: false,
                    })
                    .collect();
                
                Ok(CandidatesResult {
                    success: true,
                    original: original.to_string(),
                    candidates,
                    reason: "success".to_string(),
                })
            }
            Err(e) => Ok(CandidatesResult {
                success: false,
                original: original.to_string(),
                candidates: vec![],
                reason: format!("解析响应失败: {}", e),
            }),
        }
    }
}

impl Default for LLMCorrector {
    fn default() -> Self {
        Self::new().expect("创建 LLMCorrector 失败")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_corrector_creation() {
        let corrector = LLMCorrector::new();
        assert!(corrector.is_ok());
    }
}

