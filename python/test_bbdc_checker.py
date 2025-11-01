#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试不背单词词书核对工具
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bbdc_word_checker import BBDCWordChecker
    print("✅ 成功导入BBDCWordChecker类")
    
    # 创建实例
    checker = BBDCWordChecker()
    print("✅ 成功创建BBDCWordChecker实例")
    
    # 测试解析结果功能
    test_result = {
        "result_code": 200,
        "data_kind": "",
        "data_version": "1.0",
        "data_body": {
            "unknowList": "test1,test2,test3",
            "knowList": "known1,known2,known3"
        }
    }
    
    parsed = checker.parse_result(test_result)
    print("✅ 成功解析测试结果")
    print(f"   未知单词数: {parsed['unknown_count']}")
    print(f"   已知单词数: {parsed['known_count']}")
    
    print("\n🎉 所有测试通过！脚本可以正常使用。")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 测试失败: {e}")


