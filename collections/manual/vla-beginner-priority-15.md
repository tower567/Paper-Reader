# VLA 与具身智能：初学者优先阅读 15 篇

- 整理日期：2026-08-10
- 适用读者：具备基础深度学习知识，尚未系统学习机器人学习、具身智能或 VLA
- 阅读模式：15 篇均已按 fast / 30 分钟预算整理并完成 targeted verification
- 详细路线：[VLA 初学者系统学习路线](../../synthesis/vla-beginner-learning-roadmap-2026-08-10.md)
- 候选池与筛选依据：[34 篇候选报告](../../inbox/candidates/vla-beginner-2026-08-10.md)

每篇正式记录均包含 `original.pdf`、`source.md`、`reading-pack.md`、`translation.zh.md`、`notes.md` 与 `metadata.yaml`。第一次阅读建议先打开下表链接的 `notes.md`，再按需要进入同目录查看中文整理和限时阅读包。

| 顺序 | 论文 | 学习定位 |
|---:|---|---|
| 1 | [Vision-Language-Action Models for Robotics: A Review Towards Real-World Applications](../../papers/2025-kawaharazuka-vla-review/notes.md) | 建立 VLA 的架构、数据、评测与真实部署全景图 |
| 2 | [SayCan](../../papers/2023-ichter-saycan/notes.md) | 理解“语言规划器＋技能库＋可供性”的模块化路线 |
| 3 | [RT-1](../../papers/2023-brohan-rt1/notes.md) | 学习真实机器人 Transformer、动作 token 与数据多样性 |
| 4 | [Diffusion Policy](../../papers/2023-chi-diffusion-policy/notes.md) | 补齐连续、多模态动作块生成与滚动控制基础 |
| 5 | [PaLM-E](../../papers/2023-driess-palme/notes.md) | 区分 embodied VLM、高层技能输出与低层动作 VLA |
| 6 | [RT-2](../../papers/2023-zitkovich-rt2/notes.md) | 理解 VLM 与机器人轨迹共同微调、网页知识迁移到动作 |
| 7 | [Open X-Embodiment](../../papers/2024-open-x-embodiment-rtx/notes.md) | 掌握跨机器人数据标准化、混合训练与迁移边界 |
| 8 | [LIBERO](../../papers/2023-liu-libero/notes.md) | 建立语言条件操作与终身学习 benchmark 意识 |
| 9 | [Octo](../../papers/2024-octo-model-team-octo/notes.md) | 学习开放、模块化、可微调的通用机器人策略 |
| 10 | [OpenVLA](../../papers/2024-kim-openvla/notes.md) | 学习开放 7B VLA、离散动作 token、LoRA 与量化 |
| 11 | [SIMPLER](../../papers/2024-li-simpler/notes.md) | 理解经真机校准的 sim-to-real 评测能支持多强结论 |
| 12 | [π0](../../papers/2024-black-pi0/notes.md) | 学习 VLM＋流匹配动作专家与连续动作块路线 |
| 13 | [FAST](../../papers/2025-pertsch-fast/notes.md) | 对照连续 flow，学习 DCT/BPE 动作 tokenization |
| 14 | [π0.5](../../papers/2025-physical-intelligence-pi05/notes.md) | 学习异构协同训练、高层子任务与开放世界泛化 |
| 15 | [SmolVLA](../../papers/2025-shukor-smolvla/notes.md) | 用小模型、开放数据与异步推理完成低门槛实践收尾 |

## 选择边界

- LIBERO 原论文研究的是终身机器人学习，不是专为 VLA 设计；它被保留，是因为语言条件视觉操作、公开示范和标准成功率协议已使其成为常用下游评测入口。不要把 LIBERO 仿真成功率直接解释成真机能力。
- SIMPLER 验证的是特定任务与模型范围内的 sim-real 相对排序和行为相关性，不是用仿真替代真实机器人评测。
- π0.5 与 SmolVLA 截至 2026-08-10 仍按预印本记录阅读；重要结论应保留相应证据等级。
- FAST 与 π0 是离散压缩 token 和连续 flow 两种动作表示路线的有意对照，不是简单的前后继承关系。
