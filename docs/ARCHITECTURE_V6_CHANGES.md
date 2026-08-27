# Diff-Eval Architecture V6 - Pre-Verification Layer

## Overview
V6 introduces a **pre-verification layer** that analyzes each SOLID principle individually before the final unified verification. This two-stage approach provides more detailed analysis and better ranking of violations.

## Architecture Changes

### Previous Architecture (V5)
```
For each violation (5 iterations):
  scenario → modify → diff
↓
verification (analyze all 5 diffs at once)
↓
finalize
```

### New Architecture (V6)
```
For each violation (5 iterations):
  scenario → modify → diff → pre_verification
↓
verification (rank pre-verification results)
↓
finalize
```

## Key Components

### 1. Pre-Verification Node (NEW)
**Location**: `benchmark_runner_langgraph.py` - `pre_verification_node()`

**Input**:
- Original code
- Modification scenario
- Diff text
- Signal description for specific violation type

**Output** (JSON):
```json
{
  "violation_type": "SRP|OCP|LSP|ISP|DIP",
  "is_detected": true/false,
  "detailed_explanation": "Specific explanation with class and method names"
}
```

**Key Features**:
- Analyzes ONE violation type at a time
- Provides detailed explanation with specific class/method names
- Does NOT mention scenario or detection signals in explanation
- Focuses on describing the violation in the ORIGINAL code

### 2. Unified Verification Node (UPDATED)
**Location**: `benchmark_runner_langgraph.py` - `verification_node()`

**Input**:
- Original code
- 5 pre-verification results (one for each SOLID principle)

**Output** (JSON):
```json
{
  "is_detected": true/false,
  "violation_type": "SRP|OCP|LSP|ISP|DIP|null",
  "explanation": "Why this violation is most obvious",
  "all_checks": [
    {
      "violation_type": "SRP",
      "is_detected": true/false,
      "detailed_explanation": "..."
    },
    // ... for all 5 principles
  ]
}
```

**Key Features**:
- Ranks violations by obviousness
- Selects the MOST OBVIOUS violation
- Uses ranking criteria:
  1. Clarity of evidence (specific classes/methods identified)
  2. Strength of explanation (detailed and convincing)

### 3. New Prompts

#### PRE_VERIFICATION_PROMPT_V6
**Location**: `prompts_diff_eval.py`

**Purpose**: Analyze a single violation type with detailed evidence

**Key Instructions**:
- Focus on ORIGINAL code violations
- Mention specific class and method names
- Do NOT reference scenario or detection signals in explanation
- Be conservative (only report if signal is CLEAR)

#### UNIFIED_VERIFICATION_PROMPT_V6
**Location**: `prompts_diff_eval.py`

**Purpose**: Rank pre-verification results and select most obvious violation

**Key Instructions**:
- Review all 5 pre-verification results
- Rank by obviousness and clarity
- Select AT MOST ONE violation
- Include all 5 results in `all_checks`

### 4. Signal Descriptions
**Location**: `prompts_diff_eval.py` - `SIGNAL_DESCRIPTIONS`

Extracted from inline code to a module-level dictionary for reusability:
- SRP: Layer-scoped changes requiring cross-layer edits
- OCP: New variants requiring existing code modifications
- LSP: Polymorphic calls throwing exceptions
- ISP: Fat interfaces forcing dummy implementations
- DIP: High-level class modifications when switching implementations

## State Changes

### DiffEvalState (UPDATED)
```python
class DiffEvalState(TypedDict):
    code: str
    language: str
    modified_code: str  # Temporary

    # Collected data
    all_scenarios: List[Dict[str, Any]]
    all_diffs: List[Dict[str, Any]]
    all_pre_verifications: List[Dict[str, Any]]  # NEW in V6

    # Final result
    detection_result: Dict[str, Any]
    final_result: str
    error: Optional[str]
```

## Helper Functions

### New Functions
1. **`format_pre_verification_prompt()`**
   - Formats pre-verification prompt for a specific violation type
   - Includes code, scenario, diff, and signal description

2. **`format_unified_verification_prompt_v6()`**
   - Formats unified verification prompt with pre-verification results
   - Replaces V5's `format_unified_verification_prompt()`

