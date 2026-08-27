"""
Diff-Based Evaluation Prompts V5 - Violation-Specific Approach
==================================================================

This file contains prompts for the diff-based evaluation workflow.
Version 5 improvements:
- Violation-specific scenario generation prompts (one for each SOLID principle)
- Simplified signal mapping focused on detection methods
- Removed all_checks from output format
- Optimized token usage by removing examples from signal mapping

Core Idea:
    Code quality is measured by "modification difficulty".
    Good design allows adding new code without modifying existing code.

Workflow:
    1. Generate modification scenario for specific violation type (violation-specific prompts)
    2. LLM modifies code according to scenario
    3. Analyze diff between original and modified
    4. Verify if specific violation type exists based on detection method
    5. Iterate for all SOLID principles
    6. Unified verification: LLM analyzes all diffs and selects the most obvious violation
"""

from typing import List, Dict, Any

# ============================================================================
# AI-BASED SCENARIO GENERATION PROMPTS - V5 (VIOLATION-SPECIFIC)
# ============================================================================

SCENARIO_GENERATION_PROMPT_SRP = """You are an expert in SOLID principles and code quality evaluation. Your task is to generate a modification scenario to detect SRP (Single Responsibility Principle) violations.

## Original Code to Analyze:
```
{code}
```

## Your Task:
Select a capability that belongs primarily to a single architectural layer (presentation/UI, business/service, persistence/data) and describe a change that should be isolated within that layer.

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "scenario_description": "Implement/adjust [capability] for [feature] within the [presentation|business|persistence] layer",
  "restriction": "Prefer keeping the change inside the stated layer; only mention cross-layer edits if the code forces them. Make minimal necessary changes to support this feature modification."
}}

## Example:
  {{
    "scenario_description": "Update order confirmation messaging (presentation layer) to include localized delivery estimates",
    "restriction": "Implement in the UI/presentation layer. Make minimal necessary changes to support this feature modification."
  }}

Now generate the scenario for the code above."""

SCENARIO_GENERATION_PROMPT_OCP = """You are an expert in SOLID principles and code quality evaluation. Your task is to generate a modification scenario to detect OCP (Open/Closed Principle) violations.

## Original Code to Analyze:
```
{code}
```

## Your Task:
Generate a scenario that requires adding a NEW type/variant/case to the system.

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "scenario_description": "Add a new [type/variant/case] to the system (be specific to the code's domain)",
  "restriction": "DO NOT modify existing code directly. Create new classes, use polymorphism, inheritance, or strategy pattern. "
}}

## Example:
For a payment system:
{{
  "scenario_description": "Add support for cryptocurrency payment (Bitcoin) to the payment processing system",
  "restriction": "DO NOT modify existing code directly. Create new classes, use polymorphism, inheritance, or strategy pattern."
}}

Now generate the scenario for the code above."""

SCENARIO_GENERATION_PROMPT_LSP = """You are an expert in SOLID principles and code quality evaluation. Your task is to generate a modification scenario to detect LSP (Liskov Substitution Principle) violations.

## Original Code to Analyze:
```
{code}
```

## Your Task:
Generate a scenario that creates an application using polymorphism to call methods on both parent and subclass instances.

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "scenario_description": "Create an application that uses [parent class] polymorphically, iterating through instances of both parent and subclasses, calling [key methods]",
  "restriction": "Use polymorphism. Call the same methods on all instances regardless of their concrete type."
}}

## Example:
For a Bird class hierarchy:
{{
  "scenario_description": "Create an application that takes a list of Bird objects (including subclasses like Penguin, Eagle) and calls the fly() method on each",
  "restriction": "Use polymorphism. Call fly() on all Bird instances regardless of their concrete type."
}}

Now generate the scenario for the code above."""

