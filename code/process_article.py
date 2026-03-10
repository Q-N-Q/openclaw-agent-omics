#!/usr/bin/env python3
"""用户分享文章处理器 - 增强版（带 Tavily 提取、OCR、URL 验证）"""

import json
import re
import os
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import urllib.parse
import time

sys.path.insert(0, str(Path(__file__).parent))

USER_SHARE_DIR = Path.home() / "advances" / "usershare"
USER_SHARE_DIR.mkdir(parents=True, exist_ok=True)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8080")

# 12 个主题
TOPICS = [
    "基因组学", "临床检测", "细胞组学", "时空组学",
    "合成生物学", "生命科学大模型", "细胞治疗", "类器官",
    "衰老与发育", "生命起源与极端环境生物", "脑科学", "脑健康"
]

TOPIC_KEYWORDS = {
    "基因组学": ["genom", "sequencing", "genome"],
    "临床检测": ["diagnostic", "biomarker", "clinical"],
    "细胞组学": ["single cell", "scrna", "transcriptom"],
    "时空组学": ["spatial", "transcriptomics"],
    "合成生物学": ["synthetic biology", "gene circuit"],
    "生命科学大模型": ["AI", "AlphaFold", "protein", "deep learning"],
    "细胞治疗": ["CAR-T", "cell therapy", "immunotherapy"],
    "类器官": ["organoid", "organ-on-chip"],
    "衰老与发育": ["aging", "senescence", "development"],
    "生命起源与极端环境生物": ["origin of life", "extremophile"],
    "脑科学": ["neuroscience", "neural", "brain"],
    "脑健康": ["Alzheimer", "Parkinson", "neurodegeneration"]
}

def extract_with_tavily(url):
    """使用 Tavily 提取网页内容"""
    if not TAVILY_API_KEY:
        return None
    try:
        env = os.environ.copy()
        env["TAVILY_API_KEY"] = TAVILY_API_KEY
        cmd = ["node", "/root/skills/tavily-search/scripts/extract.mjs", url]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env, timeout=30)
        return result.stdout
    except Exception as e:
        print(f"Tavily 提取失败：{e}")
        return None

