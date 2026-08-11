# Paper Reader

Paper Reader 是一个面向 Codex 的可追溯学术文献工作流。它把论文检索、PDF/HTML 解析、限时阅读、中文整理、证据核验、分类和索引维护放在同一个项目中。

默认采用 30 分钟快速模式：只读取与研究问题最相关的核心章节，自动省略图片和非关键表格，避免一篇论文消耗数小时和大量 token。

## 核心特点

- 默认最多读取 8 个章节、约 30,000 字符；
- 自动生成 `reading-plan.yaml` 和去图片、限表格的 `reading-pack.md`；
- 中文产物默认是“摘要全文翻译 + 核心内容压缩翻译”；
- 重要结论使用 Paper claim、Reported result、Reader inference 和 Open question 标签；
- 优先复用缓存和 arXiv HTML，再使用本地 PDF 解析；MinerU 仅作为质量升级；
- 每篇论文只存一份，通过 metadata 标签生成分类索引；
- 自动生成 Obsidian 论文主页、研究分类文件夹和 Bases 数据库视图；
- WSL、Linux 和 Windows 均使用 micromamba 管理环境；
- 公共模板默认忽略个人 PDF、翻译、笔记和检索记录，降低误上传风险。

## 快速开始

```bash
cd Paper-Reader
micromamba create -f environment.yml
micromamba run -n paper-reader pytest -q
```

在 Codex 中打开项目，然后输入：

> 使用 `$manage-literature-repository` 快速阅读这篇论文，控制在 30 分钟以内，并保留原始 PDF、中文整理、笔记和元数据。

如果需要 MinerU：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/configure_mineru_token.py
```

Token 会保存在用户目录的 `~/.config/paper-reader/mineru.env`，不会写入仓库。

## 使用 Obsidian 阅读

在 Obsidian 中将项目根目录作为 Vault 打开。入口文件是：

```text
00-论文库.md
```

左侧 `library/研究分类/` 按 Skill 自进化、Memory 自进化、VLA 具身智能和其他论文组织。每篇论文目录中的 `paper.md` 集中提供原文 PDF、中文整理和阅读笔记。

手动刷新 Obsidian 页面：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/build_obsidian.py --repo .
```

正常完成论文晋升后运行 `build_index.py` 即可，它会同时更新 Obsidian。

## 工作产物

每篇新论文在完成后包含：

- `original.pdf`：原始论文；
- `source.md`、`parse.yaml`、`source-sections/`：缓存与分段后的原文；
- `reading-plan.yaml`：阅读范围、预算和升级条件；
- `reading-pack.md`：限量阅读包；
- `translation.zh.md`：带明确范围的中文产物；
- `notes.md`：带证据位置的分析笔记；
- `metadata.yaml`：身份、分类、流程和质量信息。
- `paper.md`：由 metadata 自动生成的 Obsidian 论文主页。

## 文档

- [安装与部署](docs/DEPLOYMENT.md)
- [完整使用步骤](docs/USAGE.md)
- [安全说明](SECURITY.md)

## 目录结构

```text
.agents/skills/manage-literature-repository/  核心 Skill、脚本和模板
.codex/                                      Codex MCP 与 Agent 配置
inbox/                                       搜索请求、候选和待处理论文
papers/                                      已验证论文
collections/manual/                          人工维护的阅读清单
bibliography/                                引用记录
synthesis/                                   跨论文综合
library/                                     Obsidian Bases 与研究分类入口
tests/                                       自动化测试
```

## 快速模式边界

30 分钟目标适用于普通、可机器读取的研究论文。扫描件、超长论文、图像型论文、完整逐字翻译和 MinerU 长任务属于深度模式或明确例外，不会通过牺牲证据质量来硬凑时间。

## 个人文献保护

建议将个人论文、翻译、笔记和检索记录保存在本地私有空间。共享项目文件前，应单独检查 PDF、翻译、图表和数据的版权、隐私及再分发许可。
