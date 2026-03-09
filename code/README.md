# 生命科学日报系统

## 系统结构

```
~/advances/
├── readme.md              # 配置说明
├── daily_report/          # 日报归档
├── usershare/             # 用户分享文章归档
└── code/                  # 脚本
    ├── generate_daily_report.py  # 日报生成
    ├── generate_daily_report.sh  # cron 调用脚本
    ├── process_article.py        # 文章处理
    ├── validate_urls.py          # URL 验证
    ├── fetch_citation.py         # 引用获取
    ├── api_tracker.py            # API 统计
    └── cron.log                  # cron 日志
```

## 功能

### 1. 每日早报 (0:15 自动生成)
- 抓取 Nature/Science/arXiv 等 RSS 源
- 按 12 个主题分类
- 自动去重（对比过去 10 天）
- 归档到 ~/advances/daily_report/YYYY-MM-DD.md

### 2. 文章分享处理
- 发送链接给我，自动处理归档
- 判断研究类/其它类
- 提取元数据（标题、作者、机构、DOI）
- 生成 APA/Nature 引用格式
- 归档到 ~/advances/usershare/

### 3. API 调用统计
- 记录每次调用
- 位置：~/advances/code/api_stats.json
- 查看：`python3 api_tracker.py today`

## 使用方法

### 生成日报（手动测试）
```bash
cd ~/advances/code
python3 generate_daily_report.py
```

### 处理文章链接
```bash
python3 process_article.py <文章链接>
```

### 查看 API 使用
```bash
python3 api_tracker.py today
```

## Cron 任务
```
15 0 * * * /root/advances/code/generate_daily_report.sh
```

## 12 个主题
1. 基因组学
2. 临床检测
3. 细胞组学
4. 时空组学
5. 合成生物学
6. 生命科学大模型
7. 细胞治疗
8. 类器官
9. 衰老与发育
10. 生命起源与极端环境生物
11. 脑科学
12. 脑健康
