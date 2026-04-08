# UE AI 材质节点性能分析工具 —— Agent 开发说明书

## 1. 文档用途

这是一份交给 Agent（如 Cursor / Claude Code / Copilot / ChatGPT Agent）使用的项目说明文档。
目标是指导 Agent 按照明确边界与步骤，优先完成 **“UE AI 分析材质节点性能工具”**，并在架构上为后续扩展 **“UE AI 创作助手（材质生成）”** 预留空间。

本项目当前 **不做蓝图生成**，也 **不优先做完整 MCP 平台**，先聚焦 **材质节点性能分析**。

---

## 2. 作业要求（原始要求整理）

### 作业一：UE AI 创作助手
设计并实现一款运行于 UE 引擎的 AI 创作助手工具，要求界面使用 Web 实现。
工具可选择实现 **AI 生成材质** 或 **AI 生成蓝图** 功能（二选一即可），支持用户对 AI 生成的结果进行预览、手动调整，并可基于调整后的内容触发 AI 再次迭代生成，直至满足使用需求。

**核心功能：**
- 基于 UE 引擎 API 开发，AI 生成材质 / 蓝图（二选一）
- Web 界面实现交互操作，支持生成结果预览
- 支持对生成结果手动调整，并触发 AI 迭代优化
- 最终输出可直接在 UE 中使用的材质 / 蓝图文件

### 作业二：UE AI 分析材质节点性能工具
设计并实现一款运行于 UE 引擎的 AI 材质节点性能分析工具，界面使用 Web 实现。
工具需通过 AI 分析材质节点的连接逻辑合理性、材质运算过程中的冗余计算与重复逻辑，并将分析逻辑和判定规则沉淀为可复用的 Skills，供 TA 后续拓展迭代。

**核心功能：**
- 基于 UE 引擎 API 或者文件文本方式，解析材质节点的连接关系与运算逻辑
- 利用 AI 分析：判定节点连接合理性、识别重复 / 冗余计算
- 输出可视化的性能分析报告（含问题定位、优化建议）
- 沉淀分析规则为可复用的 Skills 模块，支持 TA 二次迭代开发

---

## 3. 当前项目目标（必须遵守）

### 当前唯一主目标
先完成：

**UE AI 分析材质节点性能工具**

### 当前明确边界
- 只做 **材质**，不做蓝图
- 先做 **分析**，不做生成
- UI 使用 **Streamlit** 实现 Web 界面
- 第一阶段优先支持 **UE Live（通过 UE Python / Remote Execution 自动获取材质图）**
- 第二阶段补 **Paste Text（从 UE 复制节点文本后粘贴分析）** 作为降级与容灾输入
- AI 在第一阶段主要负责：
  - 解释规则分析结果
  - 生成优化建议
  - 生成报告文本
- 第一阶段不强依赖 MCP
- 必须预留后续扩展到“材质生成助手”的接口

### 不建议一开始做的内容
- 不要一开始做完整 Agent 平台
- 不要一开始做复杂前端框架（如完整 React 节点编辑器）
- 不要一开始做贴图生成
- 不要一开始做材质和蓝图双线并行
- 不要把所有判断都交给大模型

---

## 4. 对“运行于 UE 引擎 + Web 界面”的理解

该工具的合理实现方式是：

- **工具服务于 UE 编辑器工作流**
- **数据来自 UE 材质**
- **分析结果用于 UE 材质优化**
- **界面层使用 Web 技术实现（Streamlit）**

因此可以采用下面的结构：

```text
UE 编辑器 / UE 材质
   ↓
节点信息导出（UE API / Remote Execution 为主，文本粘贴为备选）
   ↓
Python 分析层（解析、规则分析、AI分析、报告生成）
   ↓
Streamlit Web UI（展示摘要、问题、建议、报告、Skills）
```

这满足：
- 工具围绕 UE 工作流运行
- 界面使用 Web 实现
- 后续可以扩展到更复杂的 Agent / MCP 形式

