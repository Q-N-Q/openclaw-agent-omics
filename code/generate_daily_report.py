#!/usr/bin/env python3
"""
生命科学日报生成器 - 优化版（带飞书发送）
"""

import feedparser
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
import re
import hashlib
import hmac
import base64
import time

# Tavily API Key
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")
import subprocess
import urllib.parse

# 配置
DAILY_REPORT_DIR = Path.home() / "advances" / "daily_report"
CODE_DIR = Path.home() / "advances" / "code"

# 飞书配置
FEISHU_APP_ID = "cli_a92796e523b89cce"
FEISHU_APP_SECRET = "x4SslSMT8tdzUVO4JsrqGbzTIk4uWifv"
# 接收日报的群聊 ID 或用户 ID（可配置）
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "ou_b74df689805f15a1b56b456227a3d4fd")

# 确保目录存在
DAILY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

# 12 个主题
TOPICS = [
    "基因组学", "临床检测", "细胞组学", "时空组学",
    "合成生物学", "生命科学大模型", "细胞治疗", "类器官",
    "衰老与发育", "生命起源与极端环境生物", "脑科学", "脑健康"
]

# RSS 源 (简化版，每个主题 1-2 个源)
RSS_FEEDS = [
    "https://www.nature.com/subjects/genomics.rss",
    "https://www.nature.com/subjects/neuroscience.rss",
    "https://www.nature.com/subjects/synthetic-biology.rss",
    "https://arxiv.org/rss/q-bio.GN",
    "https://www.science.org/rss/current.xml",
]

# 主题关键词
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

def search_with_searxng(query, max_results=3):
    """使用 searxng 搜索学术信息"""
    try:
        searxng_url = os.environ.get("SEARXNG_URL", "http://localhost:8080")
        search_url = f"{searxng_url}/search?q={urllib.parse.quote(query)}&format=json"
        result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", search_url], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               universal_newlines=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            results = []
            for r in data.get("results", [])[:max_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")
                })
            return results
    except Exception as e:
        pass
    return []