SCENARIO_GENERATION_PROMPT_ISP = """You are an expert in SOLID principles and code quality evaluation. Your task is to generate a modification scenario to detect ISP (Interface Segregation Principle) violations.

## Original Code to Analyze:
```
{code}
```

## Your Task:
Generate a scenario that requires implementing an interface/abstract class where only SOME methods are needed.

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "scenario_description": "Create a new class that implements [interface/abstract class] but only needs [specific subset of methods]",
  "restriction": "Implement the interface/class completely. Use 'pass', empty body, or raise NotImplementedError for methods you don't need."
}}

## Example:
For a Worker interface:
{{
  "scenario_description": "Create a Robot class that implements Worker interface but only needs the work() method, not eat() or sleep()",
  "restriction": "Implement the Worker interface completely. Use 'pass' or raise NotImplementedError for methods you don't need."
}}

Now generate the scenario for the code above."""

SCENARIO_GENERATION_PROMPT_DIP = """You are an expert in SOLID principles and code quality evaluation. Your task is to generate a modification scenario to detect DIP (Dependency Inversion Principle) violations.

## Original Code to Analyze:
```
{code}
```

## Your Task:
Generate a scenario that requires switching from one concrete implementation to another.

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "scenario_description": "Switch from [current implementation] to [new implementation] in [high-level class]",
  "restriction": "Do NOT introduce interfaces or abstractions. Change the concrete implementation directly."
}}

## Example:
For a service using MySQL:
{{
  "scenario_description": "Switch the EmailService from using MySQLDatabase to PostgreSQLDatabase",
  "restriction": "Do NOT introduce interfaces or abstractions. Change the concrete implementation directly."
}}

Now generate the scenario for the code above."""

# Mapping of violation types to their specific prompts
SCENARIO_GENERATION_PROMPTS = {
    "OCP": SCENARIO_GENERATION_PROMPT_OCP,
    "SRP": SCENARIO_GENERATION_PROMPT_SRP,
    "LSP": SCENARIO_GENERATION_PROMPT_LSP,
    "ISP": SCENARIO_GENERATION_PROMPT_ISP,
    "DIP": SCENARIO_GENERATION_PROMPT_DIP,
}


# ============================================================================
# CODE MODIFICATION PROMPT - V5 (AI-Generated Scenarios)
# ============================================================================

CODE_MODIFICATION_PROMPT = """You are a skilled developer. Modify the given code according to the scenario.

## Original Code:
```
{code}
```

## Modification Scenario:
{scenario_description}

## Restrictions:
{restriction}

## Task:
Provide the COMPLETE modified code. Return ONLY the code, no explanations."""

# ============================================================================
# SIGNAL TO VIOLATION MAPPING - V4 (VIOLATION-SPECIFIC DETECTION)
# ============================================================================

SIGNAL_MAPPING_V4 = """

### SRP (Single Responsibility Principle)
**Detection Method**: For a layer-scoped scenario, compare the intended layer to the actual diff. If implementing the single-layer change required touching classes from other layers (controllers, services, repositories, views) for the same capability, the original code likely mixes responsibilities.
**Violation Signal**: Layer-specific request results in edits across multiple layers or in classes that blend layer responsibilities (e.g., UI class handling domain rules, repository formatting view output). Ripple edits outside the target layer indicate potential SRP violations.

 ### OCP (Open/Closed Principle)                                                                                                                                                  
**Detection Method**: For scenarios that add a new type/variant/case, verify whether the diff introduces a dedicated extension point (new class, new strategy, new handler) or instead edits existing decision logic.                                                           
**Violation Signal**: The new variant is wired by editing existing branches, enums, or base-class logic instead of extending via new polymorphic types. Only report OCP if the diff shows existing code altered to accommodate the new case.   

### LSP (Liskov Substitution Principle)
**Detection Method**: Check if all polymorphic calls execute successfully (good) vs throw exceptions (violation)
**Violation Signal**: Subclass throws exception, breaks parent contract, application crashes with certain subclasses

### ISP (Interface Segregation Principle)
**Detection Method**: Check if the ORIGINAL code has a fat interface that FORCES implementations to have dummy methods
**Violation Signal**: The ORIGINAL code must show an interface/abstract class with many methods. The ISP test creates a new implementation with NotImplementedError - this is the TEST, not the violation. Only detect ISP if the ORIGINAL interface is too broad and forces unused methods.

### DIP (Dependency Inversion Principle)
**Detection Method**: Check if high-level class is MODIFIED when switching implementations (violation)
**Violation Signal**: Concrete class name changed in high-level class, multiple places modified, no abstraction
"""