def extract_with_fallback(url):
    """备用提取方法（curl + readability）"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-A", "Mozilla/5.0", url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout[:50000]  # 限制长度
    except:
        pass
    return None

def extract_image_urls(content):
    """从内容中提取图片 URL"""
    image_urls = []
    matches = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', content)
    image_urls.extend(matches)
    matches = re.findall(r'<img[^>]+src="(https?://[^"]+)"', content)
    image_urls.extend(matches)
    return list(set(image_urls))[:5]

def ocr_image_with_tesseract(image_url):
    """使用 Tesseract OCR 识别图片"""
    try:
        tmp_file = "/tmp/ocr_temp.jpg"
        download = subprocess.run(["curl", "-s", "-o", tmp_file, image_url], timeout=10)
        if download.returncode != 0:
            return ""
        
        ocr_result = subprocess.run(
            ["tesseract", tmp_file, "stdout", "-l", "chi_sim+eng"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60
        )
        
        if ocr_result.returncode == 0:
            text = ocr_result.stdout.strip()
            if len(text) > 20:
                print(f"  OCR 识别到 {len(text)} 字符")
                return text
        return ""
    except Exception as e:
        print(f"OCR 失败：{e}")
        return ""

def is_research(content, url=""):
    """判断是否是研究类文章"""
    score = 0
    
    # 域名加分
    academic = ["nature.com", "science.org", "cell.com", "arxiv.org", "pubmed", "doi.org", "ncbi.nlm.nih.gov"]
    for d in academic:
        if d in url.lower():
            score += 3
    
    # 关键词加分
    research_words = ["abstract", "doi", "methods", "results", "figure", "supplementary", 
                      "摘要", "方法", "结果", "图", "补充", "细胞", "基因", "蛋白", "受体", "研究", "论文", "阅读来自"]
    content_lower = content.lower()
    for w in research_words:
        if w in content_lower:
            score += 1
    
    # DOI 加分
    doi_pattern = r"10\.\d{4,}/[\w\-\.]+"
    if re.search(doi_pattern, content):
        score += 5
    
    return score >= 4

def validate_article_url(url):
    """验证文献链接是否有效（非期刊首页）"""
    try:
        from validate_urls import is_valid_url
        result = is_valid_url(url, timeout=10)
        return result["valid"], result.get("title", ""), result.get("error", "")
    except:
        # 简单验证
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-A", "Mozilla/5.0", url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10
            )
            status = result.stdout.strip()
            if status in ["200", "301", "302"]:
                return True, "", ""
            return False, "", f"HTTP {status}"
        except:
            return False, "", "验证失败"

def fetch_citation_info(title, doi=""):
    """获取引用信息"""
    try:
        cmd = ["python3", str(Path(__file__).parent / "fetch_citation.py"), doi if doi else title]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"获取引用失败：{e}")
    return {}

def search_citation_with_image_hints(content, image_urls):
    """从图片中提取线索搜索引用"""
    for img_url in image_urls[:2]:
        ocr_text = ocr_image_with_tesseract(img_url)
        if ocr_text:
            # 从 OCR 结果中提取 DOI 或标题
            doi_match = re.search(r"10\.\d{4,}/[\w\-\.]+", ocr_text)
            if doi_match:
                return fetch_citation_info("", doi_match.group())
            
            # 提取标题关键词
            lines = [l for l in ocr_text.split("\n") if len(l) > 20 and len(l) < 200]
            if lines:
                return fetch_citation_info(lines[0])
    return {}

def search_article_url_searxng(title, doi="", journal=""):
    """使用 searxng 搜索文章全文页"""
    try:
        query = f"{title} {doi} {journal}".strip()[:200]
        search_url = f"{SEARXNG_URL}/search?q={urllib.parse.quote(query)}&format=json"
        result = subprocess.run(["curl", "-s", search_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            for r in data.get("results", [])[:5]:
                url = r.get("url", "")
                # 排除首页、搜索页
                if any(p in url for p in ["/search", "/journal/", "/browse/"]):
                    continue
                # 优先选择 DOI 链接或期刊全文页
                if "doi.org" in url or "nature.com/articles" in url or "science.org/doi" in url:
                    return url
    except Exception as e:
        print(f"searxng 搜索失败：{e}")
    return ""

def classify_topic(title, content=""):
    """归类到 12 个主题"""
    text = (title + " " + content).lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return topic
    return "基因组学"  # 默认

def extract_metadata(content, url=""):
    """提取元数据"""
    meta = {
        "title": "",
        "authors": "",
        "org": "",
        "journal": "",
        "year": "",
        "doi": "",
        "article_url": "",
        "share_url": url,
        "breakthrough": "",
        "technology": "",
        "achievements": "",
        "application": ""
    }
    
    # 提取 DOI
    doi_match = re.search(r"10\.\d{4,}/[\w\-\.]+", content)
    if doi_match:
        meta["doi"] = doi_match.group()
    
    # 提取标题（从 markdown 或 HTML）
    title_match = re.search(r"^#\s+(.+)$", content, re.M)
    if title_match:
        meta["title"] = title_match.group(1).strip()
    
    # 提取机构关键词
    org_keywords = ["大学", "研究所", "学院", "University", "Institute", "Laboratory", "医院"]
    for line in content.split("\n"):
        if any(kw in line for kw in org_keywords) and len(line) < 200:
            if not meta["org"]:
                meta["org"] = line.strip()
    
    return meta

def generate_summary_with_llm(content, meta, limit=200):
    """使用 LLM 生成总结"""
    try:
        # 简化版：提取关键句
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p) > 50 and len(p) < 500]
        
        key_info = []
        for p in paragraphs:
            if any(kw in p for kw in ["发现", "显示", "表明", "达到", "准确率", "首次", "突破"]):
                if len(p) < 150:
                    key_info.append(p.strip())
                    break
        
        for p in paragraphs:
            if any(kw in p for kw in ["意义", "应用", "医疗", "药物", "有望", "治疗"]):
                if len(p) < 150:
                    key_info.append(p.strip())
                    break
        
        summary = " ".join(key_info[:3])
        if len(summary) > limit:
            summary = summary[:limit-3] + "..."
        
        return summary if len(summary) > 30 else ""
    except:
        return ""

def generate_apa_citation(authors, title, journal, year, doi):
    """生成 APA/Nature 格式引用"""
    citation = f"{authors}. {title}. {journal} ({year})."
    if doi:
        if not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        citation += f" {doi}"
    return citation

def process(url):
    """处理用户分享文章"""
    print(f"处理：{url}")
    
    # 1. 提取内容
    content = extract_with_tavily(url)
    if not content:
        content = extract_with_fallback(url)
    
    if not content:
        return {"error": "无法提取内容"}
    
    # 2. 判断类型
    is_res = is_research(content, url)
    print(f"文章类型：{'研究类' if is_res else '其它类'}")
    
    # 3. 提取图片
    image_urls = extract_image_urls(content)
    citation_info = {}
    
    # 4. 研究类文章处理
    if is_res and image_urls:
        print(f"发现 {len(image_urls)} 张图片，尝试从图片中获取线索...")
        citation_info = search_citation_with_image_hints(content, image_urls)
    
    # 5. 提取元数据
    meta = extract_metadata(content, url)
    
    # 6. 生成总结
    summary = ""
    if is_res and meta.get("title"):
        print(f"正在生成深度总结...")
        summary = generate_summary_with_llm(content, meta, 200)
    
    if not summary:
        # 简单总结
        text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", content)
        text = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        summary = text[:200] + "..." if len(text) > 200 else text
    
    # 7. 获取完整引用信息（研究类）
    if is_res and meta.get("title"):
        print(f"正在获取引用信息...")
        
        if not citation_info and meta.get("doi"):
            citation_info = fetch_citation_info(meta["title"], meta.get("doi", ""))
        
        retry_count = 0
        while not citation_info and retry_count < 3 and meta.get("doi"):
            retry_count += 1
            print(f"  第 {retry_count} 次尝试搜索...")
            if meta.get("doi"):
                citation_info = fetch_citation_info("", meta["doi"])
            if not citation_info:
                time.sleep(1)
        
        if citation_info:
            if citation_info.get("title"):
                meta["title"] = citation_info["title"]
                print(f"  使用学术 API 获取的真实标题：{meta['title'][:80]}...")
            if citation_info.get("authors"):
                meta["authors"] = citation_info["authors"]
            if citation_info.get("journal"):
                meta["journal"] = citation_info["journal"]
            if citation_info.get("year"):
                meta["year"] = citation_info["year"]
            if citation_info.get("doi"):
                meta["doi"] = citation_info["doi"]
            if citation_info.get("URL"):
                meta["article_url"] = citation_info["URL"]
        
        # 8. 搜索并验证文章页面链接
        if not meta.get("article_url"):
            print(f"正在搜索文章页面链接...")
            article_url = ""
            
            if meta.get("doi"):
                article_url = search_article_url_searxng(meta["title"], meta["doi"], meta.get("journal", ""))
            
            if article_url:
                # 验证链接
                valid, title, error = validate_article_url(article_url)
                if valid:
                    meta["article_url"] = article_url
                    print(f"  验证通过：{article_url}")
                else:
                    print(f"  验证失败：{error}")
                    meta["article_url"] = f"https://doi.org/{meta['doi']}" if meta["doi"] else url
            elif meta.get("doi"):
                meta["article_url"] = f"https://doi.org/{meta['doi']}"
    
    # 9. 归类到主题
    topic = classify_topic(meta.get("title", ""), content)
    print(f"归类到主题：{topic}")
    
    # 10. 生成归档文件
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r"[^\w\u4e00-\u9fff]", "_", meta.get("title", "unknown")[:30])
    archive = USER_SHARE_DIR / f"{today}_{safe_title}.md"
    
    # 生成引用
    if not meta.get("citation") and meta.get("authors") and meta.get("title"):
        meta["citation"] = generate_apa_citation(
            meta["authors"], 
            meta["title"], 
            meta.get("journal", "Unknown journal"),
            meta.get("year", "n.d."),
            meta.get("doi", "")
        )
    elif not meta.get("citation"):
        meta["citation"] = "待补充（未找到完整引用信息）"
    
    content_md = f"""# {meta.get('title', '未知标题')}