---

## 5. 总体系统架构

```text
ue_material_analyzer/
│
├─ app.py                         # Streamlit 入口
├─ requirements.txt
├─ README.md
│
├─ data_models/
│   └─ material_graph.py          # 统一数据结构定义
│
├─ parser/
│   ├─ ue_api_parser.py           # UE Live 返回数据解析器（第一阶段主线）
│   ├─ paste_text_parser.py       # 粘贴文本解析器（第二阶段补齐）
│   └─ normalize_graph.py         # 统一图结构格式
│
├─ analyzer/
│   ├─ graph_utils.py             # 图遍历工具函数
│   ├─ builtin_rules.py           # 基础规则
│   └─ run_analysis.py            # 执行规则分析
│
├─ services/
│   ├─ ai_service.py              # 调用外部 LLM API
│   └─ report_service.py          # 报告整理与导出
│
├─ skills/
│   ├─ duplicate_texture_sampling/
│   ├─ dead_node_detection/
│   ├─ redundant_math_chain/
│   └─ long_path_warning/
│
├─ prompts/
│   ├─ report_prompt.txt
│   └─ suggestion_prompt.txt
│
├─ samples/
│   ├─ sample_copy_text_01.txt
│   ├─ sample_copy_text_02.txt
│   └─ sample_graph_01.json
│
├─ outputs/
│   ├─ parsed_graphs/
│   └─ reports/
│
└─ ue_bridge/
    ├─ remote_exec_client.py      # 第二阶段做
    └─ export_material_graph.py   # 第二阶段做
```

---

## 6. 开发阶段规划（按顺序执行）

# 阶段 0：建立项目边界与交付标准

### 目标
统一理解项目范围，避免一开始做得过大。

### 要求
Agent 必须先完成以下确认：
- 当前项目只做 **作业二：材质节点性能分析工具**
- 作业一只做架构预留，不做实现主体
- 第一阶段优先支持 UE API / Remote Execution，第二阶段再补文本输入
- Web UI 使用 Streamlit
- AI 不负责替代全部规则分析

### 产出
- 一份 README 的项目简介
- 一份目录结构初始化

---

# 阶段 1：定义统一数据结构（最重要）

### 目标
定义整个系统的统一输入/输出格式。

### 必须完成
创建一个统一数据结构 `material_graph`，至少包含以下字段：

```json
{
  "material_name": "M_Test",
  "source_type": "ue_api",
  "nodes": [
    {
      "id": "node_1",
      "name": "TextureSample_0",
      "type": "TextureSample",
      "params": {
        "texture": "/Game/Textures/T_Rock_D"
      }
    }
  ],
  "edges": [
    {
      "from_node": "node_1",
      "from_pin": "RGB",
      "to_node": "node_2",
      "to_pin": "A"
    }
  ],
  "outputs": [
    {
      "output": "BaseColor",
      "source_node": "node_2"
    }
  ],
  "stats": {
    "node_count": 2,
    "edge_count": 1,
    "output_count": 1
  }
}
```

### 设计原则
- 所有输入源最终都要归一到这个结构
- UE Live 输出与文本解析结构必须一致
- 后续材质生成功能也尽量复用这个结构

### 建议实现
- 使用 `dataclass` 或 `pydantic` 定义模型
- 增加校验函数与 `to_dict()` / `from_dict()`

### 产出
- `data_models/material_graph.py`
- `samples/sample_graph_01.json`

---

# 阶段 2：实现 UE Live 输入（第一阶段主线）

### 目标
支持通过 UE 引擎 API / Remote Execution 自动获取材质图并分析。

### 为什么先做这个
- 作业明确允许并鼓励基于 UE 引擎 API
- 能拿到更完整的资产级信息（如材质域、混合模式等）
- 结构更稳定，减少对复制文本格式的依赖