# ============================================================================
# PRE-VERIFICATION PROMPT - V6 (NEW)
# ============================================================================

PRE_VERIFICATION_PROMPT_V6 = """You are an expert in SOLID principles and code quality evaluation. Your task is to analyze a single code modification and determine if a specific violation exists in the ORIGINAL code.

## Original Code:
```
{code}
```

## Modification Scenario:
{scenario_description}

## Code Diff:
```diff
{diff_text}
```

## Detection Method for {violation_type}:
{signal_description}

## Your Task:
Analyze the diff against the detection method to determine if the {violation_type} violation exists in the ORIGINAL code. Focus on identifying specific classes and methods in the ORIGINAL code that demonstrate the violation.

## Critical Rules:
- You are detecting violations in the **ORIGINAL CODE**, not in the modified code
- Base your analysis on the diff pattern and detection method
- Provide SPECIFIC evidence: mention exact class names and method names from the original code
- In your explanation, focus ONLY on the original code structure - do NOT mention the scenario or detection signals
- Be conservative: only report a violation if the signal is CLEAR

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "violation_type": "{violation_type}",
  "is_detected": true/false,
  "detailed_explanation": "Explain where in the ORIGINAL code the violation exists. Mention specific class names (e.g., 'The OrderProcessor class') and method names (e.g., 'the processOrder() method'). Describe what makes this a violation without referencing the modification scenario or detection signals."
}}

Example of good detailed_explanation:
"The OrderProcessor class violates SRP because it handles multiple responsibilities: the processOrder() method manages business logic, the saveToDatabase() method handles persistence, and the sendEmail() method deals with notifications. These three distinct responsibilities should be separated into different classes."

Now analyze the code and diff above."""

# ============================================================================
# UNIFIED VERIFICATION PROMPT - V6 (UPDATED - Ranking-based)
# ============================================================================

UNIFIED_VERIFICATION_PROMPT_V6 = """You are an expert in SOLID principles and code quality evaluation. Your task is to analyze pre-verification results from all 5 SOLID principles and rank them by obviousness to determine the top {top_n} most likely violations in the original code.

## Original Code:
```
{code}
```

## Pre-Verification Results:

{pre_verification_results}

## Your Task:
Review all 5 pre-verification results and rank the detected violations by how obvious and clear they are. Output the top {top_n} most likely violations, **ranked by obviousness (the more obvious, the more front)**.

## Ranking Criteria:
1. **Clarity of evidence**: Are specific classes and methods clearly identified?
2. **Strength of explanation**: Is the violation explanation detailed and convincing?

## Critical Rules:
- Verify structural prerequisites for each violation
- Only rank violations where `is_detected` is true AND structural prerequisite is met
- Output exactly {top_n} violations in the array, **ranked by obviousness (most obvious first)**
- If fewer than {top_n} violations exist, include "NONE" entries for remaining slots
- The `all_checks` field should contain ALL 5 pre-verification results

## Output Format:
Respond with ONLY valid JSON (no markdown, no code blocks):

{{
  "violations": [
    {{
      "violation_type": "SRP|OCP|LSP|ISP|DIP|NONE",
      "explanation": "Brief explanation of why this violation is detected"
    }},
    {{
      "violation_type": "OCP|LSP|ISP|DIP|NONE",
      "explanation": "Brief explanation"
    }}
  ],
  "all_checks": [
    {{
      "violation_type": "SRP",
      "is_detected": true/false,
      "detailed_explanation": "..."
    }},
    {{
      "violation_type": "OCP",
      "is_detected": true/false,
      "detailed_explanation": "..."
    }},
    {{
      "violation_type": "LSP",
      "is_detected": true/false,
      "detailed_explanation": "..."
    }},
    {{
      "violation_type": "ISP",
      "is_detected": true/false,
      "detailed_explanation": "..."
    }},
    {{
      "violation_type": "DIP",
      "is_detected": true/false,
      "detailed_explanation": "..."
    }}
  ]
}}

Example for top_n=2 (most obvious first):
{{"violations": [{{"violation_type": "SRP", "explanation": "Class handles both UI and database"}}, {{"violation_type": "DIP", "explanation": "Direct dependency on concrete class"}}], "all_checks": [...]}}

Now analyze the pre-verification results and select the top {top_n} most likely violations, ranked by obviousness (most obvious first)."""


