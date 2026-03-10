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

### 4. LabOS - AI-XR 联合科学家（问题诊断案例）
**微信链接：** https://mp.weixin.qq.com/s/ME3Rtsl8yAvm9mKMUOCynw  
**论文标题：** LabOS: The AI-XR Co-Scientist That Sees and Works With Humans  
**DOI：** 10.48550/arXiv.2510.14861  
**期刊：** arXiv preprint  
**年份：** 2025  
**作者：** Le Cong, David Smerkous, Xiaotong Wang, Mengdi Wang, et al. (33 位)

**问题描述：**
- Tavily 提取内容不完整，微信文章被反爬虫拦截
- 原文中 arXiv 链接以纯文本形式存在，而非 markdown 格式
- 初始版本没有提取到 arXiv 链接

**解决方案：**
1. 扩展正则表达式，提取纯文本 arXiv/DOI 链接
2. 添加 SearXNG 二次搜索机制
3. 增加图片 OCR 识别，从配图中提取论文线索

**测试结果：** ✅ 成功获取真实论文标题和完整引用

**关键教训：**
- 不要依赖单一提取源
- 正则表达式要全面（markdown/HTML/纯文本）
- 搜索是最后的保障
- 图片 OCR 可能包含关键信息

---

### 5. Nature Neuroscience - 流式脑 - 语音神经假体
**微信链接：** https://mp.weixin.qq.com/s/ogkFvhTFmJrREOyJt4_qxw  
**论文标题：** A streaming brain-to-voice neuroprosthesis to restore naturalistic communication  
**DOI：** 10.1038/s41593-025-01905-6  
**期刊：** Nature Neuroscience  
**年份：** 2025  
**作者：** Kaylo T. Littlejohn, Cheol Jun Cho, Jessie R. Liu, et al.  
**单位：** 加州大学旧金山分校 (UCSF)

**处理流程：**
1. Tavily 提取微信文章内容
2. 原文中无学术链接
3. 使用 Tavily 搜索找到 Nature Neuroscience 原文
4. 提取完整引用信息

**测试结果：** ✅ 成功获取真实论文标题和完整引用

**核心发现：**
- ECoG 电极阵列捕捉大脑信号
- RNN-T 深度学习模型实时解码
- 80 毫秒内生成自然语音
- 失语症患者通过"想象说话"即可交流

---

### 6. Nature - 细胞记忆体 GEART
**微信链接：** https://mp.weixin.qq.com/s/rptQ9f2tlLsVaG_Q6VzN-A  
**论文标题：** Genetically encoded assembly recorder temporally resolves cellular history  
**DOI：** 10.1038/s41586-026-10323-y  
**期刊：** Nature  
**年份：** 2026  
**作者：** Yuqing Yan, Jiaxi Lu, Zhe Li, et al.  
**单位：** 北京大学等

**处理流程：**
1. Tavily 提取微信文章内容
2. 从原文中提取到 Nature 链接
3. 使用 Tavily 提取 Nature 论文页面
4. 获取完整引用信息

**测试结果：** ✅ 成功获取真实论文标题和完整引用

**核心发现：**
- 基因编码组装记录器（GEART）
- 时序记录细胞内分子组装事件
- 可回溯生命历史
- 解析细胞谱系和发育轨迹

---

### 7. Science Advances - 磁性微机器人
**微信链接：** https://mp.weixin.qq.com/s/dSFBaqT3kR6SkdsThRy0lw  
**论文标题：** Microfluidic-enabled modular assembly of magnetic microrobots for multimodal locomotion  
**DOI：** 10.1126/sciadv.adw3172  
**期刊：** Science Advances  
**年份：** 2026  
**作者：** 待确认  
**单位：** 待确认

**处理流程：**
1. Tavily 提取微信文章内容
2. 从原文中提取到 DOI 链接
3. Tavily 提取 Science 官网失败（反爬虫）
4. 使用 DOI 链接归档

**测试结果：** ✅ 成功获取 DOI 链接，部分信息待补充

**核心发现：**
- 微流控技术制备磁性微机器人
- 模块化组装
- 多种运动模式（行走、爬行、飞行）
- 应用于靶向给药、微创手术

