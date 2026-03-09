#!/usr/bin/env python3
"""文献引用获取器 - 从 PubMed/Google Scholar 等获取标准引用格式"""

import requests
import re
from urllib.parse import quote
import json
import sys

def search_crossref(title: str) -> dict:
    """通过 CrossRef API 查找 DOI 和引用信息"""
    search_url = f"https://api.crossref.org/works?query.title={quote(title)}&rows=5"
    
    try:
        response = requests.get(search_url, timeout=10)
        data = response.json()
        
        if data.get("status") == "ok" and data.get("message", {}).get("items"):
            items = data["message"]["items"]
            for item in items:
                # 匹配度检查
                item_title = item.get("title", [""])[0].lower()
                if similar(title.lower(), item_title, threshold=0.7):
                    return {
                        "doi": item.get("DOI"),
                        "title": item.get("title", [""])[0],
                        "authors": format_authors(item.get("author", [])),
                        "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                        "year": item.get("created", {}).get("date-parts", [[None]])[0][0],
                        "source": "CrossRef"
                    }
    except Exception as e:
        pass
    
    return {}

def search_pubmed(title: str) -> dict:
    """通过 PubMed API 查找文献"""
    # 先搜索获取 PMID
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={quote(title)}&retmax=5&retmode=json"
    
    try:
        response = requests.get(search_url, timeout=10)
        data = response.json()
        
        if data.get("esearchresult", {}).get("idlist"):
            pmid = data["esearchresult"]["idlist"][0]
            
            # 获取详细信息
            fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
            response = requests.get(fetch_url, timeout=10)
            data = response.json()
            
            if data.get("result", {}).get(pmid):
                item = data["result"][pmid]
                return {
                    "doi": item.get("doi", ""),
                    "title": item.get("title", ""),
                    "authors": format_authors_pubmed(item.get("authors", [])),
                    "journal": item.get("fulljournalname", ""),
                    "year": item.get("pubdate", "")[:4] if item.get("pubdate") else "",
                    "pmid": pmid,
                    "source": "PubMed"
                }
    except Exception as e:
        pass
    
    return {}

def similar(s1: str, s2: str, threshold: float = 0.7) -> bool:
    """简单的字符串相似度检查"""
    words1 = set(s1.split())
    words2 = set(s2.split())
    if not words1 or not words2:
        return False
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union >= threshold if union > 0 else False

def format_authors(authors: list) -> str:
    """格式化作者列表"""
    if not authors:
        return ""
    
    formatted = []
    for author in authors[:10]:  # 最多 10 位作者
        given = author.get("given", "")
        family = author.get("family", "")
        if given and family:
            formatted.append(f"{family}, {given[0]}.")
        elif family:
            formatted.append(family)
    
    if len(formatted) > 1:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return formatted[0] if formatted else ""

def format_authors_pubmed(authors: list) -> str:
    """格式化 PubMed 作者列表"""
    if not authors:
        return ""
    
    formatted = []
    for author in authors[:10]:
        name = author.get("name", "")
        if name:
            # 转换为 Last, F. 格式
            parts = name.split()
            if len(parts) >= 2:
                formatted.append(f"{parts[-1]}, {''.join(p[0] + '.' for p in parts[:-1])}")
            else:
                formatted.append(name)
    
    if len(formatted) > 1:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return formatted[0] if formatted else ""

def generate_citation(info: dict) -> str:
    """生成 Nature/APA 格式引用"""
    if not info:
        return ""
    
    authors = info.get("authors", "Unknown")
    title = info.get("title", "Unknown title")
    journal = info.get("journal", "Unknown journal")
    year = info.get("year", "n.d.")
    doi = info.get("doi", "")
    
    citation = f"{authors}. {title}. {journal} ({year})."
    
    if doi:
        if not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        citation += f" {doi}"
    
    return citation

def fetch_citation(title: str, url: str = "") -> dict:
    """主函数：尝试多种来源获取引用"""
    # 1. 先尝试 CrossRef
    result = search_crossref(title)
    if result:
        result["citation"] = generate_citation(result)
        return result
    
    # 2. 尝试 PubMed
    result = search_pubmed(title)
    if result:
        result["citation"] = generate_citation(result)
        return result
    
    # 3. 都失败，返回基本信息
    return {
        "title": title,
        "citation": f"Unknown. {title}. Retrieved from {url}" if url else f"Unknown. {title}.",
        "source": "Fallback"
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        title = " ".join(sys.argv[1:])
        result = fetch_citation(title)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("用法：fetch_citation.py <论文标题>")
