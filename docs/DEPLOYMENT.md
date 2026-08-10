# 安装与部署

## 1. 前置条件

- micromamba；
- Codex Desktop 或 Codex CLI；
- 可选：MinerU Token，用于本地/HTML 解析失败后的质量升级。

推荐在 WSL 或 Linux 中运行。Windows 原生环境同样使用 micromamba，命令保持一致；路径改为 Windows 路径即可。

## 2. 创建环境

进入下载或解压后的项目目录：

```bash
cd Paper-Reader
micromamba create -f environment.yml
```

检查环境：

```bash
micromamba run -n paper-reader python --version
micromamba run -n paper-reader arxiv-mcp-server --help
micromamba run -n paper-reader pytest -q
```

## 3. Codex 与 arXiv MCP

项目的 `.codex/config.toml` 已配置：

- micromamba 环境：`paper-reader`；
- MCP server：`arxiv-mcp-server`；
- 相对缓存目录：`.cache/arxiv`。

创建环境后重新打开 Codex 项目，使 MCP 配置生效。相对路径使项目可以移动，不需要修改用户名或磁盘盘符。

## 4. 配置 MinerU（可选）

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/configure_mineru_token.py
```

检查配置：

```bash
micromamba run -n paper-reader python \
  .agents/skills/manage-literature-repository/scripts/configure_mineru_token.py --check
```

脚本隐藏输入，将 Token 写到 `~/.config/paper-reader/mineru.env` 并设置为仅当前用户可读。不要把真实 Token 放进项目文件、Codex 对话、日志或截图。

## 5. 常见问题

### Codex 找不到 arXiv MCP

确认 `micromamba run -n paper-reader arxiv-mcp-server --help` 可运行，然后重新打开 Codex 项目。

### 本地 PDF 解析失败

先确认文件是完整、可读取的 PDF。若 `parse.yaml` 的质量状态不是 `passed`，再显式运行 `prepare_source.py --backend mineru`。

### MinerU Token 已设置但子进程读不到

运行配置脚本的 `--check`。MinerU 客户端会直接读取用户配置文件，不依赖 shell 是否加载 `.bashrc`。

### 30 分钟内没有完成

扫描件、图片型论文、超长附录和 MinerU 长任务属于快速模式例外。缓存解析结果后继续，或明确升级到深度模式。