**待改进：**
- Science 官网反爬虫，需要备用提取方案
- 作者和单位信息需通过其他方式获取

---

## 功能测试清单

### 内容提取
- [x] tavily 内容提取
- [x] 备用方法（curl + readability）
- [x] 微信文章处理
- [ ] Science 官网提取（反爬虫，需改进）

### 链接发现
- [x] Markdown 格式链接提取 `[text](url)`
- [x] HTML 格式链接提取 `<a href="url">`
- [x] 纯文本 arXiv 链接提取 `arxiv.org/abs/xxx`
- [x] 纯文本 arXiv ID 提取 `arXiv:2510.14861`
- [x] DOI 提取 `10.xxxx/xxxxx`
- [x] 期刊官网链接提取（nature.com, science.org, cell.com）
- [x] SearXNG 二次搜索
- [x] Tavily 搜索补充

### 图片处理
- [x] 图片 URL 提取
- [x] Tesseract OCR 识别（中英文）
- [x] 从 OCR 结果中提取 DOI
- [x] 从 OCR 结果中提取论文标题

### 引用获取
- [x] CrossRef API 搜索
- [x] PubMed API 搜索
- [x] searxng 搜索
- [x] Tavily 搜索
- [x] APA/Nature 引用格式生成
- [x] DOI 链接包含
- [x] 真实论文标题优先（学术 API）

### 文章处理
- [x] 研究类/其它类判断
- [x] 非论文识别（不强行匹配）
- [x] 12 主题分类
- [x] 归档文件生成
- [x] URL 验证（非期刊首页）

---

## 完整处理流程检查清单

处理用户分享文章时，按顺序执行：

### 第 1 步：内容提取
- [ ] Tavily 提取内容
- [ ] 如果失败，使用备用方法（curl）

### 第 2 步：链接发现
- [ ] 提取 Markdown 格式链接
- [ ] 提取 HTML 格式链接
- [ ] 提取纯文本 arXiv/DOI 链接
- [ ] 提取期刊官网链接
- [ ] 如果没找到学术链接，使用 Tavily/SearXNG 搜索标题

### 第 3 步：图片处理（如果第 2 步没找到）
- [ ] 提取图片 URL
- [ ] 对图片进行 OCR 识别
- [ ] 从 OCR 结果中提取 DOI（正则：`10\.\d{4,}/[\w\-\.]+`）
- [ ] 从 OCR 结果中提取论文标题（长文本行）
- [ ] 使用提取的信息搜索引用

### 第 4 步：验证与获取
- [ ] 验证文献链接可访问性（非期刊首页）
- [ ] 获取完整引用信息（CrossRef/PubMed/Tavily）
- [ ] 生成 APA/Nature 格式引用

### 第 5 步：归档
- [ ] 判断文章类型（研究类/其它类）
- [ ] 归类到 12 个主题
- [ ] 生成归档文件（usershare/YYYY-MM-DD_标题.md）
- [ ] 研究类：200 字总结 + 完整引用
- [ ] 其它类：100 字总结 + 金句

---

## 修改记录

### 2026-03-10 12:48
1. 添加 Nature Neuroscience 脑 - 语音神经假体测试用例（案例 5）
2. 添加 Nature 细胞记忆体 GEART 测试用例（案例 6）
3. 添加 Science Advances 磁性微机器人测试用例（案例 7）
4. 更新功能测试清单（添加 Tavily 搜索）
5. 标注 Science 官网反爬虫问题

### 2026-03-10 12:14
1. 添加 LabOS 问题诊断案例
2. 扩展链接提取（纯文本 arXiv/DOI）
3. 添加 SearXNG 二次搜索
4. 增加图片 OCR 检查清单
5. 完善完整处理流程检查清单

### 2026-03-09
1. 集成 tavily-search 提取网页内容
2. 添加 Tesseract OCR 支持
3. 优化研究类判断逻辑
4. 修复引用格式 DOI 链接缺失
5. 优先使用学术 API 获取真实论文标题
6. 更新 .gitignore 排除归档目录

---

**最后更新：** 2026-03-10 12:48
