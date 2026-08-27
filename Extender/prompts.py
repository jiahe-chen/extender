"""
SOLID Detection Prompts
=======================

This file contains all prompts used in SOLID violation detection.
Modify these prompts to customize the detection behavior.

Quick Guide:
- DETECTION_PROMPT: Main prompt for single-agent violation detection
- Shared constants: SOLID_PRINCIPLES_DEF, OUTPUT_FORMAT_DEF, COMMON_RULES_DEF
"""

# ============================================================================
# SHARED PROMPT COMPONENTS (Used across all workflows)
# ============================================================================

# Complete detector prompt template (used by both single agent and two agent detector)
DETECTOR_PROMPT_BASE = """You are a specialized SOLID principle violation detector.

Your role:
1. Analyze code for SOLID principle violations
2. Identify the top {top_n} most likely violations, **ranked by obviousness (the more obvious, the more front)**
3. Provide clear explanations for each

## SOLID Principles:
- **SRP**: A class does too many unrelated tasks.
- **OCP**: Multiple `if-else` or `switch` blocks for logic that should be handled by polymorphism.
- **LSP**: Subclasses override behavior in a way that breaks the contract of the base class (e.g., throw exceptions).
- **ISP**: Interfaces that are too large or force implementing unnecessary methods.
- **DIP**: High-level classes directly depend on low-level classes instead of abstractions.

## Output Format:
Respond with ONLY a valid JSON object. Do NOT wrap it in markdown code blocks (no ```json or ```). Output raw JSON only:

{output_format_example}

Rules:
- Output ONLY raw JSON, no markdown formatting, no code blocks, no additional text
- Output exactly {top_n} violations in the array, **ranked by obviousness (most obvious first)**
- Each violation must have: violation_type (SRP/OCP/LSP/ISP/DIP), explanation
- If fewer than {top_n} violations exist, include "NONE" entries: {{"violation_type": "NONE", "explanation": "No violation detected"}}

Example for top_n={top_n} (most obvious first):
{example}
"""

# ============================================================================
# SINGLE AGENT DETECTION PROMPT
# ============================================================================

DETECTION_PROMPT = """Analyze this code:
{input_code}

{detector_prompt_base}
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_detection_prompt(workflow_type: str = 'single_agent') -> str:
    """
    Get the appropriate prompt for the specified workflow type.

    Args:
        workflow_type: 'single_agent', 'two_agent', or 'multi_agent'

    Returns:
        The prompt template string
    """
    if workflow_type == 'single_agent':
        return DETECTION_PROMPT
    elif workflow_type == 'two_agent':
        return TWO_AGENT_ANALYZER_PROMPT  # You'll need to handle both prompts
    elif workflow_type == 'multi_agent':
        return MULTI_AGENT_COORDINATOR_PROMPT
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")

def format_prompt(template: str, input_code: str, **kwargs) -> str:
    """
    Format a prompt template with the provided variables.

    Args:
        template: Prompt template string
        input_code: The code to analyze
        **kwargs: Additional variables (e.g., top_n)

    Returns:
        Formatted prompt string
    """
    # Import TOP_N from config if not provided
    if 'top_n' not in kwargs:
        from benchmark_config import TOP_N
        kwargs['top_n'] = TOP_N

    # Generate output format example and final example based on top_n
    top_n = kwargs['top_n']

    if top_n == 1:
        output_format_example = '''{
  "violations": [
    {"violation_type": "SRP", "explanation": "Clear explanation"}
  ]
}'''
        example = '{"violations": [{"violation_type": "SRP", "explanation": "Class handles both UI and database"}]}'
    elif top_n == 2:
        output_format_example = '''{
  "violations": [
    {"violation_type": "SRP", "explanation": "Clear explanation"},
    {"violation_type": "OCP", "explanation": "Clear explanation"}
  ]
}'''
        example = '{"violations": [{"violation_type": "SRP", "explanation": "Class handles both UI and database"}, {"violation_type": "DIP", "explanation": "Direct dependency on concrete class"}]}'
    else:
        # For top_n >= 3, show first 3 examples
        output_format_example = '''{
  "violations": [
    {"violation_type": "SRP", "explanation": "Clear explanation"},
    {"violation_type": "OCP", "explanation": "Clear explanation"},
    {"violation_type": "LSP", "explanation": "Clear explanation"}
  ]
}'''
        example = '{"violations": [{"violation_type": "SRP", "explanation": "Class handles both UI and database"}, {"violation_type": "DIP", "explanation": "Direct dependency on concrete class"}, {"violation_type": "OCP", "explanation": "Uses if-else instead of polymorphism"}]}'

    # Add shared detector prompt base with examples
    kwargs['detector_prompt_base'] = DETECTOR_PROMPT_BASE.format(
        top_n=top_n,
        output_format_example=output_format_example,
        example=example
    )

    return template.format(input_code=input_code, **kwargs)

