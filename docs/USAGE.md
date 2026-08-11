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

`build_index.py` 会同时刷新 `paper.md`、`00-论文库.md`、研究分类文件夹和 Bases。

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

- 优先在 `metadata.yaml` 的 `research.tracks` 中使用 `skill-evolution`、`memory-evolution`、`vla-embodied-ai`；
- 一篇论文可以属于多个 track；留空时由 Obsidian 构建脚本根据标题、领域和主题自动分类；
- 在 metadata.yaml 的 `domains` 和 `topics` 中添加标签；
- `collections/manual/` 用于人工阅读清单；
- bibliography 与 synthesis 只使用已验证论文；
- 快速模式下建议批量更新跨论文综合，而不是每篇都扩写。

## 7. 数据保护

个人成果可保存在 `.local/` 或其他私有目录。共享项目前，应移除论文、候选报告和搜索记录，并确认 PDF、翻译和图表的再分发许可。

## 8. 使用 Obsidian 文献库

在 Obsidian 中打开项目根目录，并进入 `00-论文库.md`。主要入口包括：

- `library/全部论文.base`：全部论文数据库；
- `library/研究分类/Skill 自进化/`；
- `library/研究分类/Memory 自进化/`；
- `library/研究分类/VLA 具身智能/`；
- 每篇论文目录中的 `paper.md`。

单独刷新 Obsidian 产物：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/build_obsidian.py --repo .
```

`paper.md` 是自动生成文件。需要修改论文内容或分类时，应编辑 `metadata.yaml`、`translation.zh.md` 或 `notes.md`，然后重新构建。
