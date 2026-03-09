#!/usr/bin/env python3
"""API 调用追踪器 - 记录大模型 API 使用情况"""

import json
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / "advances" / "code" / "api_usage.log"
STATS_FILE = Path.home() / "advances" / "code" / "api_stats.json"

def log_call(call_type: str, tokens_used: int = 0, model: str = "unknown"):
    """记录一次 API 调用"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "type": call_type,
        "tokens": tokens_used,
        "model": model
    }
    
    # 追加到日志文件
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # 更新统计
    update_stats(call_type, tokens_used)

def update_stats(call_type: str, tokens_used: int):
    """更新累计统计"""
    stats = {}
    if STATS_FILE.exists():
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if "total_calls" not in stats:
        stats["total_calls"] = 0
    if "total_tokens" not in stats:
        stats["total_tokens"] = 0
    if "daily_calls" not in stats:
        stats["daily_calls"] = {}
    if "daily_tokens" not in stats:
        stats["daily_tokens"] = {}
    
    stats["total_calls"] += 1
    stats["total_tokens"] += tokens_used
    
    if today not in stats["daily_calls"]:
        stats["daily_calls"][today] = 0
        stats["daily_tokens"][today] = 0
    
    stats["daily_calls"][today] += 1
    stats["daily_tokens"][today] += tokens_used
    
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

def get_stats():
    """获取当前统计信息"""
    if not STATS_FILE.exists():
        return {"total_calls": 0, "total_tokens": 0, "daily_calls": {}, "daily_tokens": {}}
    
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def get_today_usage():
    """获取今日使用情况"""
    stats = get_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "calls": stats["daily_calls"].get(today, 0),
        "tokens": stats["daily_tokens"].get(today, 0)
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "log":
            call_type = sys.argv[2] if len(sys.argv) > 2 else "unknown"
            tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            log_call(call_type, tokens)
        elif cmd == "stats":
            stats = get_stats()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        elif cmd == "today":
            usage = get_today_usage()
            print(f"今日调用：{usage['calls']} 次，Token: {usage['tokens']}")
    else:
        print("用法：api_tracker.py [log|stats|today] [type] [tokens]")
