# UE 与 Web 工具连接与问题复盘（UE5.3）

## 1. 结论先说

当前问题不是“完全连接失败”，而是“连接成功，但 UE Live 节点读取不稳定”。

已确认成功的部分：
1. UE 可以启动本地桥接服务。
2. Web 能拿到 UE 选中材质路径和名称。
3. `/health` 和 `/run_python` 通信可用。

当前未完全稳定的部分：
1. `M_ShockWave` 在 UE Live 通道中返回 `nodes=0`。
2. 但粘贴文本通道能解析出大量节点，说明材质图本身是有数据的。

## 2. 根因分析（为什么会这样）

### 2.1 不是材质为空

你提供的节点文本中存在大量 `MaterialGraphNode_*`、`MaterialExpression*`，并且有连线信息，说明材质图有效。

### 2.2 主要是 UE5.3 的 Python API 差异

在调试中出现过错误：
1. `MaterialEditingLibrary.get_material_expressions` 在 UE5.3 环境中不存在。
2. 部分 API 在不同版本或不同上下文（编辑器对象 / 运行时对象）可见性不同。

这意味着：
1. 脚本“思路正确”，但单一 API 路径不够稳。
2. 必须做多路径回退读取，而不是只依赖一个函数。

### 2.3 也存在操作层面误用

早期报错如 `Unrecognized class /health`、`SyntaxError`，本质是控制台命令格式问题：
1. 在 UE `Cmd` 中执行 Python 必须带 `py` 前缀。
2. 同一行多个语句必须用 `;` 分隔。
3. HTTP 请求不能在 UE Cmd 里执行，要在系统终端执行。

## 3. 当前脚本是否正确

结论：整体方向正确，但 UE Live 节点提取需要“版本兼容策略”。

目前脚本已做的正确点：
1. 桥接协议清晰：`GET /health`、`POST /run_python`。
2. UE 侧提供了最小导出函数：
	- `get_selected_material_name()`
	- `export_selected_material_graph()`
	- `export_material_graph_by_name(name)`
3. Web 侧支持按 query 参数加载材质。

仍需增强的点：
1. UE5.3 下表达式读取路径需进一步覆盖（不同资产结构）。
2. 后续要补父材质 / 函数调用展开策略。

## 4. 推荐解决方案（分层）

### 4.1 短期可交付方案（已可用）

1. UE Live 负责“选择材质 + 打开网页 + 基础连接”。
2. 节点解析先用 Paste Text 通道兜底（已验证可解析你的案例）。
3. 先继续完成规则分析与报告流程，不被 UE5.3 API 差异阻断。

### 4.2 中期稳定方案（建议下一步）

1. UE 侧继续补充表达式读取回退路径。
2. 增加调试接口，返回每条读取路径的命中数量。
3. 引入“UE Live + Paste Text 双通道一致性校验”。

### 4.3 最终产品化方案

1. 做成 UE 插件按钮（手动启停服务，不自动常驻）。
2. 页面显示连接状态、错误详情、回退策略提示。
3. 一键切换到 Paste Text 解析，保证工具可用性。

## 5. 标准连接步骤（全部使用 UE Cmd 的 `py` 前缀）

## 5.1 前置准备

1. 在 UE 启用插件：
	- Python Editor Script Plugin
	- Editor Scripting Utilities
2. 重启 UE。
3. 本地启动 Web：
	- `streamlit run app.py`
4. 确认网页可打开：
	- `http://127.0.0.1:8501`

## 5.2 脚本放置

将以下文件放到 UE 项目 `Content/Python/`：
1. `ue_http_bridge_server.py`
2. `ue_open_web_for_selected_material.py`

## 5.3 启动桥接服务（UE Cmd）

在 UE Output Log 的 `Cmd` 输入：

`py import ue_http_bridge_server as bridge; bridge.start_bridge()`

成功标志：
1. 日志出现 `UE Bridge started at http://127.0.0.1:30010`。

## 5.4 验证服务（PowerShell）

在系统终端执行：

`Invoke-RestMethod http://127.0.0.1:30010/health`

预期返回包含：
1. `ok=True`
2. `service=ue-bridge`

## 5.5 选中材质并打开网页（UE Cmd）

先在 Content Browser 选中一个 Material，然后执行：

`py import ue_open_web_for_selected_material as launcher; launcher.open_web_for_selected_material()`

预期：
1. 浏览器打开带 `material_name` 参数的页面。

## 5.6 网页触发加载

1. 点击 `Load from Query Material`。
2. 若节点仍为 0，改用 `Parse Pasted Text`（兜底可用）。

## 6. 常见错误与正确写法

### 6.1 SyntaxError（同一行多语句）

错误示例：
1. `py import a as b b.run()`

正确示例：
1. `py import a as b; b.run()`

### 6.2 Unrecognized class /health

原因：
1. 把 HTTP 请求写到了 UE Cmd。

正确做法：
1. 在 PowerShell 执行 `Invoke-RestMethod`。

### 6.3 ModuleNotFoundError

原因：
1. Python 文件不在 `Content/Python`。

解决：
1. 复制脚本到 UE 项目 Python 路径后重试。

### 6.4 500 Internal Server Error

原因：
1. UE 侧执行导出函数报错（常见为 API 不存在、材质路径错误）。

解决：
1. 先确认 `health` 正常。
2. 重载脚本再启动：
	- `py import importlib, ue_http_bridge_server as bridge; importlib.reload(bridge); bridge.stop_bridge(); bridge.start_bridge()`

## 7. 停止服务（UE Cmd）

`py import ue_http_bridge_server as bridge; bridge.stop_bridge()`

## 8. 当前阶段建议

1. 连接链路已可用，继续推进规则分析和报告功能。
2. UE Live 节点提取继续迭代，但不阻塞主功能开发。
3. 后续插件化时采用“手动启停服务 + 一键打开网页 + 失败自动回退文本解析”。
