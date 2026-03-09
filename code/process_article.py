#!/usr/bin/env python3
"""用户分享文章处理器 - 增强版（带 OCR 和强制搜索）"""

import json
import re
import os
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import urllib.parse
import base64
import requests
import subprocess
import json
import time

sys.path.insert(0, str(Path(__file__).parent))

USER_SHARE_DIR = Path.home() / "advances" / "usershare"
USER_SHARE_DIR.mkdir(parents=True, exist_ok=True)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8080")

def extract_with_tavily(url):
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

def extract_image_urls(content):
    """从内容中提取图片 URL"""
    image_urls = []
    matches = re.findall(r'!\[.*?\]\((https?://[^\s\)]+)\)', content)
    image_urls.extend(matches)
    matches = re.findall(r'<img[^>]+src="(https?://[^"]+)"', content)
    image_urls.extend(matches)
    return image_urls[:5]

def ocr_image_with_tesseract(image_url):
    """使用 Tesseract OCR 识别图片"""
    try:
        # 下载图片
        tmp_file = "/tmp/ocr_temp.jpg"
        download = subprocess.run(["curl", "-s", "-o", tmp_file, image_url], timeout=10)
        if download.returncode != 0:
            return ""
        
        # 用 Tesseract OCR（中英文）
        ocr_result = subprocess.run(
            ["tesseract", tmp_file, "stdout", "-l", "chi_sim+eng"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60
        )
        
        if ocr_result.returncode == 0:
            text = ocr_result.stdout.strip()
            if len(text) > 20:  # 至少 20 个字符才认为有效
                print(f"  OCR 识别到 {len(text)} 字符")
                return text
        return ""
    except Exception as e:
        print(f"OCR 失败：{e}")
        return ""

def is_research(content, url=""):
    score = 0
    academic = ["nature.com", "science.org", "cell.com", "arxiv.org", "pubmed", "doi.org"]
    for d in academic:
        if d in url.lower():
            score += 3
    research_words = ["abstract", "doi", "methods", "results", "figure", "supplementary", "摘要", "方法", "结果", "图", "补充", "细胞", "基因", "蛋白", "受体", "研究", "论文", "阅读来自"]
    content_lower = content.lower()
    for w in research_words:
        if w in content_lower:
            score += 1
    doi_pattern = r"10\.\d{4,}/[\w\-\.]+"
    if re.search(doi_pattern, content):
        score += 5
    return score >= 4

def fetch_citation_info(title, doi=""):
    try:
        if doi:
            cmd = ["python3", str(Path(__file__).parent / "fetch_citation.py"), doi]
        else:
            cmd = ["python3", str(Path(__file__).parent / "fetch_citation.py"), title]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"fetch_citation 失败：{e}")
    return {}

