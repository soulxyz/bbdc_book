//! 环境变量加载模块
//! 
//! 支持从 .env 文件和系统环境变量加载配置

use crate::{Error, Result};
use std::env;
use std::path::PathBuf;

/// 环境变量加载器
pub struct EnvLoader;

impl EnvLoader {
    /// 初始化环境变量
    /// 
    /// 会按以下顺序查找 .env 文件：
    /// 1. 当前可执行文件所在目录
    /// 2. 当前工作目录
    /// 3. 父目录
    pub fn init() -> Result<()> {
        // 尝试多个位置加载 .env 文件
        let search_paths = Self::get_search_paths();
        
        for path in &search_paths {
            let env_file = path.join(".env");
            if env_file.exists() {
                log::info!("找到 .env 文件: {:?}", env_file);
                dotenv::from_path(&env_file).ok();
                return Ok(());
            }
        }
        
        log::warn!("未找到 .env 文件，将只使用系统环境变量");
        Ok(())
    }
    
    /// 获取环境变量，带默认值
    pub fn get(key: &str, default: Option<&str>) -> Result<String> {
        env::var(key)
            .or_else(|_| default.ok_or_else(|| 
                Error::EnvVar(format!("环境变量 {} 未设置", key))
            ).map(|s| s.to_string()))
    }
    
    /// 获取可选的环境变量
    pub fn get_optional(key: &str) -> Option<String> {
        env::var(key).ok()
    }
    
    /// 检查环境变量是否存在
    pub fn exists(key: &str) -> bool {
        env::var(key).is_ok()
    }
    
    /// 获取搜索路径列表
    fn get_search_paths() -> Vec<PathBuf> {
        let mut paths = Vec::new();
        
        // 1. 当前可执行文件所在目录
        if let Ok(exe_path) = env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                paths.push(exe_dir.to_path_buf());
            }
        }
        
        // 2. 当前工作目录
        if let Ok(cwd) = env::current_dir() {
            paths.push(cwd.clone());
            
            // 3. 父目录
            if let Some(parent) = cwd.parent() {
                paths.push(parent.to_path_buf());
            }
        }
        
        paths
    }
    
    /// 检查 .env 文件是否存在
    pub fn check_env_file() -> (bool, Option<PathBuf>) {
        for path in Self::get_search_paths() {
            let env_file = path.join(".env");
            if env_file.exists() {
                return (true, Some(env_file));
            }
        }
        (false, None)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_get_with_default() {
        let result = EnvLoader::get("NONEXISTENT_VAR", Some("default_value"));
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "default_value");
    }
}