def fetch_paper_info_enhanced(title, doi="", link=""):
    """增强版：从多源获取完整论文信息"""
    paper_info = {
        "title": title,
        "authors": "",
        "org": "",
        "journal": "",
        "year": "",
        "doi": doi,
        "article_url": link,
        "progress": "",
        "summary": ""
    }
    
    # 如果 DOI 是 arXiv 格式，直接设置
    if doi and doi.startswith("arXiv:"):
        paper_info["journal"] = "arXiv"
        paper_info["article_url"] = f"https://arxiv.org/abs/{doi.replace('arXiv:', '')}"
        return paper_info
    
    # 1. 优先用 DOI 从 CrossRef 获取
    if doi and doi.startswith("10."):
        try:
            url = f"https://api.crossref.org/works/{doi}"
            result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   universal_newlines=True, timeout=10)
            if result.returncode == 0 and result.stdout and len(result.stdout) > 100:
                try:
                    data = json.loads(result.stdout)
                    message = data.get("message", {})
                    if message and message.get("title"):
                        paper_info["title"] = message.get("title", [title])[0]
                        paper_info["authors"] = format_authors(message.get("author", []))
                        paper_info["journal"] = message.get("container-title", [""])[0] if message.get("container-title") else ""
                        paper_info["year"] = str(message.get("created", {}).get("date-parts", [[None]])[0][0]) if message.get("created") else ""
                        paper_info["doi"] = message.get("DOI", doi)
                        paper_info["article_url"] = message.get("URL", link)
                        
                        # 提取机构
                        affiliations = []
                        for author in message.get("author", []):
                            aff = author.get("affiliation", [])
                            if aff:
                                affiliations.extend([a.get("name", "") for a in aff])
                        if affiliations:
                            paper_info["org"] = affiliations[0]
                except Exception as e:
                    pass
        except Exception as e:
            pass
    
    # 2. 如果信息不全，用标题搜索
    if not paper_info["authors"] or not paper_info["journal"]:
        try:
            search_url = f"https://api.crossref.org/works?query.title={title[:100]}&rows=1"
            result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", search_url], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   universal_newlines=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    items = data.get("message", {}).get("items", [])
                    if items:
                        item = items[0]
                        if not paper_info["authors"]:
                            paper_info["authors"] = format_authors(item.get("author", []))
                        if not paper_info["journal"]:
                            paper_info["journal"] = item.get("container-title", [""])[0] if item.get("container-title") else ""
                        if not paper_info["year"]:
                            paper_info["year"] = str(item.get("created", {}).get("date-parts", [[None]])[0][0]) if item.get("created") else ""
                        if not paper_info["doi"]:
                            paper_info["doi"] = item.get("DOI", "")
                        if not paper_info["article_url"]:
                            paper_info["article_url"] = item.get("URL", link)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            pass
    
    # 3. 尝试从链接提取信息（arXiv 等）
    if "arxiv.org" in link.lower() and not paper_info["authors"]:
        try:
            arxiv_id = link.split("/")[-1]
            api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", api_url], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   universal_newlines=True, timeout=10)
            if result.returncode == 0:
                # 简单解析 arXiv XML
                if "<title>" in result.stdout:
                    title_start = result.stdout.find("<title>") + 7
                    title_end = result.stdout.find("</title>", title_start)
                    if title_start > 6 and title_end > title_start:
                        paper_info["title"] = result.stdout[title_start:title_end].strip()
                
                if "<author>" in result.stdout:
                    authors = []
                    for match in re.finditer(r"<name>([^<]+)</name>", result.stdout):
                        authors.append(match.group(1))
                    if authors:
                        paper_info["authors"] = ", ".join(authors[:10])
                
                if "<published>" in result.stdout:
                    pub_match = re.search(r"<published>(\d{4})-", result.stdout)
                    if pub_match:
                        paper_info["year"] = pub_match.group(1)
        except Exception as e:
            pass
    
    # 4. 如果 CrossRef 失败，从链接提取期刊信息
    if not paper_info["journal"]:
        if "nature.com" in link:
            paper_info["journal"] = "Nature"
        elif "science.org" in link:
            paper_info["journal"] = "Science"
        elif "cell.com" in link:
            paper_info["journal"] = "Cell"
        elif "pnas.org" in link:
            paper_info["journal"] = "PNAS"
    
    # 5. 生成进展描述
    if not paper_info["progress"]:
        year = paper_info.get('year', '近年')
        authors = paper_info.get('authors', '研究团队') or '研究团队'
        journal = paper_info.get('journal', '相关期刊') or '相关期刊'
        title = paper_info.get('title', title)[:50]
        paper_info["progress"] = f"该研究发表于{year}，{authors}在{journal}发表论文《{title}...》，报道了最新研究进展。"
    
    return paper_info

def fetch_paper_info(title, doi=""):
    """从 CrossRef/PubMed 获取论文完整信息（兼容旧版）"""
    try:
        # 优先用 DOI 搜索
        if doi:
            url = f"https://api.crossref.org/works/{doi}"
            result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    message = data.get("message", {})
                    if message:
                        return {
                            "title": message.get("title", [""])[0] if message.get("title") else title,
                            "authors": format_authors(message.get("author", [])),
                            "journal": message.get("container-title", [""])[0] if message.get("container-title") else "",
                            "year": str(message.get("created", {}).get("date-parts", [[None]])[0][0]) if message.get("created") else "",
                            "doi": message.get("DOI", doi)
                        }
                except json.JSONDecodeError:
                    pass
        
        # 用标题搜索
        search_url = f"https://api.crossref.org/works?query.title={title[:100]}&rows=1"
        result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", search_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                items = data.get("message", {}).get("items", [])
                if items:
                    item = items[0]
                    return {
                        "title": item.get("title", [""])[0] if item.get("title") else title,
                        "authors": format_authors(item.get("author", [])),
                        "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                        "year": str(item.get("created", {}).get("date-parts", [[None]])[0][0]) if item.get("created") else "",
                        "doi": item.get("DOI", "")
                    }
            except json.JSONDecodeError:
                pass
    except Exception as e:
        pass
    
    return {"title": title, "authors": "", "journal": "", "year": "", "doi": doi}

def format_authors(authors):
    """格式化作者列表"""
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

