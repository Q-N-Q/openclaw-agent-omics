# 生命科学日报系统配置

## 系统说明

本系统自动抓取生命科学领域最新进展，每日凌晨 0:15 生成早报并归档。

## 12 个主题分类

1. **基因组学** (Genomics)
2. **临床检测** (Clinical Diagnostics)
3. **细胞组学** (Cell Omics)
4. **时空组学** (Spatiotemporal Omics)
5. **合成生物学** (Synthetic Biology)
6. **生命科学大模型** (Life Science AI/LLM)
7. **细胞治疗** (Cell Therapy)
8. **类器官** (Organoids)
9. **衰老与发育** (Aging & Development)
10. **生命起源与极端环境生物** (Origin of Life & Extremophiles)
11. **脑科学** (Neuroscience)
12. **脑健康** (Brain Health)

## RSS 信息源

### Nature 系列
- https://www.nature.com/subjects/genomics.rss
- https://www.nature.com/subjects/transcriptomics.rss
- https://www.nature.com/subjects/proteomics.rss
- https://www.nature.com/subjects/bioinformatics.rss
- https://www.nature.com/subjects/synthetic-biology.rss
- https://www.nature.com/subjects/neuroscience.rss

### arXiv
- https://arxiv.org/rss/q-bio.GN
- https://arxiv.org/rss/q-bio.OT

### PLOS
- https://journals.plos.org/plosgenetics/feed/atom
- https://journals.plos.org/ploscompbiol/feed/atom

### BMC
- https://bmcgenomics.biomedcentral.com/feed

### Science
- https://www.science.org/rss/current.xml

### Cell
- https://www.cell.com/cell/current.rss
- https://www.cell.com/cell-systems/current.rss

## 搜索关键词配置

### 各主题关键词 (用于全网搜索)

```json
{
  "基因组学": ["genomics", "genome sequencing", "whole genome", "clinical genomics", "基因组测序"],
  "临床检测": ["clinical diagnostics", "biomarker", "liquid biopsy", "molecular diagnostics", "临床检测"],
  "细胞组学": ["single cell", "scRNA-seq", "cell atlas", "transcriptomics", "单细胞"],
  "时空组学": ["spatial transcriptomics", "spatial omics", "spatial proteomics", "空间组学"],
  "合成生物学": ["synthetic biology", "gene circuit", "metabolic engineering", "合成生物学"],
  "生命科学大模型": ["protein folding", "AlphaFold", "biology AI", "drug discovery AI", "生物大模型"],
  "细胞治疗": ["CAR-T", "cell therapy", "immunotherapy", "stem cell therapy", "细胞治疗"],
  "类器官": ["organoid", "organ-on-chip", "3D culture", "类器官"],
  "衰老与发育": ["aging", "senescence", "developmental biology", "longevity", "衰老", "发育"],
  "生命起源与极端环境生物": ["origin of life", "extremophile", "astrobiology", "primordial", "生命起源"],
  "脑科学": ["neuroscience", "neural circuit", "brain mapping", "connectome", "神经科学"],
  "脑健康": ["Alzheimer", "Parkinson", "neurodegeneration", "brain disease", "脑健康"]
}
```

## 归档规则

### 研究类文章判定标准
- 包含实验数据、方法、结果
- 来自学术期刊、预印本平台
- 有明确的作者、单位、DOI

### 引用格式 (Nature/APA)
```
作者。文章标题。期刊名 (发表年份). DOI 链接
```

示例：
```
Smith, J., & Wang, L. CRISPR-based gene editing in human embryos. Nature (2025). https://doi.org/10.1038/s41586-025-xxxxx
```

### 去重规则
- 对比过去 10 天日报中的标题和 DOI
- 相同内容不重复报道
- 用户分享的内容需纳入主题归类

## API 调用统计

系统记录每次大模型 API 调用：
- 日期
- 类型 (早报生成/文章处理)
- Token 使用量
- 累计调用次数

日志位置：~/advances/code/api_usage.log

## Cron 任务配置

```bash
# 每日凌晨 0:15 生成早报
15 0 * * * /home/admin/advances/code/generate_daily_report.sh >> /home/admin/advances/code/cron.log 2>&1
```

## 文件结构

```
~/advances/
├── readme.md              # 本配置文件
├── daily_report/          # 日报归档
│   └── YYYY-MM-DD.md
├── usershare/             # 用户分享文章归档
│   └── YYYY-MM-DD_项目名.md
└── code/                  # 脚本和程序
    ├── generate_daily_report.sh
    ├── process_article.sh
    ├── validate_urls.py
    ├── fetch_citation.py
    ├── api_tracker.py
    └── cron.log
```
