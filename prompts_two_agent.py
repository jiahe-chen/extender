"""
Two-Agent SOLID Detection Prompts
==================================

This file contains prompts for the two-agent workflow using Google ADK:
- Detector Agent: Identifies SOLID violations in code
- Evaluator Agent: Reviews detector's findings and provides feedback

Using LoopAgent for feedback mechanism between detector and evaluator.
"""

# Import shared components from prompts.py
from prompts import DETECTOR_PROMPT_BASE

# ============================================================================
# DETECTOR AGENT INSTRUCTION
# ============================================================================

DETECTOR_INSTRUCTION = """{detector_prompt_base}"""

# ============================================================================
# EVALUATOR AGENT INSTRUCTION
# ============================================================================

# Import SOLID principles definition for evaluator
SOLID_PRINCIPLES_FOR_EVALUATOR = """## SOLID Principles:
- **SRP**: A class does too many unrelated tasks.
- **OCP**: Multiple `if-else` or `switch` blocks for logic that should be handled by polymorphism.
- **LSP**: Subclasses override behavior in a way that breaks the contract of the base class (e.g., throw exceptions).
- **ISP**: Interfaces that are too large or force implementing unnecessary methods.
- **DIP**: High-level classes directly depend on low-level classes instead of abstractions."""

EVALUATOR_INSTRUCTION = """You are an expert evaluator for SOLID principle analysis.

Your role:
1. Review the detector's top {{top_n}} violation rankings critically
2. Check if the violations are correctly identified and properly ranked by obviousness
3. Verify the explanations are accurate
4. Provide feedback if the analysis needs improvement

{solid_principles}

## Output Format:
Respond with ONLY a valid JSON object. Do NOT wrap it in markdown code blocks (no ```json or ```). Output raw JSON only:

{{
  "agrees": true or false,
  "feedback": "Specific pure-text feedback if you disagree, otherwise null"
}}

Rules:
- Output ONLY raw JSON, no markdown formatting, no code blocks, no additional text
- agrees=true: Accept the detector's ranking (loop terminates)
- agrees=false: Provide actionable feedback about ranking or identification issues (loop continues)
- Focus on whether violations are ranked by obviousness (most obvious first)
- Be critical but constructive
"""

# ============================================================================
# PROMPT TEMPLATES FOR AGENTS
# ============================================================================

DETECTOR_PROMPT_TEMPLATE = """Analyze this code for SOLID principle violations:

```
{input_code}
```

{feedback_section}

Provide your analysis in JSON format as specified in your instructions."""


EVALUATOR_PROMPT_TEMPLATE = """Review this SOLID violation detection:

## Original Code:
```
{input_code}
```

## Detector's Analysis:
{detector_output}

Evaluate the accuracy and provide your assessment in JSON format as specified in your instructions."""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_detector_prompt(input_code: str, feedback: str = None) -> str:
    """Format the detector prompt with optional feedback"""
    # Import TOP_N from config
    from benchmark_config import TOP_N

    if feedback:
        feedback_section = f"""
## Evaluator Feedback:
The evaluator disagreed with your previous analysis. Please reconsider:
{feedback}
"""
    else:
        feedback_section = ""

    # Generate output format example and final example based on top_n
    if TOP_N == 1:
        output_format_example = '''{
  "violations": [
    {"violation_type": "SRP", "explanation": "Clear explanation"}
  ]
}'''
        example = '{"violations": [{"violation_type": "SRP", "explanation": "Class handles both UI and database"}]}'
    elif TOP_N == 2:
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

    # Format DETECTOR_INSTRUCTION with shared components
    formatted_instruction = DETECTOR_INSTRUCTION.format(
        detector_prompt_base=DETECTOR_PROMPT_BASE.format(
            top_n=TOP_N,
            output_format_example=output_format_example,
            example=example
        )
    )

    # Combine instruction with prompt template
    full_prompt = formatted_instruction + "\n\n" + DETECTOR_PROMPT_TEMPLATE.format(
        input_code=input_code,
        feedback_section=feedback_section
    )
    return full_prompt

def format_evaluator_prompt(input_code: str, detector_output: str) -> str:
    """Format the evaluator prompt"""
    # Import TOP_N from config
    from benchmark_config import TOP_N

    # Format EVALUATOR_INSTRUCTION with SOLID principles
    formatted_instruction = EVALUATOR_INSTRUCTION.format(
        solid_principles=SOLID_PRINCIPLES_FOR_EVALUATOR,
        top_n=TOP_N
    )

    # Combine instruction with prompt template
    full_prompt = formatted_instruction + "\n\n" + EVALUATOR_PROMPT_TEMPLATE.format(
        input_code=input_code,
        detector_output=detector_output
    )
    return full_prompt
