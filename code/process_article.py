#!/usr/bin/env python3
"""用户分享文章处理器"""

import json
import re
from datetime import datetime
from pathlib import Path
import requests

USER_SHARE_DIR = Path.home() / "advances" / "usershare"
USER_SHARE_DIR.mkdir(parents=True, exist_ok=True)

def is_research(url, content):
    """判断是否研究类"""
    score = 0
    academic = ["nature.com", "science.org", "cell.com", "arxiv.org", "pubmed"]
    for d in academic:
        if d in url.lower():
            score += 3
    research_words = ["abstract", "doi", "methods", "results", "abstract", "doi", "方法", "结果"]
    for w in research_words:
        if w in content.lower():
            score += 1
    return score >= 4

def extract_metadata(url, content):
    """提取元数据"""
    meta = {"title": "", "authors": "", "org": "", "doi": ""}
    
    # 标题
    m = re.search(r'<title[^>]*>(.*?)</title>', content, re.I)
    if m:
        meta["title"] = m.group(1).strip()
    
    # DOI
    m = re.search(r'10\.\d{4,}/[^\s"\']+', content)
    if m:
        meta["doi"] = m.group(0)
    
    # 机构
    m = re.search(r'([A-Z][a-z]+ (?:University|Institute|Center))', content)
    if m:
        meta["org"] = m.group(1)
    
    return meta

def get_citation(title, url):
    """获取引用格式（简化版）"""
    # 实际应调用 fetch_citation.py，这里简化
    return f"Unknown. {title}. Retrieved from {url}"

def process(url):
    """处理文章"""
    print(f"处理：{url}")
    
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        content = r.text[:50000]  # 限制长度
    except Exception as e:
        return {"error": str(e)}
    
    is_res = is_research(url, content)
    meta = extract_metadata(url, content)
    
    # 生成摘要
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text).strip()
    summary = text[:200] + "..." if len(text) > 200 else text
    
    # 归档
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', meta.get("title", "unknown")[:30])
    archive = USER_SHARE_DIR / f"{today}_{safe_title}.md"
    
    content_md = f"""# {meta.get('title', '未知标题')}

**日期**: {today}
**类型**: {"研究类" if is_res else "其它类"}
**链接**: {url}

"""
    
    if is_res:
        citation = get_citation(meta.get("title", ""), url)
        content_md += f"""## 引用
{citation}

## 元数据
- 作者：{meta.get('authors', '未知')}
- 机构：{meta.get('org', '未知')}
- DOI: {meta.get('doi', '未知')}

"""
    
    content_md += f"""## 摘要
{summary}
"""
    
    with open(archive, "w") as f:
        f.write(content_md)
    
    return {
        "is_research": is_res,
        "title": meta.get("title", ""),
        "org": meta.get("org", ""),
        "doi": meta.get("doi", ""),
        "summary": summary[:100],
        "archive": str(archive)
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = process(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("用法：process_article.py <url>")
