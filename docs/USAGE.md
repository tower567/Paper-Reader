# 使用步骤

## 1. 选择工作模式

| 模式 | 适用场景 | 默认限制 |
|---|---|---|
| fast | 普通文献筛选、方法理解、建立笔记 | 30 分钟、8 个章节、30,000 字符、2 张短表、最多 6 条证据 |
| deep | 核心 baseline、完整翻译、系统综述、高风险核验 | 显式升级，读取范围由任务决定 |

## 2. 在 Codex 中直接使用

单篇快速阅读：

> 使用 `$manage-literature-repository` 快速阅读这篇论文。围绕“我的研究问题”生成限量阅读包，完成中文整理、笔记、核验、归档和索引。

仅检索候选：

> 使用 `$manage-literature-repository` 调研“研究问题”，先给出候选论文，不要下载或精读。

深度阅读：

> 使用 `$manage-literature-repository` 以 deep 模式阅读这篇核心论文，需要核心章节完整翻译和独立证据核验。

## 3. 命令行流程

### 初始化论文

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/init_paper.py \
  --repo . \
  --year 2025 \
  --first-author Smith \
  --short-title example-method \
  --title "Example Method" \
  --authors "John Smith;Jane Doe" \
  --arxiv "2501.00001" \
  --source-url "https://arxiv.org/abs/2501.00001" \
  --pdf /path/to/paper.pdf
```

默认创建 `fast` 记录，并使用 `structured-summary` 翻译范围。

### 准备结构化原文

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/prepare_source.py \
  inbox/papers/2025-smith-example-method --backend auto
```

快速后端顺序：缓存 → arXiv HTML → 本地 PyMuPDF4LLM。质量失败时再运行：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/prepare_source.py \
  inbox/papers/2025-smith-example-method --backend mineru
```

### 生成限量阅读包

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/plan_reading.py \
  inbox/papers/2025-smith-example-method \
  --research-question "your focused research question"
```

可重复使用 `--focus transfer --focus ablation` 提高特定章节优先级。使用 `--dry-run` 可预览选择结果而不写文件。

### 阅读与填写产物

Reader 只读取 `reading-pack.md`，然后完成：

- `translation.zh.md`；
- `notes.md`；
- `metadata.yaml` 中的研究分类、代码地址和复现判断。

不要为了补齐非核心图表而重新读取整篇 PDF。关键证据缺失时，只回查对应 source-section 或 PDF 页面。

### 校验、晋升与索引

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/validate_paper.py \
  inbox/papers/2025-smith-example-method --strict

micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/promote_paper.py \
  --repo . --paper-id 2025-smith-example-method

micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/build_index.py --repo .
```

## 4. 文献检索流程

创建搜索任务：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/init_search_request.py \
  --repo . --question "your research question"
```

Scout 只处理候选发现、身份核验和去重，不读取全文。确认候选后再初始化单篇论文。

## 5. 深度模式

初始化时指定：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/init_paper.py \
  ... --reading-mode deep --translation-scope core-sections
```

只有明确需要逐字全文翻译时使用 `--translation-scope full`。深度模式可以启用独立 Verifier，并按需读取附录、图表和更多 PDF 页面。

## 6. 分类与综合

- 在 metadata.yaml 的 `domains` 和 `topics` 中添加标签；
- `build_index.py` 自动生成 `collections/generated/`；
- `collections/manual/` 用于人工阅读清单；
- bibliography 与 synthesis 只使用已验证论文；
- 快速模式下建议批量更新跨论文综合，而不是每篇都扩写。

## 7. 数据保护

个人成果可保存在 `.local/` 或其他私有目录。共享项目前，应移除论文、候选报告和搜索记录，并确认 PDF、翻译和图表的再分发许可。