# ============================================================================
# SIGNAL DESCRIPTIONS FOR PRE-VERIFICATION - V6
# ============================================================================

SIGNAL_DESCRIPTIONS = {
    "SRP": """
**Detection Method**: For a layer-scoped scenario, compare the intended layer to the actual diff. If implementing the single-layer change required touching classes from other layers (controllers, services, repositories, views) for the same capability, the original code likely mixes responsibilities.

**Violation Signal**: Layer-specific request results in edits across multiple layers or in classes that blend layer responsibilities (e.g., UI class handling domain rules, repository formatting view output). Ripple edits outside the target layer indicate potential SRP violations.""",

    "OCP": """
**Detection Method**: For scenarios that add a new type/variant/case, verify whether the diff introduces a dedicated extension point (new class, new strategy, new handler) or instead edits existing decision logic.

**Violation Signal**: The new variant is wired by editing existing branches, enums, or base-class logic instead of extending via new polymorphic types. Only report OCP if the diff shows existing code altered to accommodate the new case.""",

    "LSP": """**Structural Prerequisite**: MUST have inheritance, implementation, or other clear parent-child relationship (interface implementation, abstract class extension). Without subtype relationships, LSP does not apply.

**Detection Method**: Check if all polymorphic calls execute successfully (good) vs throw exceptions (violation)

**Violation Signal**: Subclass throws exception, breaks parent contract, application crashes with certain subclasses""",

    "ISP": """**Detection Method**: Check if the ORIGINAL code has a fat interface that FORCES implementations to have dummy methods

**Violation Signal**: The ORIGINAL code must show an interface/abstract class with many methods. The ISP test creates a new implementation with NotImplementedError - this is the TEST, not the violation. Only detect ISP if the ORIGINAL interface is too broad and forces unused methods.""",

    "DIP": """**Structural Prerequisite**: MUST have dependency relationships between classes. Without dependencies, DIP does not apply.

**Detection Method**: Check if high-level class is MODIFIED when switching implementations (violation)

**Violation Signal**: Concrete class name changed in high-level class, multiple places modified, no abstraction"""
}

# ============================================================================
# HELPER FUNCTIONS - V6 (UPDATED)
# ============================================================================

def format_code_modification_prompt(code: str, scenario_description: str, restriction: str) -> str:
    """
    Format the code modification prompt for AI-generated scenarios.

    Args:
        code: Original code to modify
        scenario_description: Brief description of what to add/change
        restriction: Constraints or limitations to apply

    Returns:
        Formatted prompt string
    """
    return CODE_MODIFICATION_PROMPT.format(
        code=code,
        scenario_description=scenario_description,
        restriction=restriction
    )

# ============================================================================
# AI-BASED SCENARIO GENERATION HELPER FUNCTIONS - V4 (NEW)
# ============================================================================