def extract_article_with_tavily(link):
    """使用 tavily 提取文章完整信息"""
    if not link or not link.startswith("http"):
        return {}
    
    try:
        env = os.environ.copy()
        env["TAVILY_API_KEY"] = TAVILY_API_KEY
        
        result = subprocess.run(
            ["node", "/root/skills/tavily-search/scripts/extract.mjs", link],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, env=env, timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.split("\n")
            article_info = {"title": "", "content": result.stdout, "abstract": ""}
            
            # 提取标题（第一个有意义的非 URL 行）
            for line in lines:
                line = line.strip()
                # 跳过 URL、空行、导航等
                if not line or line.startswith("# http") or line.startswith("*") or line.startswith("- ["):
                    continue
                # 找第一个长标题（不含 http，长度>20）
                if "http" not in line and len(line) > 20 and not line.startswith("#"):
                    article_info["title"] = line
                    break
                # 或者 # 开头的标题
                if line.startswith("# ") and len(line) > 10 and "http" not in line:
                    article_info["title"] = line.replace("#", "").strip()
                    break
            
            # 提取摘要
            abstract_lines = []
            for i, line in enumerate(lines):
                if "abstract" in line.lower() or "摘要" in line.lower() or "[研究机构]" in line:
                    for j in range(i, min(i+3, len(lines))):
                        if lines[j].strip() and not lines[j].startswith("#"):
                            abstract_lines.append(lines[j].strip())
                    break
            
            if abstract_lines:
                article_info["abstract"] = " ".join(abstract_lines)[:500]
            
            return article_info
    except Exception as e:
        print(f"Tavily 提取失败：{e}")
    
    return {}

def get_feishu_token():
    """获取飞书 app_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("app_access_token")
        else:
            print(f"获取飞书 token 失败：{data}")
            return None
    except Exception as e:
        print(f"飞书 token 请求异常：{e}")
        return None

def send_feishu_message(content, report_file=None):
    """发送飞书消息"""
    token = get_feishu_token()
    if not token:
        print("无法获取飞书 token，跳过发送")
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    
    # 构建富文本消息
    text_content = content[:2000]  # 限制长度
    if report_file:
        text_content += f"\n\n📄 完整报告：{report_file}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 判断是群聊还是单聊
    if FEISHU_CHAT_ID.startswith("oc_"):
        # 群聊
        payload = {
            "receive_id": FEISHU_CHAT_ID,
            "msg_type": "text",
            "content": json.dumps({"text": text_content}),
            "uuid": str(datetime.now().timestamp())
        }
    else:
        # 单聊（用户 ID）
        payload = {
            "receive_id": FEISHU_CHAT_ID,
            "msg_type": "text",
            "content": json.dumps({"text": text_content})
        }
    
    params = {"receive_id_type": "open_id" if not FEISHU_CHAT_ID.startswith("oc_") else "chat_id"}
    
    try:
        resp = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
        data = resp.json()
        if data.get("code") == 0 or resp.status_code == 200:
            print(f"✓ 飞书消息发送成功")
            return True
        else:
            print(f"飞书发送失败：{data}")
            return False
    except Exception as e:
        print(f"飞书发送异常：{e}")
        return False

def fetch_rss(timeout=10):
    """抓取 RSS，带超时"""
    all_entries = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                all_entries.append({
                    "title": entry.get("title", "无标题"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200],
                    "published": entry.get("published", ""),
                    "source": feed.feed.get("title", "")
                })
        except Exception as e:
            print(f"RSS 失败 {feed_url}: {e}")
    return all_entries

def classify(title, summary):
    """分类到主题"""
    text = (title + " " + summary).lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return topic
    return "脑科学"  # 默认

def load_history(days=10):
    """加载历史标题去重"""
    titles = set()
    today = datetime.now()
    for i in range(days):
        date = today - timedelta(days=i)
        f = DAILY_REPORT_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if f.exists():
            with open(f) as fp:
                for line in fp:
                    if line.startswith("## "):
                        titles.add(line[3:].strip())
    return titles

def extract_org(summary):
    """提取机构"""
    patterns = [r"([A-Z][a-z]+ University)", r"([A-Z] Institute)"]
    for p in patterns:
        m = re.search(p, summary)
        if m:
            return m.group(1)
    return "研究机构"

def generate_report():
    """生成日报"""
    print(f"[{datetime.now().isoformat()}] 开始生成...")
    
    entries = fetch_rss()
    print(f"抓取 {len(entries)} 条")
    
    history = load_history()
    categorized = {t: [] for t in TOPICS}
    
    for e in entries:
        topic = classify(e["title"], e["summary"])
        if e["title"] in history:
            continue
        
        # 提取 DOI（增强版：支持多种格式）
        link = e.get("link", "")
        summary = e.get("summary", "")
        doi = ""
        
        # 1. 尝试标准 DOI 格式
        doi_match = re.search(r"10\.\d{4,}/[\w\-\.]+", summary + " " + link)
        if doi_match:
            doi = doi_match.group(0)
        
        # 2. 尝试从 Nature 链接提取
        if not doi and "nature.com/articles/" in link:
            nature_match = re.search(r"/articles/(s?\d{4,}[\w\-\.]+)", link)
            if nature_match:
                article_id = nature_match.group(1)
                if article_id.startswith('s'):
                    doi = f"10.1038/{article_id}"
                else:
                    doi = f"10.1038/s{article_id}"
        
        # 3. 尝试从 Science 链接提取
        if not doi and "science.org/doi/" in link:
            science_match = re.search(r"/doi/(10\.\d{4,}/[\w\-\.]+)", link)
            if science_match:
                doi = science_match.group(1)
        
        # 4. 尝试从 arXiv 链接提取
        if not doi and "arxiv.org/abs/" in link:
            arxiv_match = re.search(r"/abs/([\d\.]+)", link)
            if arxiv_match:
                doi = f"arXiv:{arxiv_match.group(1)}"
        
        # 获取完整论文信息（增强版）
        paper_info = fetch_paper_info_enhanced(e["title"], doi, e["link"])
        
        org = extract_org(e["summary"])
        categorized[topic].append({
            "title": paper_info.get("title", e["title"]),
            "authors": paper_info.get("authors", ""),
            "org": paper_info.get("org", org),
            "journal": paper_info.get("journal", ""),
            "year": paper_info.get("year", ""),
            "doi": paper_info.get("doi", doi),
            "article_url": paper_info.get("article_url", e["link"]),
            "progress": paper_info.get("progress", ""),
            "link": e["link"],
            "summary": e["summary"][:200]
        })
    
    # 生成内容
    today = datetime.now()
    report = f"# 生命科学日报 {today.strftime('%Y 年 %m 月 %d 日')}\n\n"
    report += f"生成时间：{today.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    for topic in TOPICS:
        items = categorized[topic][:3]
        if not items:
            continue
        report += f"## {topic}\n\n"
        for item in items:
            # 生成 APA/Nature 引用格式
            citation = ""
            if item.get("authors") and item.get("title") and item.get("journal"):
                citation = f"{item.get('authors', '')}. {item.get('title', '')}. {item.get('journal', '')} ({item.get('year', 'n.d.')})."
                if item.get("doi"):
                    citation += f" https://doi.org/{item.get('doi', '')}"
            
            report += f"- **{item.get('org', '研究机构')}**\n"
            report += f"  - **论文标题**: [{item.get('title', 'Unknown')}]({item.get('article_url', item.get('link', '#'))})\n"
            report += f"  - **作者**: {item.get('authors', '未知')[:100]}\n"
            report += f"  - **进展**: {item.get('progress', item.get('summary', '...'))[:150]}...\n"
            report += f"  - **文献链接**: {item.get('article_url', item.get('link', '#'))}\n"
            report += f"  - **分享链接**: {item.get('link', '#')}\n"
            if citation:
                report += f"  - **引用**: *{citation}*\n"
            
            # 生成 200 字总结
            summary = f"{item.get('progress', '')} {item.get('summary', '')}"
            if len(summary) > 200:
                summary = summary[:200] + "..."
            report += f"  - **总结**: {summary}\n"
            report += "\n"
    
    # 保存
    report_file = DAILY_REPORT_DIR / f"{today.strftime('%Y-%m-%d')}.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"已保存：{report_file}")
    return report, report_file

if __name__ == "__main__":
    report, report_file = generate_report()
    print(f"\n=== 预览 ===\n{report[:300]}")
    
    # 发送飞书
    print("\n=== 发送飞书 ===")
    send_feishu_message(report, str(report_file))
