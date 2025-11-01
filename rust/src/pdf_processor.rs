//! PDF 处理模块
//! 
//! 通过 Mineru API 将 PDF 转换为 Markdown

use crate::{Error, Result, EnvLoader};
use reqwest::blocking::{Client, multipart};
use serde::Deserialize;
use std::fs;
use std::path::{Path, PathBuf};
use std::thread;
use std::time::Duration;

/// Mineru API 客户端
pub struct MineruClient {
    client: Client,
    api_token: String,
    base_url: String,
}

/// 任务创建响应
#[derive(Debug, Deserialize)]
struct TaskResponse {
    code: i32,
    message: String,
    data: Option<TaskData>,
}

#[derive(Debug, Deserialize)]
struct TaskData {
    task_id: String,
}

/// 任务状态响应
#[derive(Debug, Deserialize)]
struct TaskStatusResponse {
    code: i32,
    message: String,
    data: Option<TaskStatusData>,
}

#[derive(Debug, Deserialize)]
struct TaskStatusData {
    status: String,
    progress: Option<f64>,
    result_url: Option<String>,
}

impl MineruClient {
    /// 创建新的 Mineru 客户端
    pub fn new() -> Result<Self> {
        let api_token = EnvLoader::get_optional("MINERU_API_TOKEN")
            .ok_or_else(|| Error::EnvVar(
                "未设置 MINERU_API_TOKEN\n\
                 请在 .env 文件中添加: MINERU_API_TOKEN=your_token_here\n\
                 获取地址: https://mineru.net/".to_string()
            ))?;
        
        let base_url = EnvLoader::get(
            "MINERU_BASE_URL",
            Some("https://mineru.net/api/v4"),
        )?;
        
        let client = Client::builder()
            .timeout(Duration::from_secs(300))
            .build()?;
        
        log::info!("Mineru API 客户端初始化成功");
        
        Ok(Self {
            client,
            api_token,
            base_url,
        })
    }
    
    /// 上传 PDF 文件并开始解析
    pub fn process_pdf<P: AsRef<Path>>(
        &self,
        pdf_path: P,
        output_dir: Option<P>,
        is_ocr: bool,
    ) -> Result<PathBuf> {
        let pdf_path = pdf_path.as_ref();
        
        log::info!("开始处理 PDF: {:?}", pdf_path);
        
        // 1. 上传 PDF
        log::info!("📤 正在上传 PDF 文件...");
        let task_id = self.upload_pdf(pdf_path, is_ocr)?;
        log::info!("✅ 上传成功，任务ID: {}", task_id);
        
        // 2. 轮询任务状态
        log::info!("⏳ 等待解析完成...");
        let result_url = self.wait_for_task(&task_id)?;
        log::info!("✅ 解析完成");
        
        // 3. 下载结果
        log::info!("📥 正在下载结果...");
        let zip_data = self.download_result(&result_url)?;
        log::info!("✅ 下载完成");
        
        // 4. 解压并提取 markdown
        let output_dir = output_dir
            .map(|p| p.as_ref().to_path_buf())
            .unwrap_or_else(|| {
                pdf_path
                    .parent()
                    .unwrap_or_else(|| Path::new("."))
                    .to_path_buf()
            });
        
        log::info!("📦 正在解压文件...");
        let markdown_path = self.extract_markdown(&zip_data, &output_dir)?;
        log::info!("✅ PDF 处理完成: {:?}", markdown_path);
        
        Ok(markdown_path)
    }
    
