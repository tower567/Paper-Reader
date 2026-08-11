# VLA 与具身智能：扩展 fast 阅读 28 篇

- 整理日期：2026-08-10
- 适用读者：已完成“VLA 初学者优先阅读 15 篇”，准备系统补齐历史前驱、数据工程、动作建模、具身推理、真实评测与安全
- 阅读模式：28 篇均按 fast / 30 分钟预算整理，完成 targeted verification，并晋升为正式记录
- 学习路线：[VLA 扩展学习路线与专题地图](../../synthesis/vla-extended-learning-roadmap-2026-08-10.md)
- 候选池：[VLA 扩展候选报告](../../inbox/candidates/vla-extended-2026-08-10.md)
- 前置路线：[VLA 初学者优先阅读 15 篇](vla-beginner-priority-15.md)

第一次阅读建议打开每篇的 `notes.md`；需要方法细节时再看同目录的 `translation.zh.md` 与 `reading-pack.md`。下表顺序按学习依赖排列，不按发表时间或单一排行榜排序。

| 顺序 | 论文 | 模块 | 建议 | 学习定位 |
|---:|---|---|---|---|
| 1 | [Gato](../../papers/2022-reed-gato/notes.md) | 历史前驱 | 核心 | 理解统一 token 序列、共享权重、多任务 mixture 与“通才”边界 |
| 2 | [CLIPort](../../papers/2022-shridhar-cliport/notes.md) | 历史前驱 | 专题 | 理解 CLIP 语义“是什么”与空间“在哪里”的双通路操作 |
| 3 | [BC-Z](../../papers/2022-jang-bcz/notes.md) | 历史前驱 | 核心 | 学习语言/视频条件的真实机器人零样本任务泛化与数据规模效应 |
| 4 | [CALVIN](../../papers/2022-mees-calvin/notes.md) | 长时程接口 | 核心 | 建立语言条件长时程任务链、连续评测与 benchmark 意识 |
| 5 | [VIMA](../../papers/2023-jiang-vima/notes.md) | 多模态提示 | 核心 | 学习交错文本—图像提示、物体 token 和四级泛化协议 |
| 6 | [RoboCat](../../papers/2023-bousmalis-robocat/notes.md) | 通用策略 | 核心 | 理解多 embodiment 动作 token、少样本适配与自主数据飞轮 |
| 7 | [BridgeData V2](../../papers/2023-walke-bridgedata-v2/notes.md) | 数据工程 | 核心 | 学习跨场景真实操作数据的规模、覆盖、标注和数据质量边界 |
| 8 | [DROID](../../papers/2024-khazatsky-droid/notes.md) | 数据工程 | 核心 | 理解多地点、多人、多环境 in-the-wild 数据采集与标准化 |
| 9 | [UMI](../../papers/2024-chi-umi/notes.md) | 数据接口 | 核心 | 学习不把机器人带到现场的手持示教、标定和策略部署链路 |
| 10 | [AutoRT](../../papers/2024-ahn-autort/notes.md) | 舰队部署 | 专题 | 理解 VLM/LLM 任务生成、可供性筛选、混合自治和 Robot Constitution |
| 11 | [RoboCasa](../../papers/2024-nasiriany-robocasa/notes.md) | 仿真数据平台 | 专题 | 学习日常厨房任务生成、MimicGen 数据扩增和仿真—真实边界 |
| 12 | [AgiBot World Colosseo](../../papers/2025-agibot-world-colosseo/notes.md) | 工业数据平台 | 专题 | 理解工业级真实数据引擎、质量控制、开放数据和规模化模型训练 |
| 13 | [CogACT](../../papers/2024-li-cogact/notes.md) | VLA 架构 | 专题 | 学习认知 VLM 与动作模块协同、动作生成接口及真实机器人适配 |
| 14 | [RDT-1B](../../papers/2025-liu-rdt1b/notes.md) | 连续动作 | 核心 | 学习双臂操作的扩散基础模型、异构数据和高维动作块 |
| 15 | [GR00T N1](../../papers/2025-nvidia-gr00t-n1/notes.md) | 人形机器人 | 专题 | 理解 VLM System 2＋扩散动作 System 1、合成数据和 embodiment 适配 |
| 16 | [What Matters in Building RoboVLMs](../../papers/2026-li-robovlms/notes.md) | 设计消融 | 核心 | 用系统实验理解 VLA 中视觉、语言、动作头、数据与训练配方的相对作用 |
| 17 | [OpenVLA-OFT](../../papers/2025-kim-openvla-oft/notes.md) | 高效适配 | 核心 | 学习并行解码、连续动作块、L1 回归及吞吐—闭环频率区别 |
| 18 | [GR-2](../../papers/2024-cheang-gr2/notes.md) | 视频预训练 | 专题 | 理解网页视频动态先验、未来视频辅助目标与 cVAE 动作轨迹 |
| 19 | [RT-H](../../papers/2024-hsu-rth/notes.md) | 动作层级 | 核心 | 学习以语言动作作为层级中间表示，并在人类抽象层进行纠错 |
| 20 | [Embodied CoT](../../papers/2024-zawalski-embodied-cot/notes.md) | 具身推理 | 核心 | 理解计划、子任务、空间与运动字段如何辅助动作及交互纠错 |
| 21 | [CoT-VLA](../../papers/2025-zhao-cot-vla/notes.md) | 视觉推理 | 核心 | 学习视觉子目标链、action-less video 监督与闭环动作块生成 |
| 22 | [THE COLOSSEUM](../../papers/2024-pumacay-colosseum/notes.md) | 泛化评测 | 专题 | 学习按对象、外观、环境与动力学扰动诊断操作策略泛化 |
| 23 | [RoboArena](../../papers/2025-atreya-roboarena/notes.md) | 真机评测 | 核心 | 理解分布式真实机器人、成对比较与相对排名的统计边界 |
| 24 | [VLABench](../../papers/2025-zhang-vlabench/notes.md) | 长时程评测 | 专题 | 学习视觉、语义、世界知识和长时程推理任务 taxonomy |
| 25 | [LIBERO-PRO](../../papers/2025-zhou-libero-pro/notes.md) | 评测有效性 | 核心 | 识别标准 LIBERO 的记忆/泄漏风险，并用结构化扰动测试泛化 |
| 26 | [WorldGym](../../papers/2026-quevedo-worldgym/notes.md) | 世界模型评测 | 专题 | 学习用动作条件视频世界模型筛选策略、相关性与接触失真边界 |
| 27 | [ManipArena](../../papers/2026-sun-maniparena/notes.md) | 受控真机诊断 | 核心 | 学习 schema、分层 OOD、部分得分与 paired real-to-sim 诊断 |
| 28 | [SafeVLA-Bench](../../papers/2026-fan-safevla-bench/notes.md) | 安全评测 | 核心 | 把任务成功与轨迹安全拆开，理解 STL、SBU、VSI 和模拟安全代理 |

## 建议的最短核心路径

时间有限时，优先读以下 12 篇：Gato → BC-Z → VIMA → RoboCat → BridgeData V2 → DROID → RDT-1B → OpenVLA-OFT → RT-H → Embodied CoT → LIBERO-PRO → ManipArena；随后用 SafeVLA-Bench补安全维度。

## 解释边界

- “通用”“推理”“世界模型”“自我改进”在不同论文中含义不同。阅读时应分别检查训练分布、是否更新参数、是否在线搜索候选未来、是否有闭环失败恢复。
- 模拟 benchmark、视频世界模型、真实机器人分布式评测和受控单平台评测支持的结论不同，不能用一个平均成功率互相替代。
- 2025–2026 年的部分记录仍是预印本或快速演化的项目版本；仓库笔记已标注证据等级和版本边界。