### 输入
- 通过 UE Python / Remote Execution 调用 UE 侧导出函数
- 获取选中材质或按材质名导出的结构化数据

### 输出
- 解析成统一 `material_graph`

### 必须识别的信息
- 节点名称
- 节点类型
- 节点参数（能提取多少提取多少）
- 节点之间的连接关系
- 最终输出插槽（如 BaseColor / Roughness / Metallic / Normal）

### 开发要求
- 至少实现以下最小函数：
  - `get_selected_material_name()`
  - `export_selected_material_graph()`
  - `export_material_graph_by_name(name)`
- UE Live 输出必须包含节点、连线、输出口与关键材质属性
- 解析失败时要给出明确错误信息

### 产出
- `ue_bridge/remote_exec_client.py`
- `ue_bridge/export_material_graph.py`
- `parser/ue_api_parser.py`
- `parser/normalize_graph.py`

---

# 阶段 3：实现 Paste Text 解析器（第二阶段补齐）

### 目标
支持从 UE 复制节点后，直接粘贴文本进行分析，作为降级与容灾输入。

### 为什么仍然要做
- 在 UE Live 不可用时提供备选通道
- 便于快速分享与离线复盘
- 用于对比 UE Live 与文本解析的一致性

### 输入
- 用户从 UE 材质编辑器复制节点
- 粘贴到 Streamlit 文本框

### 输出
- 归一到统一 `material_graph`

### 开发要求
- 提供至少 2 份真实样本进行测试
- 解析逻辑要尽量模块化，不要把所有正则写死在一个函数里
- 解析失败时要给出明确错误信息

### 产出
- `parser/paste_text_parser.py`
- `samples/sample_copy_text_01.txt`
- `samples/sample_copy_text_02.txt`

---

# 阶段 4：实现最小 Streamlit Web UI

### 目标
用 Web 页面完成数据输入与基础展示。

### 页面结构建议

## 页面 1：输入区
- 文本框：粘贴 UE 节点文本
- 按钮：解析材质图
- 按钮：加载示例数据

## 页面 2：材质摘要
显示：
- 材质名称
- 节点数量
- 连线数量
- 输出槽位数量

## 页面 3：节点表格
显示：
- node id
- 节点名
- 节点类型
- 参数摘要

## 页面 4：连接表格
显示：
- from_node
- from_pin
- to_node
- to_pin

### 要求
- 页面风格可以简洁，不需要重设计
- 必须保证字段展示清晰
- 解析失败时给出错误提示

### 产出
- `app.py`

---

# 阶段 5：实现规则分析（核心功能）

### 目标
不依赖大模型，先做确定性规则检测。

### 第一版必须实现的 4 条规则

## 规则 1：重复纹理采样
检测是否对相同纹理资源进行了重复采样。

输出示例：
- rule_id: `duplicate_texture_sampling`
- severity: `medium`
- node_ids: `[node_3, node_8]`
- suggestion: `考虑复用采样结果，减少重复读取。`

## 规则 2：重复数学运算
检测相似输入链上的重复 Add / Multiply / Subtract / Divide 等运算。

## 规则 3：死节点 / 无贡献节点
检测未连接到任何最终输出的节点。

## 规则 4：链路过长
检测从关键输出口（如 BaseColor / Normal）回溯时路径过长的问题。

### 规则结果统一格式
```json
[
  {
    "rule_id": "duplicate_texture_sampling",
    "severity": "medium",
    "title": "重复纹理采样",
    "description": "检测到同一纹理在多个节点中被重复采样。",
    "node_ids": ["node_3", "node_8"],
    "suggestion": "考虑复用同一次采样结果。"
  }
]
```

### 要求
- 规则代码尽量纯函数化
- 每条规则独立
- 提供单元测试或最少样例验证

### 产出
- `analyzer/graph_utils.py`
- `analyzer/builtin_rules.py`
- `analyzer/run_analysis.py`

