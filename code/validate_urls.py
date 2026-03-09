#!/usr/bin/env python3
"""URL 验证器 - 检查链接是否有效且指向实际内容"""

import requests
from urllib.parse import urlparse
import sys
import time

def is_valid_url(url: str, timeout: int = 10) -> dict:
    """
    验证 URL 是否有效且指向实际内容
    返回：{"valid": bool, "status": int, "title": str, "error": str}
    """
    result = {"valid": False, "status": 0, "title": "", "error": "", "url": url}
    
    if not url.startswith(("http://", "https://")):
        result["error"] = "无效的 URL 格式"
        return result
    
    try:
        # 先检查是否是已知的无效页面类型
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # 跳过期刊首页、搜索页等
        invalid_patterns = [
            "/search", "/results", "/authors/", "/journal/", 
            "/browse/", "/issues/", "/volume/"
        ]
        
        for pattern in invalid_patterns:
            if pattern in path:
                result["error"] = "链接指向首页/搜索页，非具体文章"
                return result
        
        # 发送 HEAD 请求先检查状态
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LifeScienceDailyBot/1.0)"
        }
        
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code >= 400:
            # HEAD 失败，尝试 GET
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        result["status"] = response.status_code
        
        if response.status_code >= 400:
            result["error"] = f"HTTP 错误：{response.status_code}"
            return result
        
        # 提取标题
        if "text/html" in response.headers.get("Content-Type", ""):
            import re
            title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                result["title"] = title_match.group(1).strip()
        
        # 检查是否是实际文章页面
        content_indicators = [
            "abstract", "doi", "author", "published", "citation",
            "摘要", "作者", "发表", "引用"
        ]
        
        content_score = sum(1 for indicator in content_indicators 
                          if indicator in response.text.lower())
        
        if content_score < 2:
            result["error"] = "页面内容不足以确认为文章页"
            return result
        
        result["valid"] = True
        return result
        
    except requests.exceptions.Timeout:
        result["error"] = "请求超时"
        return result
    except requests.exceptions.ConnectionError:
        result["error"] = "连接失败"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

def validate_multiple(urls: list, delay: float = 0.5) -> list:
    """批量验证 URL，带延迟避免被封"""
    results = []
    for url in urls:
        result = is_valid_url(url)
        results.append(result)
        time.sleep(delay)
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = is_valid_url(url)
        print(f"URL: {url}")
        print(f"有效：{result['valid']}")
        print(f"状态码：{result['status']}")
        print(f"标题：{result['title'][:100] if result['title'] else 'N/A'}")
        if result['error']:
            print(f"错误：{result['error']}")
    else:
        print("用法：validate_urls.py <url>")
