#!/bin/bash
# 每日早报生成脚本 - 由 cron 调用

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行日报生成..."

cd /home/admin/advances/code

# 运行 Python 脚本生成日报
python3 generate_daily_report.py 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 日报生成完成"