---

# 阶段 6：接入 AI 分析层

### 目标
让大模型对规则结果进行解释、总结与建议生成。

### 第一阶段 AI 的职责
- 根据规则命中结果输出自然语言报告
- 总结整体风险等级
- 生成优化建议
- 不得凭空编造不存在的节点和关系

### 不应由 AI 负责的部分
- 完整底层图解析
- 全部冗余检测主逻辑
- 自动修改 UE 材质图

### 推荐输入给 AI 的内容
1. 材质摘要
2. 关键输出链路摘要
3. 规则命中结果

### 推荐输出格式
```json
{
  "summary": "该材质存在中等程度的性能冗余。",
  "risk_level": "medium",
  "issues": [
    {
      "title": "重复纹理采样",
      "description": "BaseColor 链路中同一贴图被多次采样。"
    }
  ],
  "suggestions": [
    "考虑缓存采样结果并复用。",
    "清理未贡献输出的中间节点。"
  ]
}
```

### API 使用建议
- 使用常规可直接调用的 LLM API
- 在服务端读取 API key
- 不要把 key 写进前端

### 产出
- `services/ai_service.py`
- `prompts/report_prompt.txt`
- `prompts/suggestion_prompt.txt`

---

# 阶段 7：生成可视化报告页面

### 目标
满足“输出可视化性能分析报告”的作业要求。

### 页面必须包含

## 总览卡片
- 材质名
- 节点数
- 命中规则数
- 风险等级

## 问题列表
每个问题包含：
- 问题标题
- 严重等级
- 涉及节点
- 说明
- 优化建议

## AI 报告区
- 整体总结
- 风险结论
- 建议列表

## 导出区
- 导出 Markdown 报告
- 导出 JSON 报告

### 说明
第一版不要求绘制真正的节点图编辑器。
表格、卡片、展开面板、简单图表，已经可以构成“可视化报告”。

### 产出
- `services/report_service.py`
- `outputs/reports/*.md`
- `outputs/reports/*.json`

---

# 阶段 8：沉淀为可复用 Skills（必须做）

### 目标
把分析逻辑和判定规则整理成 TA 后续可扩展的模块。

### Skill 的推荐结构
```text
skills/
  duplicate_texture_sampling/
    skill.md
    rule.json
    prompt.txt
    examples.json

  dead_node_detection/
    skill.md
    rule.json
    prompt.txt
    examples.json
```

### 每个 Skill 包含什么

## 1. skill.md
说明：
- Skill 名称
- 功能目标
- 输入输出格式
- 适用场景
- 扩展说明

## 2. rule.json
保存规则配置，例如：
```json
{
  "rule_id": "dead_node_detection",
  "severity": "medium",
  "description": "检测未连接到最终输出的节点",
  "suggestion_template": "可移除无输出贡献节点，减少无效复杂度。"
}
```

## 3. prompt.txt
提供该 Skill 对应的 AI 解释模板。

## 4. examples.json
提供输入/输出示例，方便后续扩展。

### 主程序要求
- 启动时扫描 `skills/` 目录
- 自动读取规则配置
- 在页面上展示当前启用的 Skills

### 产出
- `skills/*`
- Skill 加载器

---

# 阶段 9：完善 UE Live 与文本双通道一致性（增强阶段）

### 目标
在 UE Live 主线已完成的基础上，验证并增强双输入源一致性与稳定性。

### 技术路线
采用 UE Python / Python Remote Execution + 文本输入回退策略：
- UE Live 作为默认主输入
- Paste Text 作为不可用场景下的回退输入
- 两路输入统一归一并做一致性校验

### 只需要实现最少函数
- `get_selected_material_name()`
- `export_selected_material_graph()`
- `export_material_graph_by_name(name)`

### 要求
- UE Live 与 Paste Text 最终输出结构一致，并记录来源与完整度
- 分析器与前端不需要因输入源不同而重写逻辑

