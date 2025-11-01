//! 单词提取模块
//! 
//! 从 Markdown 文件中的 HTML 表格提取单词

use crate::{Error, Result};
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::Path;

/// 单词数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Word {
    pub number: String,
    pub word: String,
    pub meaning: String,
    pub line_number: Option<usize>,
}

/// 短语数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Phrase {
    pub number: String,
    pub phrase: String,
    pub meaning: String,
}

/// 提取结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtractResult {
    pub words: Vec<Word>,
    pub phrases: Vec<Phrase>,
    pub total_words: usize,
    pub total_phrases: usize,
}

/// 单词提取器
pub struct WordExtractor {
    unique: bool,
    include_phrases: bool,
}

impl WordExtractor {
    /// 创建新的提取器
    pub fn new(unique: bool, include_phrases: bool) -> Self {
        Self { unique, include_phrases }
    }
    
    /// 从 Markdown 文件提取单词
    pub fn extract_from_file<P: AsRef<Path>>(&self, file_path: P) -> Result<ExtractResult> {
        let content = fs::read_to_string(file_path)?;
        self.extract_from_markdown(&content)
    }
    
    /// 从 Markdown 内容提取单词
    pub fn extract_from_markdown(&self, content: &str) -> Result<ExtractResult> {
        let document = Html::parse_document(content);
        
        // 查找所有表格
        let table_selector = Selector::parse("table")
            .map_err(|e| Error::Parse(format!("表格选择器错误: {:?}", e)))?;
        let row_selector = Selector::parse("tr")
            .map_err(|e| Error::Parse(format!("行选择器错误: {:?}", e)))?;
        let col_selector = Selector::parse("td")
            .map_err(|e| Error::Parse(format!("列选择器错误: {:?}", e)))?;
        
        let mut words = Vec::new();
        let mut phrases = Vec::new();
        let mut seen_words: HashSet<String> = HashSet::new();
        
        for table in document.select(&table_selector) {
            for row in table.select(&row_selector) {
                let cols: Vec<_> = row.select(&col_selector).collect();
                
                // 至少需要3列：序号、单词/短语、词义
                if cols.len() >= 3 {
                    let col1_text = cols[0].text().collect::<String>().trim().to_string();
                    let col2_text = cols[1].text().collect::<String>().trim().to_string();
                    let col3_text = cols[2].text().collect::<String>().trim().to_string();
                    
                    // 跳过表头行
                    if col1_text == "NO." || col1_text.is_empty() || col1_text.contains("补充区") {
                        continue;
                    }
                    
                    // 跳过表头
                    if col2_text == "单词" || col2_text == "短语" {
                        continue;
                    }
                    
                    // 跳过无效数据
                    if col2_text.is_empty() || !col1_text.chars().all(|c| c.is_numeric()) {
                        continue;
                    }
                    
                    // 判断是单词还是短语（通过空格判断）
                    if col2_text.contains(' ') || col2_text.contains('-') {
                        if self.include_phrases {
                            phrases.push(Phrase {
                                number: col1_text,
                                phrase: col2_text,
                                meaning: col3_text,
                            });
                        }
                    } else {
                        // 去重检查
                        if self.unique {
                            let word_lower = col2_text.to_lowercase();
                            if seen_words.contains(&word_lower) {
                                continue;
                            }
                            seen_words.insert(word_lower);
                        }
                        
                        words.push(Word {
                            number: col1_text,
                            word: col2_text,
                            meaning: col3_text,
                            line_number: None,
                        });
                    }
                }
            }
        }
        
        log::info!("提取到 {} 个单词", words.len());
        if self.include_phrases {
            log::info!("提取到 {} 个短语", phrases.len());
        }
        
        Ok(ExtractResult {
            total_words: words.len(),
            total_phrases: phrases.len(),
            words,
            phrases,
        })
    }
    
    /// 保存单词列表到文件（仅单词，每行一个）
    pub fn save_words_only<P: AsRef<Path>>(
        &self,
        words: &[Word],
        output_path: P,
    ) -> Result<()> {
        let content = words
            .iter()
            .map(|w| w.word.clone())
            .collect::<Vec<_>>()
            .join("\n");
        
        fs::write(output_path, content)?;
        Ok(())
    }
    
    /// 保存完整信息（单词+词义）
    pub fn save_with_meaning<P: AsRef<Path>>(
        &self,
        result: &ExtractResult,
        output_path: P,
    ) -> Result<()> {
        let mut content = String::new();
        
        content.push_str(&"=".repeat(50));
        content.push_str("\n单词列表\n");
        content.push_str(&"=".repeat(50));
        content.push_str("\n\n");
        
        for word in &result.words {
            content.push_str(&format!("{}. {}\t{}\n", word.number, word.word, word.meaning));
        }
        
        if self.include_phrases && !result.phrases.is_empty() {
            content.push_str("\n");
            content.push_str(&"=".repeat(50));
            content.push_str("\n短语列表\n");
            content.push_str(&"=".repeat(50));
            content.push_str("\n\n");
            
            for phrase in &result.phrases {
                content.push_str(&format!(
                    "{}. {}\t{}\n",
                    phrase.number, phrase.phrase, phrase.meaning
                ));
            }
        }
        
        fs::write(output_path, content)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_extract_from_markdown() {
        let markdown = r#"
<table>
<tr><td>NO.</td><td>单词</td><td>释义</td></tr>
<tr><td>1</td><td>hello</td><td>你好</td></tr>
<tr><td>2</td><td>world</td><td>世界</td></tr>
</table>
"#;
        
        let extractor = WordExtractor::new(false, false);
        let result = extractor.extract_from_markdown(markdown).unwrap();
        
        assert_eq!(result.words.len(), 2);
        assert_eq!(result.words[0].word, "hello");
        assert_eq!(result.words[1].word, "world");
    }
}

