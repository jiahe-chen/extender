# V3 Changes Summary

## Overview
Version 3 simplifies the detection system and implements priority-based violation selection.

## Key Changes

### 1. Removed Confidence and Severity Scoring
**Before (V2):**
```json
{
  "is_detected": true,
  "confidence": 0.95,
  "violation_type": "DIP",
  "severity": "high",
  "signal": "...",
  "explanation": "..."
}
```

**After (V3):**
```json
{
  "is_detected": true,
  "violation_type": "DIP",
  "signal": "...",
  "explanation": "..."
}
```

**Rationale:**
- Confidence scores were arbitrary and not well-calibrated
- Severity was redundant (all violations are important)
- Binary detection (yes/no) is clearer and easier to evaluate

### 2. Priority-Based Selection (D > I > L > O > S)

**Before (V2):**
- Selected violation with highest confidence
- If multiple violations had same confidence, selection was random

**After (V3):**
```python
VIOLATION_PRIORITY = {
    "DIP": 5,  # Highest priority - architectural issue
    "ISP": 4,
    "LSP": 3,
    "OCP": 2,
    "SRP": 1   # Lowest priority - implementation issue
}
```

**Rationale:**
- Architectural issues (DIP, ISP) are more fundamental than design issues (LSP, OCP)
- Design issues are more fundamental than implementation issues (SRP)
- Deterministic selection when multiple violations detected

**Example:**
If both DIP and LSP are detected, V3 will always select DIP.

### 3. Improved MODIFICATION_SCENARIOS

**Key Improvements:**
- **Explicit instructions** with "CRITICAL INSTRUCTIONS" sections
- **Correct and wrong examples** for each violation type
- **Tailored constraints** per violation type

**Example - DIP Scenario:**
```python
"DIP": """Switch from one concrete low-level implementation to another.

CRITICAL INSTRUCTIONS:
1. Change ONLY the concrete class name (MySQLDatabase → PostgreSQLDatabase)
2. Do NOT add interfaces or abstractions
3. Do NOT change the type of the dependency field
4. The goal is to show how painful it is to switch implementations without abstraction

Example of CORRECT modification:
BEFORE: self.database = MySQLDatabase()
AFTER:  self.database = PostgreSQLDatabase()

Example of WRONG modification (do NOT do this):
BEFORE: self.database = MySQLDatabase()
AFTER:  self.database = Database()  # ❌ This adds abstraction!
```

### 4. Tailored Constraints Per Violation Type

**Before (V2):**
All violations used the same generic constraints:
```python
constraints = [
    "Make minimal changes to existing code",
    "Prefer adding new code over modifying existing",
    "Keep backwards compatibility"
]
```

**After (V3):**
Each violation has specific constraints:
```python
CONSTRAINTS_BY_VIOLATION = {
    "DIP": [
        "Change concrete class names in instantiation code",
        "Do NOT add interfaces or abstractions",
        "Do NOT change dependency field types",
        "Modify all places where the concrete class is used"
    ],
    "OCP": [
        "Modify existing conditional statements (if/elif/switch)",
        "Do NOT create new classes",
        "Add new branches to existing conditionals"
    ],
    # ... etc
}
```

### 5. Enhanced Signal Mapping

**V3 adds concrete diff patterns to look for:**

```python
### DIP (Dependency Inversion Principle)
**Signal Pattern**: High-level class changes when switching low-level implementations
**Diff Pattern to Look For**:
  - Concrete class name changed in instantiation (new X() → new Y())
  - Field type remains concrete (not changed to interface)
  - Multiple places in high-level class modified
  - NO interface or abstraction added
**Why it's a violation**: High-level module depends on concrete low-level implementation instead of abstraction.

**Example Diff**:
```diff
@@ class EmailService:
     def __init__(self):
-        self.db = MySQLDatabase()
+        self.db = PostgreSQLDatabase()  # Concrete class changed
```

**Key Distinction**: If you see an interface being added (+ interface Database), that's NOT a DIP violation - that's fixing the violation!
```

### 6. Improved Few-Shot Examples

**V3 adds 5 comprehensive examples:**
1. OCP violation (positive) - modifying conditional branches
2. DIP violation (positive) - changing concrete dependencies
3. DIP non-violation (negative) - abstraction added (fixing the violation)
4. LSP violation (positive) - subclass breaks contract
5. SRP non-violation (negative) - distinguishing DIP from SRP

Each example includes:
- Original code
- Modification scenario
- Diff
- Step-by-step analysis
- Expected JSON output

## Files Modified

### 1. `prompts_diff_eval_v3.py` (NEW)
- New prompt file with all V3 improvements
- Removed confidence/severity from output format
- Added VIOLATION_PRIORITY constant
- Enhanced signal mapping with concrete diff patterns
- Improved few-shot examples

### 2. `benchmark_runner_langgraph.py`
**Changes:**
- Import from `prompts_diff_eval_v3` instead of `v2`
- Import `VIOLATION_PRIORITY` and `get_constraints`
- Updated `_parse_inference_response()` to remove confidence/severity
- Updated `generate_scenario_for_diff()` to use tailored constraints
- Updated `finalize_node()` to use priority-based selection:
  ```python
  # V3: Sort by priority (DIP > ISP > LSP > OCP > SRP)
  best_result = max(detected_results,
                    key=lambda x: VIOLATION_PRIORITY.get(x.get("violation_type", ""), 0))
  ```
- Updated logger to remove confidence/severity from output
- Changed workflow marker to "diff_eval_v3"
- Added "selection_method": "priority" to output

## Expected Improvements

### 1. Better DIP Detection
**Problem in V2:**
- DIP examples were often misclassified as LSP or OCP
- LLM would "fix" the code by adding abstractions
- 0/45 DIP examples correctly detected

**Expected in V3:**
- Explicit instructions prevent LLM from adding abstractions
- Clearer signal mapping helps verification
- Priority-based selection ensures DIP is chosen when detected

### 2. Reduced False Positives
**Problem in V2:**
- LSP scenario created subclasses that didn't actually violate LSP
- OCP scenario sometimes just added new classes (good design)

**Expected in V3:**
- More precise scenarios with contract-breaking requirements
- Better distinction between "extension" and "violation"

### 3. Deterministic Selection
**Problem in V2:**
- When multiple violations had same confidence, selection was random
- Hard to reproduce results

**Expected in V3:**
- Priority-based selection is deterministic
- Same violations always produce same result

## Testing V3

To test V3, run:
```bash
# Make sure benchmark_config.py has:
# WORKFLOW_TYPE = "diff_eval"

python benchmark_runner_langgraph.py
```

Results will be saved with:
- `"workflow": "diff_eval_v3"` marker
- `"selection_method": "priority"` field
- No confidence/severity fields

## Backward Compatibility

V3 is **not backward compatible** with V2 results:
- Output JSON structure is different (no confidence/severity)
- Selection logic is different (priority vs confidence)
- Scenarios produce different modifications

To compare V2 and V3:
1. Keep V2 results in separate directory
2. Run V3 with new output directory
3. Compare detection_success rates

## Next Steps

After testing V3:
1. Analyze detection_success rate for DIP examples
2. Check if priority-based selection improves overall accuracy
3. Review log files to see if scenarios produce expected diffs
4. Consider further refinements based on results