def search_article_url_from_crossref(doi):
    try:
        url = f"https://api.crossref.org/works/{doi}"
        result = subprocess.run(["curl", "-s", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            message = data.get("message", {})
            return message.get("URL", "")
    except Exception as e:
        print(f"CrossRef 查询失败：{e}")
    return ""

def search_article_url_from_pubmed(doi):
    try:
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={doi}&retmax=1&retmode=json"
        search_result = subprocess.run(["curl", "-s", search_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if search_result.returncode == 0:
            data = json.loads(search_result.stdout)
            idlist = data.get("esearchresult", {}).get("idlist", [])
            if idlist:
                pmid = idlist[0]
                return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    except Exception as e:
        print(f"PubMed 查询失败：{e}")
    return ""

def search_article_url_searxng(title, doi="", journal=""):
    try:
        query = f"{doi} {journal} article" if doi and journal else (doi if doi else title[:50])
        searxng_url = f"{SEARXNG_URL}/search?q={urllib.parse.quote(query)}&format=json"
        response = subprocess.run(["curl", "-s", searxng_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if response.returncode == 0:
            results = json.loads(response.stdout)
            for result in results.get("results", [])[:5]:
                url = result.get("url", "")
                if url and "doi.org" not in url.lower():
                    journal_domains = ["cell.com", "nature.com", "science.org", "pnas.org", "ncbi.nlm.nih.gov/pubmed"]
                    for domain in journal_domains:
                        if domain in url.lower():
                            return url
    except Exception as e:
        print(f"searxng 搜索失败：{e}")
    return ""

def search_citation_with_image_hints(text_content, image_urls):
    """通过图片 OCR 和学术搜索获取完整引用信息"""
    print(f"  发现 {len(image_urls)} 张图片")
    
    all_text = text_content
    
    # 1. 对每张图片进行 OCR
    for img_url in image_urls:
        print(f"  正在 OCR 识别：{img_url[:60]}...")
        ocr_text = ocr_image_with_tesseract(img_url)
        if ocr_text:
            all_text += "\n" + ocr_text
    
    # 2. 从图片 URL 中提取可能的信息
    for img_url in image_urls:
        if "nature.com" in img_url:
            print(f"  发现 Nature 图片：{img_url[:80]}")
        elif "cell.com" in img_url:
            print(f"  发现 Cell 图片：{img_url[:80]}")
        elif "science.org" in img_url:
            print(f"  发现 Science 图片：{img_url[:80]}")
    
    # 3. 从 OCR+ 文本内容中搜索 DOI 和期刊信息
    doi_match = re.search(r"10\.\d{4,}/[\w\-\.]+", all_text)
    if doi_match:
        doi = doi_match.group(0)
        print(f"  从 OCR/文本找到 DOI: {doi}")
        return search_citation_by_doi(doi)
    
    # 4. 搜索期刊名
    journal_patterns = [
        r"(Nature[^\n]{0,50})", r"(Science[^\n]{0,50})", r"(Cell[^\n]{0,50})",
        r"(Nat\s+Commun)", r"(Nat\s+[A-Za-z]+)", r"(Sci\s+[A-Za-z]+)"
    ]
    for p in journal_patterns:
        m = re.search(p, all_text, re.I)
        if m:
            journal = m.group(1)
            print(f"  从 OCR/文本找到期刊：{journal}")
            return search_citation_by_keywords("", journal, "")
    
    return {}

def search_citation_by_doi(doi):
    """通过 DOI 搜索完整引用"""
    # 1. CrossRef
    try:
        url = f"https://api.crossref.org/works/{doi}"
        result = subprocess.run(["curl", "-s", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            message = data.get("message", {})
            if message:
                authors = format_authors(message.get("author", []))
                return {
                    "doi": message.get("DOI", doi),
                    "title": message.get("title", [""])[0] if message.get("title") else "",
                    "authors": authors,
                    "journal": message.get("container-title", [""])[0] if message.get("container-title") else "",
                    "year": str(message.get("created", {}).get("date-parts", [[None]])[0][0]) if message.get("created") else "",
                    "URL": message.get("URL", "")
                }
    except Exception as e:
        print(f"CrossRef 搜索失败：{e}")
    
    # 2. PubMed
    try:
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={doi}&retmax=1&retmode=json"
        search_result = subprocess.run(["curl", "-s", search_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if search_result.returncode == 0:
            data = json.loads(search_result.stdout)
            idlist = data.get("esearchresult", {}).get("idlist", [])
            if idlist:
                pmid = idlist[0]
                fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
                fetch_result = subprocess.run(["curl", "-s", fetch_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
                if fetch_result.returncode == 0:
                    fetch_data = json.loads(fetch_result.stdout)
                    item = fetch_data.get("result", {}).get(pmid, {})
                    authors = ", ".join([a.get("name", "") for a in item.get("authors", [])][:10])
                    return {
                        "doi": item.get("doi", doi),
                        "title": item.get("title", ""),
                        "authors": authors,
                        "journal": item.get("fulljournalname", ""),
                        "year": item.get("pubdate", "")[:4] if item.get("pubdate") else "",
                        "URL": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    }
    except Exception as e:
        print(f"PubMed 搜索失败：{e}")
    
    return {}

def search_citation_by_keywords(title, journal, year):
    """通过关键词搜索引用"""
    try:
        query = f"{title} {journal} {year}" if all([title, journal, year]) else (f"{title} {journal}" if title and journal else journal)
        if not query:
            return {}
        searxng_url = f"{SEARXNG_URL}/search?q={urllib.parse.quote(query)}&format=json"
        response = subprocess.run(["curl", "-s", searxng_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if response.returncode == 0:
            results = json.loads(response.stdout)
            for result in results.get("results", [])[:3]:
                url = result.get("url", "")
                if "doi.org" in url.lower():
                    doi_match = re.search(r"10\.\d{4,}/[\w\-\.]+", url)
                    if doi_match:
                        return search_citation_by_doi(doi_match.group(0))
    except Exception as e:
        print(f"searxng 搜索失败：{e}")
    return {}

def format_authors(authors):
    """格式化作者列表为 APA 格式"""
    if not authors:
        return ""
    formatted = []
    for author in authors[:10]:
        given = author.get("given", "")
        family = author.get("family", "")
        if given and family:
            formatted.append(f"{family}, {given[0]}.")
        elif family:
            formatted.append(family)
    if len(formatted) > 1:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return formatted[0] if formatted else ""

def extract_metadata(content, url):
    meta = {
        "title": "", "authors": "", "team": "", "org": "",
        "breakthrough": "", "technology": "", "achievements": "",
        "application": "", "doi": "", "journal": "", "year": "", 
        "paper_url": "", "article_url": "", "citation": ""
    }
    
    lines = content.split("\n")
    
    # 标题
    for line in lines:
        line = line.strip()
        if line.startswith("# ") and len(line) > 10 and "http" not in line and "javascript" not in line.lower():
            meta["title"] = line.replace("#", "").strip()
            break
    
    # DOI
    doi_pattern = r"10\.\d{4,}/[\w\-\.]+"
    doi_match = re.search(doi_pattern, content)
    if doi_match:
        meta["doi"] = doi_match.group(0)
    
    # 期刊
    citation_line_match = re.search(r"本次阅读来自：[^\n]+([A-Za-z]+\s+[A-Za-z]+)\s+\d+,\s*\d+\s*\(\d{4}\)", content)
    if citation_line_match:
        meta["journal"] = citation_line_match.group(1)
    else:
        journal_match = re.search(r"(Nat\s+Commun|Nature|Science|Cell|PNAS)", content, re.I)
        if journal_match:
            meta["journal"] = journal_match.group(1)
    
    # 年份
    year_match = re.search(r"\((\d{4})\)", content)
    if year_match:
        meta["year"] = year_match.group(1)
    
    # 作者
    author_match = re.search(r"本次阅读来自：([^\.]+)\.", content)
    if author_match:
        meta["authors"] = author_match.group(1).strip()
    
    # 引用行
    full_citation_match = re.search(r"本次阅读来自：([^\n]+\s+https://doi\.org/10\.\d{4,}/[\w\-\.]+)", content)
    if full_citation_match:
        citation_text = full_citation_match.group(1)
        meta["citation"] = citation_text.replace("本次阅读来自：", "").strip()
    
    # 团队
    if "团队" in content:
        team_match = re.search(r"([^\n]+ 团队 [^\n]{0,50})", content)
        if team_match:
            meta["team"] = team_match.group(1)[:100]
    
    # 单位
    org_patterns = [r"([\u4e00-\u9fa5]+(?: 大学 | 研究所 | 学院 | 实验室 | 中心 | 医院))", r"([A-Z][a-z]+\s+(?:University|Institute|Center|Laboratory))"]
    for p in org_patterns:
        m = re.search(p, content)
        if m:
            meta["org"] = m.group(1)
            break
    
    # 技术
    tech_match = re.search(r"(磁共振 |MRSI|成像技术 | 测序 | 组学 |AI| 智能体 [^\n]{0,100})", content)
    if tech_match:
        meta["technology"] = tech_match.group(1)[:200]
    
    # 成果
    ach_match = re.search(r"(绘制 | 构建 | 揭示 | 发现 | 突破 | 首创 [^\n]{0,100})", content)
    if ach_match:
        meta["achievements"] = ach_match.group(1)[:200]
    
    # 应用
    app_match = re.search(r"(应用 | 疾病 | 临床 | 医疗 | 药物 | 精准 [^\n]{0,100})", content)
    if app_match:
        meta["application"] = app_match.group(1)[:200]
    
    return meta

def generate_summary_with_llm(content, meta, limit=150):
    """使用 OpenClaw agent 命令生成深度总结"""
    try:
        # 准备 prompt
        prompt = f"""请用一段话（100-150 字）总结这篇科研文章，必须包括以下 9 个要素：
团队单位、研究骨干、研究目的、思路方法、主要工具、研究样本、主要发现、研究意义、产业应用。

要求：
- 写成一段连贯的文字，不要分条列点
- 控制在 100-150 字
- 语言简洁专业

文章内容：
{content[:8000]}"""

        # 使用 openclaw agent 命令
        env = os.environ.copy()
        result = subprocess.run(
            ["openclaw", "agent", "--to", "+15555550123", "--message", prompt, "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=120,
            env=env
        )
        print(f"LLM subprocess returncode: {result.returncode}")
        print(f"LLM stdout length: {len(result.stdout) if result.stdout else 0}")
        if result.stderr: print(f"LLM stderr: {result.stderr[:200]}")
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                # 从结果中提取文本
                payloads = output.get("result", {}).get("payloads", [])
                if payloads:
                    summary = payloads[0].get("text", "").strip()
                    if summary and len(summary) > 20:
                        return summary
            except Exception as e:
                print(f"解析输出失败：{e}")
        
        return ""
    
    except Exception as e:
        print(f"LLM 总结异常：{e}"); import traceback; traceback.print_exc()
        return ""


def generate_summary_rule_based(content, meta, limit=150):
    """基于规则提取关键信息生成总结"""
    paragraphs = content.split("\n")
    key_info = []
    
    for p in paragraphs:
        if any(kw in p for kw in ["大学", "研究所", "实验室", "团队"]):
            if len(p) < 100: key_info.append(p.strip()); break
    if meta.get("authors"): key_info.append("研究骨干：" + meta["authors"][:50] + "...")
    for p in paragraphs:
        if any(kw in p for kw in ["旨在", "为了", "解决", "难题"]):
            if len(p) < 100: key_info.append(p.strip()); break
    for p in paragraphs:
        if any(kw in p for kw in ["技术", "方法", "方案", "系统", "显微镜"]):
            if len(p) < 100: key_info.append(p.strip()); break
    for p in paragraphs:
        if any(kw in p for kw in ["发现", "显示", "表明", "达到", "准确率"]):
            if len(p) < 100: key_info.append(p.strip()); break
    for p in paragraphs:
        if any(kw in p for kw in ["意义", "应用", "医疗", "药物", "有望"]):
            if len(p) < 100: key_info.append(p.strip()); break
    
    summary = " ".join(key_info[:5])
    if len(summary) > limit: summary = summary[:limit-3] + "..."
    return summary if len(summary) > 30 else ""

def generate_summary(content, limit=200):
    """简单总结（备用）"""
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", content)
    text = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"^#\s+", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[:limit-3] + "..."
    return text

def generate_apa_citation(authors, title, journal, year, doi):
    citation = f"{authors}. {title}. {journal} ({year})."
    if doi:
        if not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        citation += f" {doi}"
    return citation

def process(url):
    print(f"处理：{url}")
    content = extract_with_tavily(url)
    if not content:
        return {"error": "无法提取内容"}
    
    is_res = is_research(content, url)
    
    # 提取图片
    image_urls = extract_image_urls(content)
    citation_info = {}
    
    if is_res and image_urls:
        print(f"发现 {len(image_urls)} 张图片，尝试从图片中获取线索...")
        citation_info = search_citation_with_image_hints(content, image_urls)
    
    # 提取元数据
    meta = extract_metadata(content, url)
    # 生成深度总结
    summary = ""
    if is_res and meta.get("title"):
        print(f"正在生成深度总结...")
        # 优先使用 LLM
        summary = generate_summary_with_llm(content, meta, 500)
        
        # 如果 LLM 失败，使用规则提取
        if not summary:
            print(f"LLM 总结失败，使用规则提取...")
            summary = generate_summary_rule_based(content, meta, 150)
    
    # 如果都失败，使用简单总结
    if not summary:
        summary = generate_summary(content, 200)
    
    # 如果是研究类，获取完整引用信息
    if is_res and meta.get("title"):
        print(f"正在获取引用信息...")
        
        # 优先使用图片搜索结果
        if not citation_info and meta.get("doi"):
            # 只有有 DOI 时才调用 fetch_citation（避免误匹配）
            citation_info = fetch_citation_info(meta["title"], meta.get("doi", ""))
        
        # 如果还没有，尝试多次搜索（仅当有 DOI 时）
        retry_count = 0
        while not citation_info and retry_count < 3 and meta.get("doi"):
            retry_count += 1
            print(f"  第 {retry_count} 次尝试搜索...")
            if meta.get("doi"):
                citation_info = search_citation_by_doi(meta["doi"])
            elif meta.get("journal") and meta.get("title"):
                citation_info = search_citation_by_keywords(meta["title"], meta["journal"], meta.get("year", ""))
            if not citation_info:
                time.sleep(1)
        
        if citation_info:
            # 优先使用 citation_info 中的真实论文标题（最重要！）
            if citation_info.get("title"):
                meta["title"] = citation_info["title"]
                print(f"  使用学术 API 获取的真实标题：{meta['title'][:80]}...")
            if citation_info.get("authors"):
                meta["authors"] = citation_info["authors"]
            if citation_info.get("journal"):
                meta["journal"] = citation_info["journal"]
            if citation_info.get("year"):
                meta["year"] = citation_info["year"]
            # 总是使用 citation_info 中的 DOI（优先级最高）
            if citation_info.get("doi"):
                meta["doi"] = citation_info["doi"]
            if citation_info.get("URL"):
                meta["article_url"] = citation_info["URL"]
        
        # 搜索文章页面链接
        if not meta.get("article_url"):
            print(f"正在搜索文章页面链接...")
            article_url = ""
            
            if meta.get("doi"):
                article_url = search_article_url_from_crossref(meta["doi"])
                if article_url:
                    print(f"CrossRef 找到：{article_url}")
            
            if not article_url and meta.get("doi"):
                article_url = search_article_url_from_pubmed(meta["doi"])
                if article_url:
                    print(f"PubMed 找到：{article_url}")
            
            if not article_url:
                article_url = search_article_url_searxng(meta["title"], meta.get("doi", ""), meta.get("journal", ""))
                if article_url:
                    print(f"searxng 找到：{article_url}")
            
            if article_url:
                meta["article_url"] = article_url
            elif meta.get("doi"):
                meta["article_url"] = f"https://doi.org/{meta['doi']}"
                print(f"使用 DOI 链接作为备选：{meta['article_url']}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r"[^\w\u4e00-\u9fff]", "_", meta.get("title", "unknown")[:30])
    archive = USER_SHARE_DIR / f"{today}_{safe_title}.md"
    
    # 生成 APA/Nature 格式引用
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
    
    return {
        "is_research": is_res,
        "title": meta.get("title", ""),
        "org": meta.get("org", ""),
        "doi": meta.get("doi", ""),
        "article_url": meta.get("article_url", ""),
        "citation": meta.get("citation", ""),
        "authors": meta.get("authors", ""),
        "images_processed": len(image_urls),
        "archive": str(archive)
    }

if __name__ == "__main__":
    import time
    if len(sys.argv) > 1:
        result = process(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("用法：process_article.py <url>")