    /// 上传 PDF 文件
    fn upload_pdf<P: AsRef<Path>>(&self, pdf_path: P, is_ocr: bool) -> Result<String> {
        let pdf_path = pdf_path.as_ref();
        
        if !pdf_path.exists() {
            return Err(Error::Other(format!("PDF 文件不存在: {:?}", pdf_path)));
        }
        
        let file_name = pdf_path
            .file_name()
            .and_then(|n| n.to_str())
            .ok_or_else(|| Error::Other("无效的文件名".to_string()))?;
        
        let file_content = fs::read(pdf_path)?;
        
        // 构建 multipart 表单
        let form = multipart::Form::new()
            .part(
                "file",
                multipart::Part::bytes(file_content)
                    .file_name(file_name.to_string())
                    .mime_str("application/pdf")?,
            );
        
        // 发送请求
        let url = format!("{}/extract/task/upload", self.base_url);
        let response = self
            .client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_token))
            .query(&[("is_ocr", is_ocr.to_string())])
            .multipart(form)
            .send()?;
        
        if !response.status().is_success() {
            return Err(Error::Other(format!(
                "上传失败: HTTP {}",
                response.status()
            )));
        }
        
        let task_response: TaskResponse = response.json()?;
        
        if task_response.code != 200 {
            return Err(Error::Other(format!(
                "API 错误: {}",
                task_response.message
            )));
        }
        
        let task_id = task_response
            .data
            .ok_or_else(|| Error::Other("API 响应中没有 task_id".to_string()))?
            .task_id;
        
        Ok(task_id)
    }
    
    /// 等待任务完成
    fn wait_for_task(&self, task_id: &str) -> Result<String> {
        let url = format!("{}/extract/task/status", self.base_url);
        let max_attempts = 180; // 最多等待30分钟（每10秒轮询一次）
        
        for attempt in 1..=max_attempts {
            thread::sleep(Duration::from_secs(10));
            
            let response = self
                .client
                .get(&url)
                .header("Authorization", format!("Bearer {}", self.api_token))
                .query(&[("task_id", task_id)])
                .send()?;
            
            if !response.status().is_success() {
                log::warn!("查询状态失败: HTTP {}", response.status());
                continue;
            }
            
            let status_response: TaskStatusResponse = response.json()?;
            
            if status_response.code != 200 {
                return Err(Error::Other(format!(
                    "查询状态失败: {}",
                    status_response.message
                )));
            }
            
            if let Some(data) = status_response.data {
                let progress = data.progress.unwrap_or(0.0);
                log::info!("进度: {:.1}% - 状态: {}", progress, data.status);
                
                match data.status.as_str() {
                    "completed" => {
                        if let Some(result_url) = data.result_url {
                            return Ok(result_url);
                        } else {
                            return Err(Error::Other("任务完成但没有结果URL".to_string()));
                        }
                    }
                    "failed" => {
                        return Err(Error::Other("任务失败".to_string()));
                    }
                    "processing" | "pending" => {
                        // 继续等待
                    }
                    _ => {
                        log::warn!("未知状态: {}", data.status);
                    }
                }
            }
            
            if attempt % 6 == 0 {
                log::info!("已等待 {} 分钟...", attempt / 6);
            }
        }
        
        Err(Error::Other("任务超时（30分钟）".to_string()))
    }
    
    /// 下载结果
    fn download_result(&self, result_url: &str) -> Result<Vec<u8>> {
        let response = self.client.get(result_url).send()?;
        
        if !response.status().is_success() {
            return Err(Error::Other(format!(
                "下载失败: HTTP {}",
                response.status()
            )));
        }
        
        Ok(response.bytes()?.to_vec())
    }
    
    /// 解压并提取 markdown 文件
    fn extract_markdown(&self, zip_data: &[u8], output_dir: &Path) -> Result<PathBuf> {
        use zip::ZipArchive;
        use std::io::Cursor;
        
        let reader = Cursor::new(zip_data);
        let mut archive = ZipArchive::new(reader)
            .map_err(|e| Error::Other(format!("解压失败: {}", e)))?;
        
        fs::create_dir_all(output_dir)?;
        
        let mut markdown_files = Vec::new();
        
        // 解压所有文件
        for i in 0..archive.len() {
            let mut file = archive.by_index(i)
                .map_err(|e| Error::Other(format!("读取压缩文件失败: {}", e)))?;
            
            let file_name = file.name().to_string();
            
            if file.is_dir() {
                continue;
            }
            
            let output_path = output_dir.join(&file_name);
            
            if let Some(parent) = output_path.parent() {
                fs::create_dir_all(parent)?;
            }
            
            let mut output_file = fs::File::create(&output_path)?;
            std::io::copy(&mut file, &mut output_file)?;
            
            // 记录 markdown 文件
            if file_name.ends_with(".md") {
                markdown_files.push(output_path);
            }
        }
        
        // 返回第一个 markdown 文件
        markdown_files
            .into_iter()
            .next()
            .ok_or_else(|| Error::Other("压缩包中没有找到 markdown 文件".to_string()))
    }
}

impl Default for MineruClient {
    fn default() -> Self {
        Self::new().expect("创建 MineruClient 失败")
    }
}