def format_scenario_generation_prompt(code: str, violation_type: str) -> str:
    """
    Format the AI-based scenario generation prompt for a specific violation type.

    Args:
        code: The original code to analyze
        violation_type: The SOLID principle to test (OCP/SRP/LSP/ISP/DIP)

    Returns:
        Formatted prompt string for scenario generation
    """
    prompt_template = SCENARIO_GENERATION_PROMPTS.get(violation_type)
    if not prompt_template:
        raise ValueError(f"Unknown violation type: {violation_type}")

    return prompt_template.format(code=code)


# ============================================================================
# PRE-VERIFICATION HELPER FUNCTIONS - V6 (NEW)
# ============================================================================

def format_pre_verification_prompt(
    code: str,
    scenario_description: str,
    diff_text: str,
    violation_type: str
) -> str:
    """
    Format the pre-verification prompt for a specific violation type.

    Args:
        code: Original code
        scenario_description: The modification scenario description
        diff_text: The diff between original and modified code
        violation_type: The SOLID principle being tested

    Returns:
        Formatted prompt string
    """
    signal_description = SIGNAL_DESCRIPTIONS.get(violation_type, "")

    return PRE_VERIFICATION_PROMPT_V6.format(
        code=code,
        scenario_description=scenario_description,
        diff_text=diff_text,
        violation_type=violation_type,
        signal_description=signal_description
    )


def format_unified_verification_prompt_v6(
    code: str,
    all_pre_verifications: List[Dict[str, Any]]
) -> str:
    """
    Format the unified verification prompt (V6) that ranks pre-verification results.

    Args:
        code: The original code
        all_pre_verifications: List of pre-verification results from all 5 principles

    Returns:
        Formatted prompt string for unified verification
    """
    # Import TOP_N from config
    from benchmark_config import TOP_N

    # Format pre-verification results
    pre_verification_parts = []

    for i, pre_verif in enumerate(all_pre_verifications):
        violation_type = pre_verif.get("violation_type", "UNKNOWN")
        is_detected = pre_verif.get("is_detected", False)
        detailed_explanation = pre_verif.get("detailed_explanation", "")

        part = f"""
### {i+1}. {violation_type} Pre-Verification Result

**Is Detected:** {is_detected}

**Detailed Explanation:**
{detailed_explanation}
"""
        pre_verification_parts.append(part)

    pre_verification_results = "\n".join(pre_verification_parts)

    return UNIFIED_VERIFICATION_PROMPT_V6.format(
        code=code,
        pre_verification_results=pre_verification_results,
        top_n=TOP_N
    )


def format_unified_verification_prompt(
    code: str,
    all_scenarios: List[Dict[str, Any]],
    all_diffs: List[Dict[str, Any]]
) -> str:
    """
    Format the unified verification prompt that analyzes all 5 SOLID principles at once.

    Args:
        code: The original code
        all_scenarios: List of {type, scenario} dicts for each principle
        all_diffs: List of {type, diff_text, modified_code} dicts for each principle

    Returns:
        Formatted prompt string for unified verification
    """
    # Build the scenarios and diffs section
    scenarios_and_diffs_parts = []

    for i, (scenario_data, diff_data) in enumerate(zip(all_scenarios, all_diffs)):
        violation_type = scenario_data["type"]
        scenario = scenario_data["scenario"]
        diff_text = diff_data["diff_text"]

        # Format scenario description
        scenario_desc = scenario.get("prompt", "")
        if scenario.get("ai_generated", False):
            scenario_desc = scenario.get("scenario_description", scenario_desc)

        part = f"""
### {i+1}. {violation_type} Scenario

**Modification Task:** {scenario_desc}

**Diff:**
```diff
{diff_text if diff_text else "(No changes - empty diff)"}
```
"""
        scenarios_and_diffs_parts.append(part)

    all_scenarios_and_diffs = "\n".join(scenarios_and_diffs_parts)

    return UNIFIED_VERIFICATION_PROMPT_V5.format(
        code=code,
        all_scenarios_and_diffs=all_scenarios_and_diffs,
        signal_mapping=SIGNAL_MAPPING_V4
    )