3. **`_parse_pre_verification_response()`**
   - Parses pre-verification JSON response
   - Extracts: violation_type, is_detected, detailed_explanation

4. **`_parse_unified_verification_response()`**
   - Parses unified verification JSON response
   - Extracts: is_detected, violation_type, explanation, all_checks

## Workflow Graph Changes

### V5 Graph
```
START → iterator → scenario → analysis → modify → diff
                                                    ↓
                                          [conditional routing]
                                                    ↓
                                    scenario (loop) OR verification
                                                    ↓
                                                finalize → END
```

### V6 Graph
```
START → iterator → scenario → analysis → modify → diff → pre_verification
                                                              ↓
                                                    [conditional routing]
                                                              ↓
                                              scenario (loop) OR verification
                                                              ↓
                                                          finalize → END
```

**Key Change**: Conditional routing now happens from `pre_verification` instead of `diff`

## Benefits of V6 Architecture

### 1. More Detailed Analysis
- Each violation gets individual attention with specific evidence
- Pre-verification provides detailed explanations with class/method names
- Better traceability of why violations are detected

### 2. Better Ranking
- LLM can compare detailed pre-verification results
- Ranking based on clarity and strength of evidence
- More objective selection of "most obvious" violation

### 3. Improved Explainability
- `all_checks` contains detailed explanations for all 5 principles
- Users can see why each violation was/wasn't detected
- Final explanation focuses on why selected violation is most obvious

### 4. Separation of Concerns
- Pre-verification: Detailed analysis of individual violations
- Unified verification: High-level ranking and selection
- Each stage has a clear, focused responsibility

## Output Format Changes

### Final Output
```json
{
  "is_detected": true/false,
  "violation_type": "SRP|OCP|LSP|ISP|DIP|null",
  "explanation": "Why this is most obvious",
  "all_checks": [
    {
      "violation_type": "SRP",
      "is_detected": true/false,
      "detailed_explanation": "Detailed explanation with class/method names"
    },
    // ... 4 more
  ],
  "workflow": "diff_eval_v6",
  "selection_method": "ranking_llm",
  // ... other metadata
}
```

**Changes from V5**:
- Removed `signal` field (replaced by `explanation`)
- `all_checks` now contains `detailed_explanation` instead of `signal`
- `workflow` changed from `diff_eval_v5` to `diff_eval_v6`
- `selection_method` changed from `unified_llm` to `ranking_llm`

## Migration Notes

### Backward Compatibility
- V6 is NOT backward compatible with V5 results
- Output format has changed (no `signal` field)
- `all_checks` structure is different

### Testing
Both files pass Python syntax validation:
```bash
python -m py_compile prompts_diff_eval.py
python -m py_compile benchmark_runner_langgraph.py
```

## Files Modified

1. **`prompts_diff_eval.py`**
   - Added: `PRE_VERIFICATION_PROMPT_V6`
   - Updated: `UNIFIED_VERIFICATION_PROMPT_V6`
   - Added: `SIGNAL_DESCRIPTIONS` dictionary
   - Added: `format_pre_verification_prompt()`
   - Added: `format_unified_verification_prompt_v6()`

2. **`benchmark_runner_langgraph.py`**
   - Updated: `DiffEvalState` (added `all_pre_verifications`)
   - Added: `_parse_pre_verification_response()`
   - Added: `_parse_unified_verification_response()`
   - Added: `pre_verification_node()`
   - Updated: `verification_node()` (uses V6 prompt and ranking logic)
   - Updated: `finalize_node()` (V6 metadata)
   - Updated: Workflow graph (added pre_verification node)

## Next Steps

1. **Test V6 Architecture**
   - Run benchmark on sample code
   - Verify pre-verification outputs
   - Check unified verification ranking

2. **Compare V5 vs V6**
   - Accuracy comparison
   - Explanation quality
   - Processing time

3. **Tune Prompts**
   - Adjust pre-verification prompt based on results
   - Refine ranking criteria in unified verification
   - Optimize signal descriptions

## Summary

V6 introduces a **two-stage verification process**:
1. **Pre-verification**: Detailed individual analysis of each SOLID principle
2. **Unified verification**: Ranking and selection of most obvious violation

This architecture provides better explainability, more detailed evidence, and more objective violation selection compared to V5's single-stage approach.