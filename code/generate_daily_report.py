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
        
        org = extract_org(e["summary"])
        categorized[topic].append({
            "title": e["title"],
            "link": e["link"],
            "org": org,
            "summary": e["summary"][:80]
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
            report += f"- [{item['org']}] {item['summary']}...  \n"
            report += f"  **[{item['title'][:60]}]({item['link']})**\n\n"
    
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