**归档日期**: {today}  
**类型**: {"研究类" if is_res else "其它类"}  
**分享链接**: {url}  
**所属主题**: {topic}

## 📌 核心信息

- **单位**: {meta.get('org', '未知')}
- **团队**: {meta.get('team', '未知')}
- **科研突破**: {meta.get('breakthrough', '未知')}
- **使用技术**: {meta.get('technology', '未知')}
- **重要成果**: {meta.get('achievements', '未知')}
- **产业应用**: {meta.get('application', '未知')}

## 📖 引用格式 (APA/Nature)

{meta.get('citation', '待补充')}

## 📎 元数据

- **作者**: {meta.get('authors', '未知')}
- **机构**: {meta.get('org', '未知')}
- **期刊**: {meta.get('journal', '未知')}
- **年份**: {meta.get('year', '未知')}
- **DOI**: {meta.get('doi', '未知')}
- **文献链接**: {meta.get('article_url', '未知')}

## 📝 全文总结

{summary}

---
**原文来源**: {url}
"""
    
    with open(archive, "w", encoding="utf-8") as f:
        f.write(content_md)
    
    print(f"已归档：{archive}")
    
    return {
        "is_research": is_res,
        "title": meta.get("title", ""),
        "org": meta.get("org", ""),
        "doi": meta.get("doi", ""),
        "article_url": meta.get("article_url", ""),
        "citation": meta.get("citation", ""),
        "authors": meta.get("authors", ""),
        "topic": topic,
        "images_processed": len(image_urls),
        "archive": str(archive)
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = process(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("用法：process_article.py <url>")
