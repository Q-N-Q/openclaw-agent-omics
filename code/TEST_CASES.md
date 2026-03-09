# 测试用例记录

## 测试文章链接

### 1. Cell - 全身单细胞 3D 图谱
**微信链接：** https://mp.weixin.qq.com/s/kOb1RUqhhOlFCznoz17-VQ  
**论文标题：** Whole-organ and whole-body 3D atlases enable cellome-wide profiling  
**DOI：** 10.1016/j.cell.2025.12.057  
**期刊：** Cell  
**年份：** 2026  
**作者：** Yoshida, S., Matsumoto, K., Takagi, S., et al.  
**测试结果：** ✅ 成功获取真实论文标题和完整引用

---

### 2. Nature Communications - 大脑代谢连接组
**微信链接：** https://mp.weixin.qq.com/s/CLOL3uDx0T6xxcUj8fQP3w?scene=1  
**论文标题：** Constructing the human brain metabolic connectome with MR spectroscopic imaging reveals cerebral biochemical organization  
**DOI：** 10.1038/s41467-025-66124-w  
**期刊：** Nature Communications  
**年份：** 2025  
**作者：** Lucchetti, F., Céléreau, E., Steullet, P., et al.  
**测试结果：** ✅ 成功获取真实论文标题和完整引用

---

### 3. BGI BiOmics - 技术发布
**微信链接：** https://mp.weixin.qq.com/s/RH5VUkvEjezobx5ecs_p4g  
**文章标题：** BGI 团队发布 BiOmics：3.5 亿条知识关系加持，全面超越所有有 agent  
**DOI：** 无  
**期刊：** 无（技术发布）  
**测试结果：** ✅ 正确识别为非论文，标注"待补充"

---

## 功能测试清单

- [x] tavily 内容提取
- [x] 图片 URL 提取
- [x] Tesseract OCR 识别（中英文）
- [x] DOI 提取（文本 + OCR）
- [x] CrossRef API 搜索
- [x] PubMed API 搜索
- [x] searxng 搜索
- [x] APA/Nature 引用格式生成
- [x] DOI 链接包含
- [x] 真实论文标题优先（学术 API）
- [x] 非论文识别（不强行匹配）
- [x] 归档文件生成

---

## 修改记录

### 2026-03-09
1. 集成 tavily-search 提取网页内容
2. 添加 Tesseract OCR 支持
3. 优化研究类判断逻辑
4. 修复引用格式 DOI 链接缺失
5. 优先使用学术 API 获取真实论文标题
6. 更新 .gitignore 排除归档目录

---

**最后更新：** 2026-03-10
