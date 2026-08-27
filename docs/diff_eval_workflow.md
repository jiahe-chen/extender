# Diff-Based Evaluation Workflow

## 概述

`diff_eval` workflow 已成功集成到 `benchmark_runner_langgraph.py` 中，实现了基于代码修改难度的 SOLID 违规检测。

## 核心思想

代码质量通过"修改难度"来衡量：
- **好的设计**：修改只需添加新代码
- **坏的设计**：修改需要改动大量现有代码

## 架构

### 1. 文件结构

```
benchmark_runner_langgraph.py
├── DiffEvalState (TypedDict)          # 状态定义
├── generate_scenario_for_diff()       # 场景生成
├── mock_modify_code_for_diff()        # Mock 修改（fallback）
├── analyze_diff_simple()              # Diff 分析
└── DiffEvalWorkflow (class)           # 主工作流
    └── process_example()              # 处理单个示例

prompts_diff_eval.py                   # 提示词配置
├── MODIFICATION_SCENARIOS             # 修改场景
├── MODIFICATION_PROMPT                # 代码修改提示词
└── Helper functions                   # 辅助函数
```

### 2. 工作流管道

```
START
  ↓
scenario_node      # 生成修改场景
  ↓
analysis_node      # [占位] 静态分析（未来增强）
  ↓
modify_node        # LLM 修改代码
  ↓
diff_node          # 分析 diff
  ↓
inference_node     # 推断违规
  ↓
finalize_node      # 最终输出
  ↓
END
```

### 3. 节点说明

#### scenario_node
- 根据 violation_type 生成修改场景
- 场景定义在 `prompts_diff_eval.py` 中
- 输出：`state["scenario"]`

#### analysis_node (占位)
- 当前为空节点
- 未来可添加静态分析
- 输出：`state["llm_analysis"] = None`

#### modify_node
- 使用 LLM 根据场景修改代码
- 使用 `format_modification_prompt()` 格式化提示词
- 失败时 fallback 到 `mock_modify_code_for_diff()`
- 输出：`state["modified_code"]`

#### diff_node
- 使用 `difflib.unified_diff` 生成 diff
- 当前版本只生成 diff_text
- TODO: 添加 DiffMetrics 计算
- 输出：`state["diff_text"]`

#### inference_node
- 当前简化版本：diff 非空 → 检测到违规
- TODO: 实现完整推断逻辑
  - 消费 diff metrics (modification_ratio, classes_changed)
  - 消费 llm_analysis
  - 应用推断规则（高修改率 → OCP 等）
- 输出：`state["inference_json"]`

#### finalize_node
- 返回 inference_json
- 格式兼容 `parse_model_response()`

## 使用方法

### 1. 配置

编辑 `benchmark_config.py`：

```python
# 设置 workflow 类型
WORKFLOW_TYPE = 'diff_eval'

# 选择模型
MODEL_SELECTION = ['qwen3:8b']

# 选择违规类型
VIOLATION_SELECTION = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
```

### 2. 运行基准测试

```bash
python benchmark_runner_langgraph.py
```

### 3. 快速测试

```bash
python test_diff_eval.py
```

## 输出格式

```json
{
  "is_detected": true,
  "violation_type": "SRP",
  "explanation": "Diff-based analysis: Code modification required"
}
```

## 未来增强

### 1. 静态分析节点
```python
def analysis_node(state: DiffEvalState) -> DiffEvalState:
    # 调用 LLM 进行静态分析
    prompt = format_static_analysis_prompt(state["code"])
    response = self.llm.invoke([HumanMessage(content=prompt)])
    # 解析并存储分析结果
    return {**state, "llm_analysis": parsed_analysis}
```

### 2. Diff Metrics 计算
```python
def analyze_diff_simple(original: str, modified: str) -> tuple[str, DiffMetrics]:
    # 计算详细指标
    metrics = DiffMetrics(
        lines_added=...,
        lines_removed=...,
        lines_modified=...,
        modification_ratio=...,
        classes_changed=[...]
    )
    return diff_text, metrics
```

### 3. 完整推断逻辑
```python
def inference_node(state: DiffEvalState) -> DiffEvalState:
    # 基于 diff metrics 的推断规则
    if modification_ratio > 0.3:
        # OCP 违规
    if len(classes_changed) == 1 and lines_modified > 5:
        # SRP 违规
    if len(classes_changed) > 2:
        # DIP 违规
    # 结合 llm_analysis
    # 生成综合结果
```

## 设计特点

1. **独立性**：不依赖 `solid_diff_evaluator.py`，所有代码都复制到 `benchmark_runner_langgraph.py`
2. **解耦提示词**：提示词在 `prompts_diff_eval.py` 中独立管理
3. **兼容性**：与 single_agent、two_agent 并行存在，不影响现有功能
4. **可扩展性**：预留 TODO 标记，方便后续迭代
5. **LangGraph 原生**：完全使用 LangGraph 状态管理和节点编排

## 测试结果

```
[OK] Workflow created
[OK] Got result
{
  "is_detected": true,
  "violation_type": "SRP",
  "explanation": "Diff-based analysis: Code modification required"
}
```

## 配置验证

`benchmark_config.py` 中的 `validate_config()` 已更新，支持 `'diff_eval'` workflow 类型。