### 产出
- `ue_bridge/remote_exec_client.py`
- `ue_bridge/export_material_graph.py`

---

# 阶段 10：为未来“AI 创作助手”预留扩展点

### 当前不实现，但必须预留

### 预留接口 1：图结构输入输出复用
现在：
- 用于分析：`material_graph`

未来：
- 可用于生成：`generated_material_graph`

### 预留接口 2：UE 执行层
现在：
- `export_material_graph()`

未来：
- `create_material_from_graph()`
- `update_material_graph()`

### 目的
保证未来扩展“AI 生成材质”时，不需要推翻分析工具的整体结构。

---

## 7. 开发分工建议（人类开发者 vs Agent）

### 人类开发者必须亲自决定
- 项目边界
- 数据结构字段
- 规则清单
- 严重等级定义
- 最终答辩表达
- 对规则结果正确性的判断

### Agent 适合完成的部分
- Streamlit 页面代码
- 数据结构代码骨架
- 文本解析器初版
- 规则函数初版
- AI 调用代码
- 报告生成代码
- Skills 模板文件
- README 和使用文档

### 必须人工验证的部分
- 节点连接方向是否正确
- 输出口识别是否正确
- 文本解析是否准确
- AI 报告是否编造内容
- 规则是否误判

---

## 8. 最小可交付版本（MVP）

如果时间有限，必须优先完成以下内容：

### 必做功能
- Streamlit Web 页面
- 支持 UE API / Remote Execution 获取材质图
- 将 UE Live 返回数据解析成结构化材质图
- 支持文本粘贴作为备选输入
- 至少 4 条规则分析
- AI 输出中文分析报告
- 至少 2 个 Skill 模块
- 可导出 Markdown / JSON 报告

### 可选加分
- UE Live 自动获取当前材质
- 图形化统计图
- 更丰富的 Skill 扩展机制
- 后续材质生成预览页

---

## 9. 推荐的实际开发顺序（非常重要）

Agent 必须严格按这个顺序开发：

1. 初始化项目目录
2. 定义 `material_graph` 数据结构
3. 实现 UE Live 导出最小函数（UE API / Remote Execution）
4. 完成 UE Live 解析与统一归一
5. 用 Streamlit 展示 UE Live 解析结果
6. 完成 4 条基础规则
7. 展示规则命中结果
8. 接入 AI 报告生成
9. 完成报告导出
10. 完成 Skills 目录与加载机制
11. 补齐 Paste Text 解析作为备选输入

不要跳步，不要一开始就做完整 Agent 平台。

---

## 10. 给 Agent 的执行原则

1. 优先保证系统跑通，不要先追求炫技
2. 每一层先做最小版本
3. 先用 mock / sample 数据，再接真实 UE 数据
4. UE Live 作为默认主输入，所有输入源统一归一到 `material_graph`
5. 规则优先，AI 解释其次
6. Skills 必须模块化，不能把所有规则写死在一个文件中
7. 所有代码应尽量可测试、可扩展、可替换
8. 后续扩展目标是“材质生成助手”，因此当前结构不能与分析功能强耦合

---

## 11. 参考资料（建议一并提供给 Agent）

### 参考资料 1：作业要求
文件：`作业要求.txt`

用途：
- 作为项目需求边界
- 用于检查最终功能是否覆盖作业要求

### 参考资料 2：课程转写文档
文件：`AI Agent x UE 编辑器工具开发.txt`

用途：
- 理解 Agent / Prompt / Rule / Tool / MCP / Skill 的关系
- 理解 UE Python Remote Execution 的整体思路
- 理解为什么能力封装应该模块化
- 理解为什么第一阶段不必先做复杂平台，而应先手搓闭环

从这份材料中应重点吸收的思想：
- Agent 可以理解为 LLM + Prompt/Rule + Tool/MCP + 可选知识库/RAG + 可选 Skill
- UE 可通过 Python Remote Execution 被外部脚本调用
- 将 UE 侧能力封装成函数，再交给外部调用层使用，会更好维护
- Skill 适合作为 Prompt/Rule/Tool 的复用模块
- 渐进式披露和按需加载能力，有利于控制复杂度

### 参考资料 3：UEEditorMCP
`UEEditorMCP库`

内容：仓库地址 `https://github.com/yangskin/UEEditorMCP.git`

用途：
- 作为 UE 编辑器能力开放层 / 桥接层的参考
- 重点参考其“如何从外部调用 UE”“如何封装 UE 编辑器能力”
- 不要把该库当作完整作业成品直接照搬

建议关注的参考点：
- UE 能力封装方式
- 外部调用 UE 的桥接思路
- 结构化返回数据的方式

---

## 12. 结论（给 Agent 的一句话任务说明）

请基于本说明文档，优先实现一个 **基于 Streamlit 的 UE AI 材质节点性能分析工具**。第一阶段优先支持 **UE Live（UE API / Remote Execution）直连导出材质图**，并将输入解析为统一 `material_graph` 结构；随后实现 **规则分析、AI 报告生成、可视化结果展示、Skills 模块化沉淀**；再补充 **Paste Text（复制节点文本）** 作为备选输入通道。项目必须保持良好模块化，并为未来扩展到 **UE AI 材质创作助手** 预留接口。

---

## 13. 当前实现步骤（已落地版本）

### 步骤 1：项目骨架初始化（已完成）
- 已建立 `data_models / parser / analyzer / services / skills / prompts / samples / outputs / ue_bridge` 目录。
- 已提供 `README.md` 与 `requirements.txt`。

### 步骤 2：统一数据结构（已完成）
- 已在 `data_models/material_graph.py` 定义统一结构：
  - `material_name`
  - `source_type`
  - `nodes`
  - `edges`
  - `outputs`
  - `stats`
- 已提供 `to_dict()` / `from_dict()` / `validate()`。
- 已提供样例：`samples/sample_graph_01.json`。

### 步骤 3：UE Live 最小桥接（进行中）
- 已实现客户端：`ue_bridge/remote_exec_client.py`。
- 已实现导出接口：`ue_bridge/export_material_graph.py`。
- 已实现归一解析：`parser/normalize_graph.py`、`parser/ue_api_parser.py`。

### 步骤 4：Web 最小展示（已完成）
- 已在 `app.py` 支持：
  - 加载样例图
  - UE Live 拉取
  - 显示摘要、节点、连线、输出

### 步骤 5：UE 选中后打开 Web（本轮新增）
- 已新增 UE 侧脚本：`ue_bridge/ue_open_web_for_selected_material.py`。
- 目标行为：在 UE 选中材质后，调用函数直接打开 Streamlit 页面，并附带 `material_name` 查询参数。
- 已在 `app.py` 增加 `material_name` 参数读取，并支持按参数材质名加载。

---

## 14. UE 里选择后打开 Web 的最小交付说明

### 功能目标
用户在 UE 中选中一个材质后，点击插件按钮（或执行 Python 函数）即可打开分析 Web 页面。

### 当前最小实现路径
1. 在 UE 中选中材质资产。
2. 执行 `open_web_for_selected_material()`。
3. 自动打开：`http://127.0.0.1:8501?material_name=...`。
4. Web 侧读取参数，并可按该材质名触发 UE Live 导出。

### UE 侧函数（已实现）
- `open_web_for_selected_material(web_url="http://127.0.0.1:8501")`
- `open_web_home(web_url="http://127.0.0.1:8501")`

### 插件化建议（手动启停模式）
- 不要求 UE 启动即自动起服务。
- 插件面板至少提供：
  - 启动服务
  - 停止服务
  - 打开分析页面（基于当前选择）
- 页面状态提示：未连接 / 已连接 / 异常。
