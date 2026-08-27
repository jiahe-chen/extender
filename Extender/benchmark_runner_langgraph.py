#!/usr/bin/env python3
"""
Universal SOLID Detection Benchmark Runner (LangGraph Edition)
=============================================================

A clean, well-structured script for running SOLID violation detection benchmarks
using LangGraph for agentic workflows with LangChain ChatOllama integration.

Features:
- LangGraph-based agent workflows (single_agent, two_agent, multi_agent)
- LangChain ChatOllama integration for seamless Ollama support
- Feedback loops and state management through LangGraph
- Configurable model selection (any Ollama model)
- Selectable SOLID violations (SRP, OCP, LSP, ISP, DIP)
- Smart skip/retry mechanism
- Progress tracking and resumable execution
- Centralized prompt management

Usage:
    1. Edit benchmark_config.py to configure your benchmark
    2. Run: python benchmark_runner_langgraph.py

The script will:
- Skip successfully processed examples
- Retry previously failed examples
- Process new examples
- Save results incrementally
"""
  
import json
import os
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, TypedDict, Literal
from abc import ABC, abstractmethod

# Load .env file if it exists (before importing config)
_env_file = Path(__file__).parent / '.env'
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END, START
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage

# Import configuration module and specific values
import benchmark_config
from benchmark_config import (
    MODEL_SELECTION,
    VIOLATION_SELECTION,
    WORKFLOW_TYPE,
    MAX_EXAMPLES_PER_VIOLATION,
    TEMPERATURE,
    MAX_TOKENS,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    REQUEST_DELAY_SECONDS,
    OLLAMA_BASE_URL,
    OUTPUT_DIR_BASE,
    OUTPUT_FILENAME,
    SKIP_SUCCESSFUL,
    RETRY_FAILED,
    PROCESS_NEW,
    DATASET_DIR,
    TOP_N,  # V8: New config for top-n detection
    CLOUD_MODELS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    validate_config,
    print_config_summary
)

from prompts import get_detection_prompt, format_prompt
from prompts_diff_eval import (
    format_scenario_generation_prompt,
    format_code_modification_prompt,
)

# ============================================================================
# STATE DEFINITIONS FOR LANGGRAPH
# ============================================================================

class SingleAgentState(TypedDict):
    """State for single agent workflow"""
    code: str
    prompt: str
    response: str
    error: Optional[str]

class TwoAgentState(TypedDict):
    """State for two agent workflow with feedback loop"""
    code: str
    detector_output: str
    evaluator_output: str
    evaluator_feedback: Optional[str]
    agrees: bool
    iteration: int
    max_iterations: int
    final_output: str
    error: Optional[str]

class MultiAgentState(TypedDict):
    """State for multi-agent workflow (future)"""
    code: str
    violation_type: str
    specialist_outputs: Dict[str, str]
    coordinator_output: str
    final_result: str
    error: Optional[str]

class DiffEvalState(TypedDict):
    """State for diff-based evaluation workflow (V6 - with pre-verification)"""
    code: str
    language: str  # Programming language (from dataset metadata)

    # Temporary fields for passing data between nodes in iteration
    modified_code: str  # Temporary: modified code from modify_node to diff_node

    # Collected data from all 5 SOLID principle iterations
    all_scenarios: List[Dict[str, Any]]  # List of {type, scenario} for each principle
    all_diffs: List[Dict[str, Any]]  # List of {type, diff_text, modified_code} for each principle
    all_pre_verifications: List[Dict[str, Any]]  # V6: List of pre-verification results for each principle

    # Final unified verification result
    detection_result: Dict[str, Any]  # Single detection result: {violation_type, explanation, all_checks}
    final_result: str  # Final aggregated result
    error: Optional[str]

# ============================================================================
# WORKFLOW FRAMEWORK (LangGraph-Based)
# ============================================================================

class WorkflowBase(ABC):
    """
    Abstract base class for all workflows.
    Extend this to create new workflow types using LangGraph.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.llm = self._create_llm()


    def _create_llm(self):
        """Create LLM instance (Ollama for local, OpenRouter for cloud)"""
        if self.model_name in CLOUD_MODELS:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=CLOUD_MODELS[self.model_name],
                base_url=OPENROUTER_BASE_URL,
                api_key=OPENROUTER_API_KEY,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS if MAX_TOKENS > 0 else None,
                timeout=120,
            )
        else:
            return ChatOllama(
                model=self.model_name,
                base_url=OLLAMA_BASE_URL,
                temperature=TEMPERATURE,
                num_predict=MAX_TOKENS,
                timeout=120,
                reasoning=False,
            )

    @abstractmethod
    def process_example(self, example: Dict, example_id: str, violation_type: str) -> Optional[str]:
        """Process a single example and return model response"""
        pass

    @abstractmethod
    def get_workflow_name(self) -> str:
        """Return the workflow name for identification"""
        pass


class SingleAgentWorkflow(WorkflowBase):
    """Single agent workflow implementation using LangGraph"""

    def process_example(self, example: Dict, example_id: str, violation_type: str) -> Optional[str]:
        """Process example using single agent with LangGraph"""
        # Setup logging
        log_base_dir = setup_log_directory(self.model_name)
        violation_log_dir = log_base_dir / violation_type.lower()
        violation_log_dir.mkdir(exist_ok=True, parents=True)
        log_file = violation_log_dir / f"{example_id}.log"
        logger = SingleAgentLogger(str(log_file))

        try:
            input_code = example.get('input', '')

            # Log header
            logger.log_header(input_code, example_id, "single_agent")

            # Get and format prompt
            prompt_template = get_detection_prompt(WORKFLOW_TYPE)
            prompt = format_prompt(prompt_template, input_code=input_code)

            # Log prompt
            logger.log_prompt(prompt)

            # Create simple workflow
            def analyze_code(state: SingleAgentState) -> SingleAgentState:
                try:
                    message = HumanMessage(content=state["prompt"])
                    response = self.llm.invoke([message])
                    return {**state, "response": response.content, "error": None}
                except Exception as e:
                    return {**state, "response": "", "error": str(e)}

            # Build graph
            workflow = StateGraph(SingleAgentState)
            workflow.add_node("analyze", analyze_code)
            workflow.add_edge(START, "analyze")
            workflow.add_edge("analyze", END)

            app = workflow.compile()

            # Execute
            result = app.invoke({
                "code": input_code,
                "prompt": prompt,
                "response": "",
                "error": None
            })

            if result["error"]:
                error_msg = f"Single agent error: {result['error']}"
                print(f"    [ERROR] {error_msg}")
                logger.log_error(error_msg)
                return None

            response = result["response"]

            # Log response
            logger.log_response(response)

            # Parse response for logging
            from benchmark_runner_langgraph import parse_model_response
            parsed = parse_model_response(response)
            logger.log_parsing(parsed)

            # Log evaluation
            from benchmark_runner_langgraph import evaluate_detection
            detection_success = evaluate_detection(violation_type, parsed.get('detected_violation_type'))
            logger.log_evaluation(detection_success, violation_type, parsed.get('detected_violation_type', 'None'))

            # Log summary
            logger.log_summary({
                'detection_success': detection_success,
                'detected_violation_type': parsed.get('detected_violation_type', 'None')
            })

            print(f"    [DEBUG] Detailed log: {log_file}")

            return response

        except Exception as e:
            error_msg = f"Single agent workflow error: {e}"
            print(f"    [ERROR] {error_msg}")
            logger.log_error(error_msg)
            return None

    def get_workflow_name(self) -> str:
        return "single_agent"


class TwoAgentWorkflow(WorkflowBase):
    """
    Two agent workflow - Detector + Evaluator with feedback loop using LangGraph

    Architecture:
    1. Detector analyzes code and identifies violations
    2. Evaluator reviews detector's output
    3. If evaluator disagrees, provides feedback
    4. Detector re-analyzes with feedback (loop continues)
    5. Loop terminates when evaluator agrees or max iterations reached
    """

    def __init__(self, model_name: str, max_iterations: int = 3):
        super().__init__(model_name)
        self.max_iterations = max_iterations

    def process_example(self, example: Dict, example_id: str, violation_type: str) -> Optional[str]:
        """Process example using two-agent workflow with LangGraph feedback loop"""
        # Setup logging
        log_base_dir = setup_log_directory(self.model_name)
        violation_log_dir = log_base_dir / violation_type.lower()
        violation_log_dir.mkdir(exist_ok=True, parents=True)
        log_file = violation_log_dir / f"{example_id}.log"
        logger = TwoAgentLogger(str(log_file))

        try:
            print(f"    [DEBUG] Starting two-agent workflow for {example_id}")
            from prompts_two_agent import (
                format_detector_prompt,
                format_evaluator_prompt
            )
            print(f"    [DEBUG] Prompts imported")

            input_code = example.get('input', '')
            print(f"    [DEBUG] Got input code, length: {len(input_code)}")

            # Log header
            logger.log_header(input_code, example_id, "two_agent")

            # Define nodes
            def detector_node(state: TwoAgentState) -> TwoAgentState:
                print(f"        [Detector] Iteration {state['iteration']}")
                try:
                    prompt = format_detector_prompt(state["code"], state.get("evaluator_feedback"))
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    print(f"        [Detector] Got response")

                    # Log detector iteration
                    logger.log_detector_iteration(state['iteration'] + 1, response.content)

                    return {**state, "detector_output": response.content}
                except Exception as e:
                    print(f"        [Detector] ERROR: {e}")
                    logger.log_error(f"Detector error: {e}")
                    return {**state, "error": f"Detector error: {e}"}

            def evaluator_node(state: TwoAgentState) -> TwoAgentState:
                print(f"        [Evaluator] Iteration {state['iteration']}")
                try:
                    prompt = format_evaluator_prompt(state["code"], state["detector_output"])
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    print(f"        [Evaluator] Got response")

                    # Parse evaluator response
                    try:
                        eval_json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                        if eval_json_match:
                            eval_data = json.loads(eval_json_match.group(0))
                            agrees = eval_data.get('agrees', False)
                            feedback = eval_data.get('feedback', 'Please reconsider your analysis.')

                            # Log evaluator feedback
                            logger.log_evaluator_feedback(agrees, feedback)

                            return {
                                **state,
                                "evaluator_output": response.content,
                                "agrees": agrees,
                                "evaluator_feedback": feedback,
                                "iteration": state["iteration"] + 1
                            }
                    except Exception as parse_error:
                        # If parsing fails, assume evaluator agrees
                        logger.log_evaluator_feedback(True, "Parse error - assuming agreement")
                        return {
                            **state,
                            "evaluator_output": response.content,
                            "agrees": True,
                            "iteration": state["iteration"] + 1
                        }

                    # Fallback
                    logger.log_evaluator_feedback(True, "Fallback - assuming agreement")
                    return {
                        **state,
                        "evaluator_output": response.content,
                        "agrees": True,
                        "iteration": state["iteration"] + 1
                    }

                except Exception as e:
                    print(f"        [Evaluator] ERROR: {e}")
                    logger.log_error(f"Evaluator error: {e}")
                    return {**state, "error": f"Evaluator error: {e}"}

            # Finalize node to normalize output
            def finalize_node(state: TwoAgentState) -> TwoAgentState:
                print(f"        [Finalize] Preparing final output")
                final_response = normalize_detector_output(state.get("detector_output"))

                # Log consensus
                logger.log_consensus(final_response)

                return {**state, "final_output": final_response}

            # Conditional routing
            def should_continue(state: TwoAgentState) -> Literal["detector", "finalize"]:
                if state["agrees"] or state["iteration"] >= state["max_iterations"]:
                    print(f"        [Router] -> finalize")
                    return "finalize"
                print(f"        [Router] -> detector")
                return "detector"

            # Build graph
            print(f"    [DEBUG] Building graph")
            workflow = StateGraph(TwoAgentState)
            workflow.add_node("detector", detector_node)
            workflow.add_node("evaluator", evaluator_node)
            workflow.add_node("finalize", finalize_node)

            workflow.add_edge(START, "detector")
            workflow.add_edge("detector", "evaluator")
            workflow.add_conditional_edges(
                "evaluator",
                should_continue,
                {"detector": "detector", "finalize": "finalize"}
            )
            workflow.add_edge("finalize", END)

            print(f"    [DEBUG] Compiling graph")
            app = workflow.compile()
            print(f"    [DEBUG] Graph compiled, executing")

            # Execute
            result = app.invoke({
                "code": input_code,
                "detector_output": "",
                "evaluator_output": "",
                "evaluator_feedback": None,
                "agrees": False,
                "iteration": 0,
                "max_iterations": self.max_iterations,
                "final_output": "",
                "error": None
            })

            print(f"    [DEBUG] Execution complete")

            if result["error"]:
                error_msg = f"Two-agent error: {result['error']}"
                print(f"    [ERROR] {error_msg}")
                logger.log_error(error_msg)
                return None

            final_output = result.get("final_output") or result.get("detector_output")

            # Log summary
            from benchmark_runner_langgraph import parse_model_response, evaluate_detection
            parsed = parse_model_response(final_output)
            detection_success = evaluate_detection(violation_type, parsed.get('detected_violation_type'))
            logger.log_summary({
                'detection_success': detection_success,
                'detected_violation_type': parsed.get('detected_violation_type', 'None')
            })

            print(f"    [DEBUG] Detailed log: {log_file}")

            return final_output

        except Exception as e:
            error_msg = f"Two-agent workflow error: {e}"
            print(f"    [ERROR] {error_msg}")
            logger.log_error(error_msg)
            import traceback
            traceback.print_exc()
            return None

    def get_workflow_name(self) -> str:
        return "two_agent"


class MultiAgentWorkflow(WorkflowBase):
    """
    Multi-agent workflow - Specialized agents for each SOLID principle
    Uses LangGraph for coordination and routing
    """

    def process_example(self, example: Dict, example_id: str, violation_type: str) -> Optional[str]:
        """Process example using multi-agent coordination"""
        try:
            input_code = example.get('input', '')

            # Define specialist nodes for each SOLID principle
            def srp_specialist(state: MultiAgentState) -> MultiAgentState:
                """Single Responsibility Principle specialist"""
                prompt = f"""You are a specialist in Single Responsibility Principle (SRP) violations.

Analyze this code for SRP violations only:

```
{state["code"]}
```

Respond with JSON:
{{"is_detected": true/false, "violation_type": "SRP" or null, "explanation": "reason"}}"""

                try:
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    outputs = state.get("specialist_outputs", {})
                    outputs["SRP"] = response.content
                    return {**state, "specialist_outputs": outputs}
                except Exception as e:
                    return {**state, "error": f"SRP specialist error: {e}"}

            def ocp_specialist(state: MultiAgentState) -> MultiAgentState:
                """Open/Closed Principle specialist"""
                prompt = f"""You are a specialist in Open/Closed Principle (OCP) violations.

Analyze this code for OCP violations only:

```
{state["code"]}
```

Respond with JSON:
{{"is_detected": true/false, "violation_type": "OCP" or null, "explanation": "reason"}}"""

                try:
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    outputs = state.get("specialist_outputs", {})
                    outputs["OCP"] = response.content
                    return {**state, "specialist_outputs": outputs}
                except Exception as e:
                    return {**state, "error": f"OCP specialist error: {e}"}

            def coordinator(state: MultiAgentState) -> MultiAgentState:
                """Coordinator that synthesizes specialist outputs"""
                specialists = state.get("specialist_outputs", {})

                prompt = f"""You are a coordinator for SOLID principle analysis.

Based on specialist analysis, provide final verdict for {state["violation_type"]} violations:

Specialist Results:
{json.dumps(specialists, indent=2)}

Expected violation type: {state["violation_type"]}

Provide final JSON response:
{{"is_detected": true/false, "violation_type": "{state["violation_type"]}" or null, "explanation": "synthesized analysis"}}"""

                try:
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    return {**state, "coordinator_output": response.content, "final_result": response.content}
                except Exception as e:
                    return {**state, "error": f"Coordinator error: {e}"}

            # Build graph based on violation type
            workflow = StateGraph(MultiAgentState)

            # Add coordinator
            workflow.add_node("coordinator", coordinator)

            # Add specialists based on violation type
            if violation_type == "SRP":
                workflow.add_node("srp_specialist", srp_specialist)
                workflow.add_edge(START, "srp_specialist")
                workflow.add_edge("srp_specialist", "coordinator")
            elif violation_type == "OCP":
                workflow.add_node("ocp_specialist", ocp_specialist)
                workflow.add_edge(START, "ocp_specialist")
                workflow.add_edge("ocp_specialist", "coordinator")
            else:
                # For other violations, use both specialists (example)
                workflow.add_node("srp_specialist", srp_specialist)
                workflow.add_node("ocp_specialist", ocp_specialist)
                workflow.add_edge(START, "srp_specialist")
                workflow.add_edge(START, "ocp_specialist")
                workflow.add_edge("srp_specialist", "coordinator")
                workflow.add_edge("ocp_specialist", "coordinator")

            workflow.add_edge("coordinator", END)

            app = workflow.compile()

            # Execute
            result = app.invoke({
                "code": input_code,
                "violation_type": violation_type,
                "specialist_outputs": {},
                "coordinator_output": "",
                "final_result": "",
                "error": None
            })

            if result["error"]:
                print(f"    [ERROR] Multi-agent error: {result['error']}")
                return None

            return result["final_result"]

        except Exception as e:
            print(f"    [ERROR] Multi-agent workflow error: {e}")
            return None

    def get_workflow_name(self) -> str:
        return "multi_agent"


# ============================================================================
# LOGGING INFRASTRUCTURE
# ============================================================================

class WorkflowLogger:
    """Base logger class for all workflow types"""

    def __init__(self, log_file: str):
        """
        Initialize logger with log file path.

        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        # Ensure parent directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Write message to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    def log_header(self, code: str, example_id: str, workflow_type: str):
        """Log workflow header"""
        import datetime
        self.log("\n" + "="*80)
        self.log(f"{workflow_type.upper().replace('_', ' ')} WORKFLOW - SOLID VIOLATION DETECTION")
        self.log("="*80)
        self.log(f"Timestamp: {datetime.datetime.now().isoformat()}")
        self.log(f"Example ID: {example_id}")
        self.log(f"Code length: {len(code)} characters")
        self.log("="*80)
        self.log("\nORIGINAL CODE:")
        self.log("-"*80)
        self.log(code)
        self.log("-"*80)
        self.log("")

    def log_error(self, error: str):
        """Log error message"""
        self.log(f"\n[ERROR] {error}")

    def log_summary(self, result: Dict):
        """Log final summary - to be overridden by subclasses"""
        self.log("\n" + "="*80)
        self.log("FINAL SUMMARY")
        self.log("="*80)
        self.log(f"Detection Success: {result.get('detection_success', False)}")
        self.log(f"Detected Violation: {result.get('detected_violation_type', 'None')}")
        self.log("="*80)


class SingleAgentLogger(WorkflowLogger):
    """Logger for single agent workflow"""

    def log_prompt(self, prompt: str):
        """Log the prompt sent to model"""
        self.log("\n[Stage 1/3] Prompt Generation")
        self.log(f"    Prompt length: {len(prompt)} characters")
        self.log("\n    PROMPT:")
        self.log("    " + "-"*76)
        # Log first 500 chars of prompt
        prompt_preview = prompt[:500]
        for line in prompt_preview.split('\n'):
            self.log(f"    {line}")
        if len(prompt) > 500:
            self.log(f"    ... ({len(prompt) - 500} more characters)")
        self.log("    " + "-"*76)

    def log_response(self, response: str):
        """Log model response"""
        self.log("\n[Stage 2/3] Model Response")
        self.log(f"    Response length: {len(response)} characters")
        self.log("\n    RESPONSE:")
        self.log("    " + "-"*76)
        for line in response.split('\n'):
            self.log(f"    {line}")
        self.log("    " + "-"*76)

    def log_parsing(self, parsed_data: Dict):
        """Log parsed detection results"""
        self.log("\n[Stage 3/3] Response Parsing")
        self.log(f"    Detected Violation: {parsed_data.get('detected_violation_type', 'None')}")
        self.log(f"    Parse Error: {parsed_data.get('parse_error', 'None')}")
        if parsed_data.get('explanation'):
            self.log(f"    Explanation: {parsed_data['explanation'][:200]}...")

    def log_evaluation(self, success: bool, expected: str, detected: str):
        """Log evaluation results"""
        self.log("\n[Evaluation]")
        self.log(f"    Expected: {expected}")
        self.log(f"    Detected: {detected}")
        self.log(f"    Success: {success}")


class TwoAgentLogger(WorkflowLogger):
    """Logger for two agent workflow"""

    def __init__(self, log_file: str):
        super().__init__(log_file)
        self.iteration_count = 0

    def log_detector_iteration(self, iteration: int, output: str):
        """Log detector output"""
        self.iteration_count = iteration
        self.log(f"\n[Iteration {iteration}] Detector Analysis")
        self.log("    " + "-"*76)
        self.log(f"    Output length: {len(output)} characters")
        self.log("\n    DETECTOR OUTPUT:")
        # Log first 300 chars
        output_preview = output[:300]
        for line in output_preview.split('\n'):
            self.log(f"    {line}")
        if len(output) > 300:
            self.log(f"    ... ({len(output) - 300} more characters)")
        self.log("    " + "-"*76)

    def log_evaluator_feedback(self, agrees: bool, feedback: str):
        """Log evaluator response"""
        self.log(f"\n[Iteration {self.iteration_count}] Evaluator Review")
        self.log("    " + "-"*76)
        self.log(f"    Agrees: {agrees}")
        if not agrees:
            self.log(f"    Feedback: {feedback}")
        self.log("    " + "-"*76)

    def log_consensus(self, final_output: str):
        """Log final consensus"""
        self.log("\n[Final Consensus]")
        self.log("    " + "-"*76)
        self.log(f"    Total iterations: {self.iteration_count}")
        self.log(f"    Final output length: {len(final_output)} characters")
        self.log("\n    FINAL OUTPUT:")
        for line in final_output.split('\n'):
            self.log(f"    {line}")
        self.log("    " + "-"*76)


# ============================================================================
# DIFF-BASED EVALUATION HELPER FUNCTIONS
# ============================================================================

class DiffEvalLogger(WorkflowLogger):
    """Logger for detailed diff-eval workflow output"""

    def __init__(self, log_file: str):
        super().__init__(log_file)
        self.iteration_count = 0

    def log_header(self, code: str, example_id: str):
        """Log workflow header for diff-eval"""
        import datetime
        self.log("\n" + "="*80)
        self.log("DIFF-BASED SOLID VIOLATION DETECTION")
        self.log("="*80)
        self.log(f"Timestamp: {datetime.datetime.now().isoformat()}")
        self.log(f"Example ID: {example_id}")
        self.log(f"Code length: {len(code)} characters")
        self.log(f"Testing principles: SRP, OCP, LSP, ISP, DIP")
        self.log("="*80)
        self.log("\nORIGINAL CODE:")
        self.log("-"*80)
        self.log(code)
        self.log("-"*80)
        self.log("")

    def log_iteration_start(self, principle: str, iteration: int, total: int):
        """Log start of iteration"""
        self.iteration_count = iteration
        self.log("\n" + "="*80)
        self.log(f"ITERATION {iteration}/{total}: TESTING {principle}")
        self.log("="*80)

    def log_scenario(self, scenario: Dict[str, Any]):
        """Log scenario generation"""
        self.log("\n[Stage 1/6] Scenario Generation")
        self.log(f"    Principle: {scenario.get('focus', 'N/A')}")
        self.log(f"    Scenario: {scenario.get('prompt', 'N/A')[:100]}...")
        self.log(f"    Constraints: {scenario.get('constraints', [])}")

    def log_modification(self, original_code: str, modified_code: str, diff_text: str):
        """Log code modification details"""
        self.log("\n[Stage 2/6] Code Modification")
        self.log(f"    Original length: {len(original_code)} characters")
        self.log(f"    Modified length: {len(modified_code)} characters")
        self.log(f"    Diff size: {len(diff_text)} characters")
        self.log("\n    MODIFIED CODE:")
        self.log("    " + "-"*76)
        for line in modified_code.split('\n'):
            self.log(f"    {line}")
        self.log("    " + "-"*76)

    def log_diff(self, diff_text: str):
        """Log diff analysis"""
        self.log("\n[Stage 3/6] Diff Analysis")

        # Count diff stats
        lines = diff_text.split('\n')
        added = sum(1 for l in lines if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in lines if l.startswith('-') and not l.startswith('---'))

        self.log(f"    Lines added: {added}")
        self.log(f"    Lines removed: {removed}")
        self.log(f"    Total changes: {added + removed}")
        self.log("\n    DIFF:")
        self.log("    " + "-"*76)
        diff_lines = diff_text.split('\n')
        for line in diff_lines[:50]:  # First 50 lines
            self.log(f"    {line}")
        if len(diff_lines) > 50:
            remaining = len(diff_lines) - 50
            self.log(f"    ... ({remaining} more lines)")
        self.log("    " + "-"*76)

    def log_verification(self, principle: str, result: Dict[str, Any]):
        """Log verification result (V3 - no confidence/severity)"""
        self.log("\n[Stage 4/6] LLM Verification")
        self.log(f"    Testing for: {principle}")
        self.log(f"    Is detected: {result.get('is_detected', False)}")
        self.log(f"    Signal: {result.get('signal', 'N/A')}")
        self.log(f"    Explanation: {result.get('explanation', 'N/A')[:200]}...")

    def log_summary(self, all_results: List[Dict[str, Any]], final_result: Dict[str, Any]):
        """Log final summary (V5 - unified verification)"""
        self.log("\n" + "="*80)
        self.log("FINAL SUMMARY (V5 - Unified LLM Verification)")
        self.log("="*80)
        self.log(f"\nTotal principles tested: {len(all_results)}")
        self.log(f"Violations detected: {sum(1 for r in all_results if r.get('is_detected', False))}")
        self.log("\nAll Checks:")
        for r in all_results:
            status = "✓ DETECTED" if r.get('is_detected') else "✗ NOT DETECTED"
            self.log(f"  {r.get('violation_type', 'N/A'):3s}: {status}")

        self.log(f"\nFinal Decision (LLM selects most obvious violation):")
        self.log(f"  Violation detected: {final_result.get('is_detected', False)}")
        self.log(f"  Violation type: {final_result.get('violation_type', 'None')}")
        self.log(f"  Signal: {final_result.get('signal', 'N/A')}")
        self.log(f"  Explanation: {final_result.get('explanation', 'N/A')}")
        self.log("\n" + "="*80)


def mock_modify_code_for_diff(code: str, scenario: Dict) -> str:
    """Mock modification when LLM fails (fallback)"""
    lines = code.split('\n')

    # Simulate adding some code
    modification = f"""
// === MODIFICATION FOR: {scenario['focus']} ===
// Scenario: {scenario['prompt'][:50]}...
// This is a mock modification demonstrating the diff-based approach
"""

    # Insert after first class ends
    for i, line in enumerate(lines):
        if line.strip() == '}' and i > 5:
            lines.insert(i, modification)
            break

    return '\n'.join(lines)


def analyze_diff_simple(original: str, modified: str) -> str:
    """
    Analyze diff between original and modified code.
    Returns unified diff text.

    Note: This is a simplified version. Full metrics calculation
    will be added in future iterations.
    """
    import difflib

    original_lines = original.split('\n')
    modified_lines = modified.split('\n')

    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile='original',
        tofile='modified',
        lineterm=''
    ))

    diff_text = '\n'.join(diff)

    # TODO: Add DiffMetrics calculation here
    # - lines_added, lines_removed, lines_modified
    # - modification_ratio
    # - classes_changed

    return diff_text


# ============================================================================
# DIFF-BASED EVALUATION WORKFLOW
# ============================================================================

class DiffEvalWorkflow(WorkflowBase):
    """
    Diff-based evaluation workflow using LangGraph.

    Core idea: Code quality is measured by "modification difficulty".
    Good design allows adding new code without modifying existing code.

    Pipeline:
    1. Generate modification scenario
    2. (Optional) Structural analysis for prerequisite checking
    3. LLM modifies code according to scenario
    4. Analyze diff between original and modified
    5. Infer violations from diff patterns
    6. Return normalized JSON response
    """

    def __init__(self, model_name: str):
        super().__init__(model_name)

    def _parse_pre_verification_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM pre-verification response into structured format (V6).

        Expected format:
        {
          "violation_type": "SRP|OCP|LSP|ISP|DIP",
          "is_detected": true/false,
          "detailed_explanation": "..."
        }
        """
        try:
            # Remove markdown code blocks
            cleaned = response_text.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'^```\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

            # Find JSON object
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")

            json_text = json_match.group(0)
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)

            # Parse JSON
            result = json.loads(json_text)

            # Validate and normalize fields
            normalized = {
                "violation_type": result.get("violation_type", ""),
                "is_detected": bool(result.get("is_detected", False)),
                "detailed_explanation": result.get("detailed_explanation", "")
            }

            return normalized

        except Exception as e:
            print(f"        [Parse] ERROR parsing pre-verification response: {e}")
            # Return fallback structure
            return {
                "violation_type": "",
                "is_detected": False,
                "detailed_explanation": f"Failed to parse LLM response: {str(e)}"
            }

    def _parse_unified_verification_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM unified verification response into structured format (V8 - top-n support).

        Expected format (V8 - top-n):
        {
          "violations": [
            {"violation_type": "SRP", "explanation": "..."},
            {"violation_type": "OCP", "explanation": "..."}
          ],
          "all_checks": [...]
        }

        Legacy format (V6 - single violation):
        {
          "is_detected": true/false,
          "violation_type": "SRP|OCP|LSP|ISP|DIP|null",
          "explanation": "...",
          "all_checks": [...]
        }
        """
        try:
            # Remove markdown code blocks
            cleaned = response_text.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'^```\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

            # Find JSON object
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")

            json_text = json_match.group(0)
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*\]', ']', json_text)

            # Parse JSON
            result = json.loads(json_text)

            # Check for new format (violations array)
            if 'violations' in result and isinstance(result['violations'], list):
                violations = result['violations']

                # Extract violation types (excluding NONE)
                detected_types = []
                explanations = []

                for v in violations:
                    if isinstance(v, dict):
                        vtype = v.get('violation_type', '').strip().upper()
                        if vtype and vtype != 'NONE':
                            detected_types.append(vtype)
                            if 'explanation' in v:
                                explanations.append(f"{vtype}: {v['explanation']}")

                # Build normalized result
                normalized = {
                    "is_detected": len(detected_types) > 0,
                    "violation_type": ', '.join(detected_types) if detected_types else None,
                    "explanation": ' | '.join(explanations) if explanations else "No violations detected",
                    "all_checks": result.get("all_checks", []),
                    "violations": violations  # V8: Keep violations array for reference
                }

                return normalized

            # Legacy format (V6 - single violation)
            normalized = {
                "is_detected": bool(result.get("is_detected", False)),
                "violation_type": result.get("violation_type"),
                "explanation": result.get("explanation", ""),
                "all_checks": result.get("all_checks", [])
            }

            return normalized

        except Exception as e:
            print(f"        [Parse] ERROR parsing unified verification response: {e}")
            # Return fallback structure
            return {
                "is_detected": False,
                "violation_type": None,
                "explanation": f"Failed to parse LLM response: {str(e)}",
                "all_checks": []
            }

    def _parse_inference_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM verification response into structured format.

        Expected format (V3 - simplified):
        {
          "is_detected": true/false,
          "signal": "description",
          "explanation": "explanation"
        }
        """
        try:
            # Remove markdown code blocks
            cleaned = response_text.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'^```\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

            # Find JSON object
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")

            json_text = json_match.group(0)
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)

            # Parse JSON
            result = json.loads(json_text)

            # Validate and normalize fields (V3 - no confidence/severity)
            normalized = {
                "is_detected": bool(result.get("is_detected", False)),
                "violation_type": result.get("violation_type"),  # Added: extract violation_type
                "signal": result.get("signal", ""),
                "explanation": result.get("explanation", ""),
                "all_checks": result.get("all_checks", [])  # Added: extract all_checks
            }

            return normalized

        except Exception as e:
            print(f"        [Parse] ERROR parsing verification response: {e}")
            # Return fallback structure
            return {
                "is_detected": False,
                "signal": "Parse error",
                "explanation": f"Failed to parse LLM response: {str(e)}"
            }

    def _parse_ai_scenario(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI-generated scenario response into structured format.

        Expected format:
        {
          "scenario_description": "...",
          "restriction": "..."
        }
        """
        try:
            # Remove markdown code blocks
            cleaned = response_text.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'^```\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

            # Find JSON object
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")

            json_text = json_match.group(0)
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*\]', ']', json_text)

            # Parse JSON
            result = json.loads(json_text)

            # Validate required fields
            required_fields = ["scenario_description", "restriction"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            return result

        except Exception as e:
            print(f"        [Parse] ERROR parsing AI scenario: {e}")
            raise ValueError(f"Failed to parse AI-generated scenario: {str(e)}")


    def process_example(self, example: Dict, example_id: str, violation_type: str) -> Optional[str]:
        """
        Process example using diff-based evaluation workflow with iteration.

        Note: violation_type parameter is kept for compatibility but not used.
        The workflow will test all SOLID principles and aggregate results.
        """
        import time
        import os
        import datetime
        start_time = time.time()

        # Initialize detailed logger with organized directory structure
        # Use setup_log_directory to match result structure with run_id
        log_base_dir = setup_log_directory(self.model_name)
        violation_log_dir = log_base_dir / violation_type.lower()
        violation_log_dir.mkdir(parents=True, exist_ok=True)

        log_file = violation_log_dir / f"{example_id}.log"
        logger = DiffEvalLogger(str(log_file))

        try:
            print(f"    [DEBUG] Starting diff-eval workflow for {example_id}")
            input_code = example.get('input', '')
            print(f"    [DEBUG] Got input code, length: {len(input_code)}")
            print(f"    [DEBUG] Detailed log: {log_file}")

            # Log header
            logger.log_header(input_code, example_id)

            # All SOLID principles to test
            ALL_PRINCIPLES = ["SRP", "OCP", "LSP", "ISP", "DIP"]

            # Define nodes
            def init_principles_node(state: DiffEvalState) -> DiffEvalState:
                """Initialise pre-verifications — all principles will be tested."""
                all_pre_verifications = [
                    {"violation_type": p, "is_detected": None, "detailed_explanation": f"Will proceed with {p} test."}
                    for p in ALL_PRINCIPLES
                ]
                return {**state, "all_pre_verifications": all_pre_verifications}

            def iterator_node(state: DiffEvalState) -> DiffEvalState:
                """Initialize iteration over all SOLID principles and handle skipping"""
                print(f"        [Iterator] Starting iteration over all SOLID principles")

                # Check if we should skip the current test based on structural analysis
                all_scenarios = state.get("all_scenarios", [])
                all_pre_verifications = state.get("all_pre_verifications", [])
                all_diffs = state.get("all_diffs", [])

                current_idx = len(all_scenarios)

                # If we've processed all principles, just return
                if current_idx >= len(ALL_PRINCIPLES):
                    return state

                current_type = ALL_PRINCIPLES[current_idx]

                # Check if this test should be skipped
                should_skip = False
                skip_reason = ""

                for pv in all_pre_verifications:
                    if pv.get("violation_type") == current_type and pv.get("is_detected") == False:
                        should_skip = True
                        skip_reason = pv.get("detailed_explanation", "Structural prerequisite not met")
                        break

                if should_skip:
                    print(f"        [Iterator] SKIPPING {current_type}: {skip_reason}")

                    # Add dummy entries to maintain consistency
                    dummy_scenario = {
                        "focus": current_type,
                        "prompt": f"SKIPPED: {skip_reason}",
                        "restriction": "",
                        "skipped": True
                    }
                    all_scenarios.append({"type": current_type, "scenario": dummy_scenario})

                    dummy_diff = {
                        "type": current_type,
                        "diff_text": "",
                        "modified_code": "",
                        "skipped": True
                    }
                    all_diffs.append(dummy_diff)

                    # The pre-verification already exists with is_detected=False
                    # No need to add it again

                    return {
                        **state,
                        "all_scenarios": all_scenarios,
                        "all_diffs": all_diffs
                    }

                # Not skipped - add placeholder so index advances
                print(f"        [Iterator] Processing {current_type} (not skipped)")
                placeholder_scenario = {
                    "focus": current_type,
                    "prompt": "",  # Will be filled by scenario_node
                    "restriction": "",
                    "skipped": False
                }
                all_scenarios.append({"type": current_type, "scenario": placeholder_scenario})

                return {
                    **state,
                    "all_scenarios": all_scenarios
                }

            def should_continue_iteration(state: DiffEvalState) -> str:
                """Determine if we should continue iterating or move to verification"""
                all_scenarios = state.get("all_scenarios", [])
                current_idx = len(all_scenarios)

                if current_idx < len(ALL_PRINCIPLES):
                    # Continue to next principle
                    next_principle = ALL_PRINCIPLES[current_idx]
                    print(f"        [Iterator] Moving to next principle: {next_principle} ({current_idx+1}/{len(ALL_PRINCIPLES)})")
                    return "iterator"  # Go back to iterator to check if we should skip
                else:
                    print(f"        [Iterator] All {len(ALL_PRINCIPLES)} principles collected, moving to unified verification")
                    return "verification"  # Done collecting, now verify all at once

            def scenario_node(state: DiffEvalState) -> DiffEvalState:
                """Generate modification scenario using AI for current violation type"""
                # Get the last scenario (placeholder added by iterator)
                all_scenarios = state.get("all_scenarios", [])

                if not all_scenarios:
                    print(f"        [Scenario] ERROR: No placeholder scenario found")
                    return state

                # Get current type from the last scenario placeholder
                current_type = all_scenarios[-1]["type"]
                current_idx = len(all_scenarios) - 1

                # Log iteration start
                logger.log_iteration_start(current_type, current_idx + 1, len(ALL_PRINCIPLES))

                print(f"        [Scenario] Generating AI-based scenario for {current_type}")
                try:
                    # Get language from state (from dataset metadata)
                    language = state.get("language", "python").lower()

                    # Generate scenario using AI
                    scenario_prompt = format_scenario_generation_prompt(
                        code=state["code"],
                        violation_type=current_type
                    )

                    # Call LLM to generate scenario
                    print(f"        [Scenario] Calling LLM to generate scenario...")
                    message = HumanMessage(content=scenario_prompt)
                    response = self.llm.invoke([message])
                    response_text = response.content.strip()

                    print(f"        [Scenario] Got AI response, length: {len(response_text)}")

                    # Parse AI-generated scenario
                    ai_scenario = self._parse_ai_scenario(response_text)

                    # Convert to format expected by modify_node
                    scenario = {
                        "focus": current_type,
                        "prompt": ai_scenario.get("scenario_description", ""),
                        "restriction": ai_scenario.get("restriction", ""),
                        "ai_generated": True  # Flag to indicate this is AI-generated
                    }

                    # Log scenario
                    logger.log_scenario(scenario)

                    print(f"        [Scenario] Successfully generated AI scenario")

                    # Update the placeholder scenario (last entry in all_scenarios)
                    all_scenarios[-1] = {"type": current_type, "scenario": scenario}

                    return {**state, "all_scenarios": all_scenarios}

                except Exception as e:
                    print(f"        [Scenario] AI generation failed: {e}")
                    error_msg = f"Failed to generate scenario for {current_type}: {str(e)}"
                    return {**state, "error": error_msg}


            def modify_node(state: DiffEvalState) -> DiffEvalState:
                """LLM modifies code according to scenario"""
                print(f"        [Modify] Requesting LLM to modify code")
                try:
                    # Get current scenario from all_scenarios (last one added)
                    all_scenarios = state.get("all_scenarios", [])
                    if not all_scenarios:
                        return {**state, "error": "No scenario available"}

                    scenario = all_scenarios[-1]["scenario"]  # Get the last scenario
                    current_type = all_scenarios[-1]["type"]
                    print(f"        [Modify] Modifying code for {current_type}")

                    # Check if this is an AI-generated scenario
                    if scenario.get("ai_generated", False):
                        # AI-generated scenario: use format_code_modification_prompt
                        prompt = format_code_modification_prompt(
                            code=state["code"],
                            scenario_description=scenario.get("prompt", ""),
                            restriction=scenario.get("restriction", "")
                        )
                    else:
                        # Should not reach here - all scenarios should be AI-generated
                        error_msg = f"Non-AI scenario encountered for {current_type}"
                        print(f"        [Modify] ERROR: {error_msg}")
                        return {**state, "error": error_msg}

                    # Call LLM
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    modified = response.content.strip()

                    # Clean markdown code blocks
                    modified = re.sub(r'^```\w*\n?', '', modified)
                    modified = re.sub(r'\n?```$', '', modified)
                    modified = modified.strip()

                    print(f"        [Modify] Got modified code, length: {len(modified)}")
                    return {**state, "modified_code": modified}

                except Exception as e:
                    print(f"        [Modify] ERROR: {e}, using mock modification")
                    all_scenarios = state.get("all_scenarios", [])
                    if all_scenarios:
                        scenario = all_scenarios[-1]["scenario"]
                    else:
                        scenario = {"focus": "ALL", "prompt": ""}
                    modified = mock_modify_code_for_diff(state["code"], scenario)
                    return {**state, "modified_code": modified}

            def diff_node(state: DiffEvalState) -> DiffEvalState:
                """Analyze diff and collect to all_diffs (inside iteration loop)"""
                print(f"        [Diff] Analyzing code differences")
                try:
                    diff_text = analyze_diff_simple(state["code"], state["modified_code"])
                    print(f"        [Diff] Generated diff, length: {len(diff_text)}")

                    # Log modification and diff
                    logger.log_modification(state["code"], state["modified_code"], diff_text)
                    logger.log_diff(diff_text)

                    # Collect diff to all_diffs
                    all_scenarios = state.get("all_scenarios", [])
                    all_diffs = state.get("all_diffs", [])

                    # Get current type from the last scenario
                    if all_scenarios:
                        current_type = all_scenarios[-1]["type"]
                        all_diffs.append({
                            "type": current_type,
                            "diff_text": diff_text,
                            "modified_code": state["modified_code"]
                        })
                        print(f"        [Diff] Collected diff for {current_type} ({len(all_diffs)}/{len(ALL_PRINCIPLES)})")

                    return {**state, "all_diffs": all_diffs}
                except Exception as e:
                    print(f"        [Diff] ERROR: {e}")
                    return {**state, "error": f"Diff analysis error: {e}"}

            def pre_verification_node(state: DiffEvalState) -> DiffEvalState:
                """V6: Pre-verification for single violation type (inside iteration loop)"""
                print(f"        [PreVerification] Starting pre-verification")
                try:
                    # Get current scenario and diff
                    all_scenarios = state.get("all_scenarios", [])
                    all_diffs = state.get("all_diffs", [])
                    all_pre_verifications = state.get("all_pre_verifications", [])

                    if not all_scenarios or not all_diffs:
                        return {**state, "error": "No scenario or diff available for pre-verification"}

                    # Get the last scenario and diff (current iteration)
                    current_scenario_data = all_scenarios[-1]
                    current_diff_data = all_diffs[-1]

                    current_type = current_scenario_data["type"]
                    scenario = current_scenario_data["scenario"]
                    diff_text = current_diff_data["diff_text"]

                    print(f"        [PreVerification] Verifying {current_type}")

                    # Get scenario description
                    scenario_desc = scenario.get("prompt", "")
                    if scenario.get("ai_generated", False):
                        scenario_desc = scenario.get("scenario_description", scenario_desc)

                    # Format pre-verification prompt
                    from prompts_diff_eval import format_pre_verification_prompt

                    prompt = format_pre_verification_prompt(
                        code=state["code"],
                        scenario_description=scenario_desc,
                        diff_text=diff_text,
                        violation_type=current_type
                    )

                    # Call LLM for pre-verification
                    print(f"        [PreVerification] Calling LLM...")
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    response_text = response.content.strip()

                    print(f"        [PreVerification] Got response, length: {len(response_text)}")

                    # Parse pre-verification response
                    pre_verif_result = self._parse_pre_verification_response(response_text)

                    # Ensure violation_type is set
                    if "violation_type" not in pre_verif_result or not pre_verif_result["violation_type"]:
                        pre_verif_result["violation_type"] = current_type

                    print(f"        [PreVerification] Result: detected={pre_verif_result.get('is_detected', False)}")

                    # Update existing entry in all_pre_verifications (don't append)
                    # Find the entry for current_type and update it
                    updated = False
                    for i, pv in enumerate(all_pre_verifications):
                        if pv.get("violation_type") == current_type:
                            all_pre_verifications[i] = pre_verif_result
                            updated = True
                            print(f"        [PreVerification] Updated result for {current_type} (total: {len(all_pre_verifications)}/{len(ALL_PRINCIPLES)})")
                            break

                    if not updated:
                        # Fallback: append if not found (shouldn't happen)
                        all_pre_verifications.append(pre_verif_result)
                        print(f"        [PreVerification] Appended result for {current_type} (total: {len(all_pre_verifications)}/{len(ALL_PRINCIPLES)})")

                    return {**state, "all_pre_verifications": all_pre_verifications}

                except Exception as e:
                    print(f"        [PreVerification] ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    # Update existing entry with fallback result
                    all_pre_verifications = state.get("all_pre_verifications", [])
                    all_scenarios = state.get("all_scenarios", [])
                    if all_scenarios:
                        current_type = all_scenarios[-1]["type"]
                        fallback = {
                            "violation_type": current_type,
                            "is_detected": False,
                            "detailed_explanation": f"Error during pre-verification: {str(e)}"
                        }
                        # Update existing entry instead of appending
                        updated = False
                        for i, pv in enumerate(all_pre_verifications):
                            if pv.get("violation_type") == current_type:
                                all_pre_verifications[i] = fallback
                                updated = True
                                break
                        if not updated:
                            all_pre_verifications.append(fallback)
                    return {**state, "all_pre_verifications": all_pre_verifications, "error": f"Pre-verification error: {e}"}

            def verification_node(state: DiffEvalState) -> DiffEvalState:
                """V6: Unified verification - rank pre-verification results (outside iteration loop)"""
                print(f"        [Verification] Starting unified verification (V6 - ranking)")
                try:
                    # Get collected data
                    all_pre_verifications = state.get("all_pre_verifications", [])
                    code = state.get("code", "")

                    if len(all_pre_verifications) != len(ALL_PRINCIPLES):
                        print(f"        [Verification] ERROR: Incomplete pre-verification collection")
                        print(f"        [Verification] Pre-verifications: {len(all_pre_verifications)}, Expected: {len(ALL_PRINCIPLES)}")
                        return {**state, "error": "Incomplete pre-verification collection"}

                    # Format unified verification prompt V6
                    from prompts_diff_eval import format_unified_verification_prompt_v6

                    prompt = format_unified_verification_prompt_v6(
                        code=code,
                        all_pre_verifications=all_pre_verifications
                    )

                    # Call LLM for unified verification
                    print(f"        [Verification] Calling LLM for ranking...")
                    message = HumanMessage(content=prompt)
                    response = self.llm.invoke([message])
                    response_text = response.content.strip()

                    print(f"        [Verification] Got LLM response, length: {len(response_text)}")

                    # Parse LLM response
                    verification_result = self._parse_unified_verification_response(response_text)

                    # Log verification result
                    detected_type = verification_result.get("violation_type")
                    is_detected = verification_result.get("is_detected", False)
                    print(f"        [Verification] Result: detected={is_detected}, type={detected_type}")

                    if "all_checks" in verification_result:
                        print(f"        [Verification] All checks:")
                        for check in verification_result["all_checks"]:
                            print(f"        [Verification]   - {check.get('violation_type', 'N/A')}: {check.get('is_detected', False)}")

                    logger.log_verification("UNIFIED_V6", verification_result)

                    return {**state, "detection_result": verification_result}

                except Exception as e:
                    print(f"        [Verification] ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback result
                    all_pre_verifications = state.get("all_pre_verifications", [])
                    fallback = {
                        "is_detected": False,
                        "violation_type": None,
                        "explanation": f"Error during verification: {str(e)}",
                        "all_checks": all_pre_verifications  # Use pre-verification results as all_checks
                    }
                    return {**state, "detection_result": fallback, "error": str(e)}

            def finalize_node(state: DiffEvalState) -> DiffEvalState:
                """Format final output with metadata (verification already done)"""
                print(f"        [Finalize] Formatting final output")

                processing_time = time.time() - start_time
                detection_result = state.get("detection_result", {})

                # Get ground truth from example metadata
                ground_truth_violation = example.get("violation", None)
                if not ground_truth_violation and "violation_type" in example:
                    ground_truth_violation = example.get("violation_type")

                # Get detection info from verification_node result
                detected_type = detection_result.get("violation_type")
                is_detected = detection_result.get("is_detected", False)

                # Calculate detection_success (V8: top-n support)
                if ground_truth_violation:
                    # Check if ground truth is in any of the detected violations (comma-separated)
                    detection_success = evaluate_detection(ground_truth_violation, detected_type)
                else:
                    detection_success = is_detected

                # Build final output
                final_output = {
                    # Core detection fields from verification_node
                    "is_detected": is_detected,
                    "violation_type": detected_type,
                    "explanation": detection_result.get("explanation", ""),
                    "all_checks": detection_result.get("all_checks", []),

                    # Enhanced fields matching two_agent format
                    "example_id": example_id,
                    "description": example.get("description", ""),
                    "level": example.get("level", "UNKNOWN"),
                    "language": example.get("language", "python"),
                    "input": state.get("code", ""),
                    "detected_violation_type": detected_type,
                    "detection_success": detection_success,
                    "ground_truth": ground_truth_violation,
                    "api_call_success": True,
                    "errors": state.get("error", []) if isinstance(state.get("error"), list) else ([state.get("error")] if state.get("error") else []),
                    "processing_time_seconds": round(processing_time, 2),
                    "status": "completed",
                    "workflow": "diff_eval_v7",

                    # Diff-eval specific fields
                    "total_iterations": len(ALL_PRINCIPLES),
                    "selection_method": "ranking_llm",  # V6: LLM ranks pre-verification results
                }

                print(f"        [Finalize] Result: detected={is_detected}, type={detected_type}")
                if ground_truth_violation:
                    print(f"        [Finalize] Ground truth: {ground_truth_violation}, Match: {detection_success}")

                final_json = json.dumps(final_output, ensure_ascii=False)
                return {**state, "final_result": final_json}

            # Helper function for conditional routing from iterator
            def should_skip_or_continue(state: DiffEvalState) -> str:
                """Check if current test was skipped in iterator"""
                all_scenarios = state.get("all_scenarios", [])

                # Check if the last scenario was skipped
                if all_scenarios and all_scenarios[-1].get("scenario", {}).get("skipped", False):
                    # Test was skipped, check if we should continue or verify
                    current_idx = len(all_scenarios)
                    if current_idx >= len(ALL_PRINCIPLES):
                        return "verification"  # All done, go to verification
                    else:
                        return "iterator"  # Continue to next test
                else:
                    # Not skipped, proceed with scenario
                    return "scenario"

            # Build graph with iteration
            workflow = StateGraph(DiffEvalState)

            workflow.add_node("init_principles", init_principles_node)
            workflow.add_node("iterator", iterator_node)
            workflow.add_node("scenario", scenario_node)
            workflow.add_node("modify", modify_node)
            workflow.add_node("diff", diff_node)
            workflow.add_node("pre_verification", pre_verification_node)  # V6: New node
            workflow.add_node("verification", verification_node)
            workflow.add_node("finalize", finalize_node)

            # Graph structure: init principles, then iterate 5 times (scenario->modify->diff->pre_verification), then verify once
            workflow.add_edge(START, "init_principles")
            workflow.add_edge("init_principles", "iterator")

            # Conditional edge from iterator: skip to iterator again or go to scenario
            workflow.add_conditional_edges(
                "iterator",
                should_skip_or_continue,
                {"iterator": "iterator", "scenario": "scenario", "verification": "verification"}
            )

            workflow.add_edge("scenario", "modify")
            workflow.add_edge("modify", "diff")
            workflow.add_edge("diff", "pre_verification")  # V6: Add pre-verification after diff

            # Conditional edge: continue iteration or move to verification
            workflow.add_conditional_edges(
                "pre_verification",  # V6: Route from pre_verification instead of diff
                should_continue_iteration,
                {"iterator": "iterator", "verification": "verification"}
            )

            # After verification, go to finalize
            workflow.add_edge("verification", "finalize")
            workflow.add_edge("finalize", END)

            print(f"    [DEBUG] Compiling graph")
            app = workflow.compile()
            print(f"    [DEBUG] Graph compiled, executing")

            # Execute workflow once - it will iterate internally through all principles
            result = app.invoke(
                {
                    "code": input_code,
                    "language": example.get('language', 'PYTHON').lower(),  # Get language from dataset
                    "modified_code": "",  # Temporary field for passing between nodes
                    "all_scenarios": [],
                    "all_diffs": [],
                    "all_pre_verifications": [],  # V6: New field
                    "detection_result": {},
                    "final_result": "",
                    "error": None
                },
                config={"recursion_limit": 50}  # Increase recursion limit for iteration
            )

            print(f"    [DEBUG] Execution complete")

            # Always return final_result, even if there was an error
            # The error will be included in the final_result JSON
            final_result = result.get("final_result")

            if result.get("error"):
                print(f"    [ERROR] Diff-eval had error: {result['error']}")
                print(f"    [DEBUG] But returning result anyway (error included in output)")

            if not final_result:
                print(f"    [ERROR] No final_result in workflow output")
                return None

            return final_result

        except Exception as e:
            print(f"    [ERROR] Diff-eval workflow error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_workflow_name(self) -> str:
        return "diff_eval"


# ============================================================================
# WORKFLOW FACTORY
# ============================================================================

def create_workflow(workflow_type: str, model_name: str) -> WorkflowBase:
    """Factory function to create workflow instances"""
    if workflow_type == "single_agent":
        return SingleAgentWorkflow(model_name)
    elif workflow_type == "two_agent":
        return TwoAgentWorkflow(model_name)
    elif workflow_type == "multi_agent":
        return MultiAgentWorkflow(model_name)
    elif workflow_type == "diff_eval":
        return DiffEvalWorkflow(model_name)
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_langgraph_client():
    """Initialize LangGraph client and verify connection with the first model"""
    first_model = MODEL_SELECTION[0]
    is_cloud = first_model in CLOUD_MODELS

    try:
        if is_cloud:
            from langchain_openai import ChatOpenAI
            test_llm = ChatOpenAI(
                model=CLOUD_MODELS[first_model],
                base_url=OPENROUTER_BASE_URL,
                api_key=OPENROUTER_API_KEY,
                temperature=0.0,
                max_tokens=50,
                timeout=30,
            )
        else:
            test_llm = ChatOllama(
                model=first_model,
                base_url=OLLAMA_BASE_URL,
                temperature=0.0,
                num_predict=MAX_TOKENS,
                reasoning=False,
            )

        # Test connection with a simple query
        test_message = HumanMessage(content="Say 'Hello' in one word.")
        test_response = test_llm.invoke([test_message])

        provider = "OpenRouter" if is_cloud else "Ollama"
        print(f"[OK] LangGraph + {provider} client initialized")
        print(f"  Test Model: {first_model}")
        if not is_cloud:
            print(f"  Ollama Server: {OLLAMA_BASE_URL}")
        print(f"  Test Response: {test_response.content.strip()[:50]}...")
        return True

    except ImportError as e:
        print("[ERROR] Required package not available.")
        if is_cloud:
            print("   Install with: pip install langchain-openai")
        else:
            print("   Install with: pip install langgraph langchain-ollama")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"[WARN] Failed to test client connection: {e}")
        if not is_cloud:
            print("   Make sure Ollama is running with: ollama serve")
        print("   Continuing anyway - workflows will handle LLM errors with fallback mechanisms")
        return True

# ============================================================================
# DIRECTORY SETUP (V9: Enhanced with RUN_ID support)
# ============================================================================

def get_run_directory_name() -> str:
    """
    Get the run directory name based on RUN_ID configuration.

    Returns:
        str: The run directory name, or empty string for legacy behavior

    Examples:
        RUN_ID = None      → 'run_1', 'run_2', 'run_3', ... (auto-increment)
        RUN_ID = 1         → 'run_1'
        RUN_ID = 'test'    → 'run_test'
        RUN_ID = ''        → '' (no run directory, legacy behavior)
    """
    if benchmark_config.RUN_ID == '':
        # Legacy behavior: no run directory
        return ''

    if benchmark_config.RUN_ID is None:
        # Auto-increment: find the next available run number
        base_dir = Path(OUTPUT_DIR_BASE) / benchmark_config.WORKFLOW_TYPE
        if not base_dir.exists():
            return 'run_1'

        # Find all existing run directories
        existing_runs = []
        for item in base_dir.iterdir():
            if item.is_dir() and item.name.startswith('run_'):
                # Extract the number from run_N
                match = re.match(r'run_(\d+)', item.name)
                if match:
                    existing_runs.append(int(match.group(1)))

        # Get next run number
        next_run = max(existing_runs, default=0) + 1
        return f'run_{next_run}'

    # Fixed or custom run ID
    return f'run_{benchmark_config.RUN_ID}'


def setup_output_directory(model_name: str) -> Path:
    """
    Create and return output directory path for a specific model.

    Directory structure:
        - With RUN_ID: result/local/{WORKFLOW_TYPE}/run_{RUN_ID}/{model_name}/
        - Legacy (RUN_ID=''): result/local/{WORKFLOW_TYPE}/{model_name}/

    Args:
        model_name: Name of the model (e.g., 'qwen3:8b')

    Returns:
        Path: The output directory path
    """
    model_folder = model_name.replace(':', '-').replace('/', '-').replace('.', '-')

    # Get run directory name
    run_dir = get_run_directory_name()

    # Build output path
    if run_dir:
        # New behavior: include run directory
        output_dir = Path(OUTPUT_DIR_BASE) / benchmark_config.WORKFLOW_TYPE / run_dir / model_folder
    else:
        # Legacy behavior: no run directory
        output_dir = Path(OUTPUT_DIR_BASE) / benchmark_config.WORKFLOW_TYPE / model_folder

    output_dir.mkdir(exist_ok=True, parents=True)
    return output_dir


def setup_log_directory(model_name: str) -> Path:
    """
    Create and return log directory path for a specific model.

    Directory structure mirrors result structure:
        - With RUN_ID: logs/local/{WORKFLOW_TYPE}/run_{RUN_ID}/{model_name}/
        - Legacy (RUN_ID=''): logs/local/{WORKFLOW_TYPE}/{model_name}/

    Args:
        model_name: Name of the model (e.g., 'qwen3:8b')

    Returns:
        Path: The log directory path
    """
    model_folder = model_name.replace(':', '-').replace('/', '-').replace('.', '-')

    # Get run directory name (same logic as output directory)
    run_dir = get_run_directory_name()

    # Build log path (mirrors result structure)
    if run_dir:
        # New behavior: include run directory
        log_dir = Path('logs/local') / benchmark_config.WORKFLOW_TYPE / run_dir / model_folder
    else:
        # Legacy behavior: no run directory
        log_dir = Path('logs/local') / benchmark_config.WORKFLOW_TYPE / model_folder

    log_dir.mkdir(exist_ok=True, parents=True)
    return log_dir

# ============================================================================
# PROGRESS BAR (Same as original)
# ============================================================================

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█'):
    """Print progress bar to terminal"""
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        print()

# ============================================================================
# MODEL INTERACTION (LangGraph Workflows)
# ============================================================================

def call_workflow(workflow: WorkflowBase, example: Dict, example_id: str, violation_type: str) -> Optional[str]:
    """
    Call workflow to process an example using LangGraph.

    Args:
        workflow: The workflow instance to use
        example: The code example to analyze
        example_id: Unique identifier for the example
        violation_type: Expected violation type

    Returns:
        Model response text or None if failed
    """
    try:
        print(f"  [DEBUG] Calling workflow.process_example for {example_id}")
        response_text = workflow.process_example(example, example_id, violation_type)
        print(f"  [DEBUG] Workflow returned, response length: {len(response_text) if response_text else 0}")
        return response_text
    except Exception as e:
        print(f"  [ERROR] Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# RESPONSE PARSING (Same as original)
# ============================================================================

def parse_model_response(response_text: str) -> Dict:
    """
    Parse model response to extract violation detection results.
    Supports both old format (single violation) and new format (top-n violations array).

    Returns:
        dict: {
            'detected_violation_type': str or None (comma-separated if multiple),
            'explanation': str or None,
            'parse_error': str or None,
            'violations': list or None (new format: array of violations)
        }
    """
    result = {
        'detected_violation_type': None,
        'explanation': None,
        'parse_error': None,
        'violations': None
    }

    if not response_text:
        result['parse_error'] = 'Empty response'
        return result

    response_text = response_text.strip()

    try:
        # Remove markdown code blocks
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        # Find JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            result['parse_error'] = 'No JSON object found in response'
            return result

        json_text = json_match.group(0)
        json_text = re.sub(r',\s*}', '}', json_text)  # Remove trailing commas
        json_text = re.sub(r',\s*\]', ']', json_text)  # Remove trailing commas in arrays

        try:
            json_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            json_data = extract_json_fields_manual(json_text)
            if not json_data:
                result['parse_error'] = f'JSON parse error: {str(e)}'
                return result

        # Check for new format (violations array)
        if 'violations' in json_data and isinstance(json_data['violations'], list):
            violations = json_data['violations']
            result['violations'] = violations

            # Extract violation types (excluding NONE)
            detected_types = []
            explanations = []

            for v in violations:
                if isinstance(v, dict):
                    vtype = v.get('violation_type', '').strip().upper()
                    if vtype and vtype != 'NONE':
                        detected_types.append(vtype)
                        if 'explanation' in v:
                            explanations.append(f"{vtype}: {v['explanation']}")

            if detected_types:
                result['detected_violation_type'] = ', '.join(detected_types)
                result['explanation'] = ' | '.join(explanations) if explanations else None

            return result

        # Old format (single violation)
        is_detected = json_data.get('is_detected', json_data.get('if_detected', False))

        # Only extract violation_type if is_detected is true
        if is_detected and 'violation_type' in json_data:
            vtype = json_data['violation_type']
            if isinstance(vtype, str):
                vtype = vtype.strip()
                if vtype.lower() not in ['none', 'null', '']:
                    result['detected_violation_type'] = vtype

        # Extract explanation
        if 'explanation' in json_data:
            explanation = json_data['explanation']
            if isinstance(explanation, str):
                result['explanation'] = explanation.strip() if explanation else None

    except Exception as e:
        result['parse_error'] = f'Parse exception: {str(e)}'

    return result


def extract_json_fields_manual(text: str) -> Dict:
    """Manually extract JSON fields from malformed JSON"""
    fields = {}

    # Extract is_detected
    match = re.search(r'"(?:is_detected|if_detected)"\s*:\s*(true|false)', text, re.IGNORECASE)
    if match:
        fields['is_detected'] = match.group(1).lower() == 'true'

    # Extract violation_type
    match = re.search(r'"violation_type"\s*:\s*["\']([^"\']+)["\']', text)
    if match:
        fields['violation_type'] = match.group(1).strip()
    else:
        match = re.search(r'"violation_type"\s*:\s*(null|None)', text, re.IGNORECASE)
        if match:
            fields['violation_type'] = None

    # Extract explanation
    match = re.search(r'"explanation"\s*:\s*["\'](.+?)["\'](?:\s*,|\s*})', text, re.DOTALL)
    if match:
        fields['explanation'] = match.group(1).strip()

    return fields


def normalize_detector_output(raw_output: Optional[str]) -> str:
    """
    Normalize detector output into canonical JSON used by single-agent workflow.
    Ensures downstream parsing sees a consistent shape.
    Supports both old format (single violation) and new format (top-n violations array).

    Handles various detector output formats:
    1. New format: {"violations": [{"violation_type": "SRP", "confidence": "high", "explanation": "..."}]}
    2. Old format: {"is_detected": true, "violation_type": "SRP", "explanation": "..."}
    3. Complex format with nested analysis (extracts violations from nested structure)
    4. Markdown-wrapped JSON (strips ```json ... ```)
    """
    default_payload = {
        "violations": [{"violation_type": "NONE", "confidence": "none", "explanation": "Detector returned no output."}]
    }

    if not raw_output or not raw_output.strip():
        return json.dumps(default_payload, ensure_ascii=False)

    cleaned = raw_output.strip()

    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    # Find the outermost JSON object
    json_section = None
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        json_section = match.group(0)
        json_section = re.sub(r',\s*}', '}', json_section)
        json_section = re.sub(r',\s*\]', ']', json_section)

    data: Optional[Dict[str, Any]] = None
    if json_section:
        try:
            data = json.loads(json_section)
        except json.JSONDecodeError:
            data = extract_json_fields_manual(json_section)

    if not data:
        data = extract_json_fields_manual(cleaned)

    # Check for new format (violations array)
    if data and 'violations' in data and isinstance(data['violations'], list):
        # Already in new format, just validate and return
        violations = data['violations']
        if violations:
            return json.dumps({"violations": violations}, ensure_ascii=False)
        else:
            return json.dumps(default_payload, ensure_ascii=False)

    # Convert old format to new format
    normalized: Dict[str, Any] = {"violations": []}

    if data:
        # Check for simple old format first
        is_detected = data.get("is_detected")
        violation_type = data.get("violation_type")
        explanation = data.get("explanation")

        # Handle complex nested format (e.g., {"code_analysis": {"violations": [...]}})
        if "code_analysis" in data or "analysis" in data or ("violations" in data and not isinstance(data.get("violations"), list)):
            analysis = data.get("code_analysis") or data.get("analysis") or data
            violations = analysis.get("violations", []) if isinstance(analysis, dict) else []

            if violations and len(violations) > 0:
                # Extract violation types from nested structure
                detected_violations = []

                for v in violations:
                    if isinstance(v, dict):
                        principle = v.get("principle", "") or v.get("violation_type", "")
                        # Extract principle abbreviation (e.g., "Single Responsibility Principle (SRP)" -> "SRP")
                        vtype = None
                        if "SRP" in principle or "Single Responsibility" in principle:
                            vtype = "SRP"
                        elif "OCP" in principle or "Open/Closed" in principle or "Open-Closed" in principle:
                            vtype = "OCP"
                        elif "LSP" in principle or "Liskov" in principle:
                            vtype = "LSP"
                        elif "ISP" in principle or "Interface Segregation" in principle:
                            vtype = "ISP"
                        elif "DIP" in principle or "Dependency Inversion" in principle:
                            vtype = "DIP"

                        if vtype:
                            detected_violations.append({
                                "violation_type": vtype,
                                "confidence": v.get("confidence", "medium"),
                                "explanation": v.get("description", v.get("explanation", ""))
                            })

                if detected_violations:
                    normalized["violations"] = detected_violations
                    return json.dumps(normalized, ensure_ascii=False)

        # Handle simple old format - convert to new format
        if isinstance(is_detected, str):
            is_detected = is_detected.strip().lower() == "true"
        elif not isinstance(is_detected, bool):
            is_detected = False

        if is_detected and violation_type:
            vtype_str = str(violation_type).strip().upper()
            if vtype_str and vtype_str not in ['NONE', 'NULL', '']:
                normalized["violations"] = [{
                    "violation_type": vtype_str,
                    "confidence": data.get("confidence", "high"),
                    "explanation": explanation or ""
                }]
                return json.dumps(normalized, ensure_ascii=False)

    # No violations detected
    return json.dumps(default_payload, ensure_ascii=False)

# ============================================================================
# EVALUATION - V8: Updated for top-n detection
# ============================================================================

def evaluate_detection(expected_violation_type: str, detected_violation_type: str) -> bool:
    """
    Check if detection was successful.
    For top-n detection: returns True if expected violation is in any of the detected violations.

    Args:
        expected_violation_type: Ground truth violation type (e.g., "SRP")
        detected_violation_type: Detected violation(s), can be comma-separated (e.g., "SRP, OCP")

    Returns:
        True if expected violation is found in detected violations
    """
    if not detected_violation_type:
        return False

    expected = str(expected_violation_type).strip().upper()
    detected_str = str(detected_violation_type).strip().upper()

    # Split by comma to handle multiple violations (top-n format)
    detected_types = [vtype.strip() for vtype in detected_str.split(',')]

    # Check if expected violation is in any of the detected violations
    return expected in detected_types

# ============================================================================
# FILE I/O (Same as original)
# ============================================================================

def load_existing_results(output_file: Path, model_name: str) -> Dict:
    """Load existing results from file"""
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    return {
        'configuration': {
            'model': model_name,
            'workflow': WORKFLOW_TYPE,
            'temperature': TEMPERATURE,
            'max_examples_per_violation': MAX_EXAMPLES_PER_VIOLATION,
        },
        'total_examples': 0,
        'by_violation_type': {}
    }


def save_result_to_file(result: Dict, violation_type: str, output_file: Path, model_name: str):
    """Save a single result incrementally"""
    try:
        data = load_existing_results(output_file, model_name)

        # Initialize violation type if needed
        if violation_type not in data['by_violation_type']:
            data['by_violation_type'][violation_type] = {
                'results': [],
                'count': 0
            }

        # Append new result
        data['by_violation_type'][violation_type]['results'].append(result)
        data['by_violation_type'][violation_type]['count'] = len(
            data['by_violation_type'][violation_type]['results']
        )

        # Update total count
        data['total_examples'] = sum(v['count'] for v in data['by_violation_type'].values())

        # Write back
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception:
        pass  # Silent error handling


def get_example_status(example_id: str, violation_type: str, output_file: Path, model_name: str) -> str:
    """
    Check status of an example.

    Returns:
        'successful': Example completed successfully
        'failed': Example failed previously
        'new': Example not yet processed
    """
    if not output_file.exists():
        return 'new'

    try:
        data = load_existing_results(output_file, model_name)

        if violation_type not in data.get('by_violation_type', {}):
            return 'new'

        for result in data['by_violation_type'][violation_type].get('results', []):
            if result.get('example_id') == example_id:
                api_success = result.get('api_call_success', False)
                errors = result.get('errors', [])

                if api_success and len(errors) == 0:
                    return 'successful'
                else:
                    return 'failed'

        return 'new'

    except:
        return 'new'

# ============================================================================
# EXAMPLE PROCESSING (Same as original)
# ============================================================================

def should_process_example(status: str) -> bool:
    """Determine if example should be processed based on status and config"""
    if status == 'successful':
        return not SKIP_SUCCESSFUL
    elif status == 'failed':
        return RETRY_FAILED
    elif status == 'new':
        return PROCESS_NEW
    return False


def process_example(
    workflow: WorkflowBase,
    example: Dict,
    example_id: str,
    violation_type: str,
    output_file: Path,
    model_name: str
) -> Dict:
    """Process a single example using LangGraph workflow"""

    # Determine whether we need to run this example
    status = get_example_status(example_id, violation_type, output_file, model_name)
    if not should_process_example(status):
        return {
            'example_id': example_id,
            'status': status,
            'skipped': True
        }

    response_text: Optional[str] = None
    last_error: Optional[str] = None
    start_time = time.time()

    for retry in range(MAX_RETRIES):
        try:
            response_text = call_workflow(workflow, example, example_id, violation_type)
            if response_text:
                break
            last_error = "Empty response from workflow"
        except Exception as e:
            last_error = str(e)

        if retry < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS)

    elapsed_time = time.time() - start_time

    if not response_text:
        result = {
            'example_id': example_id,
            'violation_type': violation_type,
            'description': example.get('description', ''),
            'level': example.get('level', ''),
            'language': example.get('language', ''),
            'input': example.get('input', ''),
            'output': example.get('output', ''),
            'model_response': None,
            'detected_violation_type': None,
            'explanation': None,
            'detection_success': False,
            'api_call_success': False,
            'errors': [f"Empty response after {MAX_RETRIES} retries: {last_error}"],
            'processing_time_seconds': round(elapsed_time, 2),
            'status': status,
            'workflow': workflow.get_workflow_name()
        }
        save_result_to_file(result, violation_type, output_file, model_name)
        return result

    # Check if this is diff_eval workflow - it returns complete JSON
    if workflow.get_workflow_name() == "diff_eval":
        try:
            # diff_eval returns complete JSON result, just parse and use it
            result = json.loads(response_text)

            # Add status field if not present
            if 'status' not in result:
                result['status'] = status

            # Save and return
            save_result_to_file(result, violation_type, output_file, model_name)
            return result
        except json.JSONDecodeError as e:
            # If JSON parsing fails, fall through to standard parsing
            print(f"  [WARN] diff_eval returned invalid JSON: {e}")

    # Standard parsing for other workflows (single_agent, two_agent, multi_agent)
    parsed = parse_model_response(response_text)

    # Evaluate detection
    detection_success = evaluate_detection(violation_type, parsed['detected_violation_type'])

    # Determine success
    api_call_success = parsed['parse_error'] is None
    errors = [parsed['parse_error']] if parsed['parse_error'] else []

    # Build result
    result = {
        'example_id': example_id,
        'violation_type': violation_type,
        'description': example.get('description', ''),
        'level': example.get('level', ''),
        'language': example.get('language', ''),
        'input': example.get('input', ''),
        'output': example.get('output', ''),
        'model_response': response_text,
        'detected_violation_type': parsed['detected_violation_type'],
        'explanation': parsed['explanation'],
        'detection_success': detection_success,
        'api_call_success': api_call_success,
        'errors': errors,
        'processing_time_seconds': round(elapsed_time, 2),
        'status': status,
        'workflow': workflow.get_workflow_name()
    }

    # Save immediately
    save_result_to_file(result, violation_type, output_file, model_name)

    return result

# ============================================================================
# MAIN PROCESSING (Same as original)
# ============================================================================

def process_violation_type(workflow: WorkflowBase, violation_type: str, output_file: Path, model_name: str) -> Dict:
    """Process all examples for a violation type"""

    # Use same structure as result directory: logs/local/diff_eval/model_name/
    # Setup summary log with organized directory structure
    # Use setup_log_directory to match result structure with run_id
    import datetime
    log_base_dir = setup_log_directory(model_name)
    log_base_dir.mkdir(parents=True, exist_ok=True)

    summary_log = log_base_dir / "summary.log"

    def log_summary(message):
        """Write to summary log"""
        with open(summary_log, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    # Log run information
    log_summary("="*80)
    log_summary(f"PROCESSING {violation_type}")
    log_summary("="*80)
    log_summary(f"Timestamp: {datetime.datetime.now().isoformat()}")
    log_summary(f"Model: {model_name}")
    log_summary(f"Workflow: {workflow.get_workflow_name()}")
    log_summary("="*80)
    log_summary("")

    # Load dataset
    dataset_file = Path(DATASET_DIR) / f'{violation_type.lower()}_violations.json'

    if not dataset_file.exists():
        print(f"[WARN] Dataset file not found: {dataset_file}")
        return {'successful': 0, 'failed': 0, 'skipped': 0}

    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    examples = data.get('code_examples', [])

    # Limit examples if configured
    if MAX_EXAMPLES_PER_VIOLATION is not None:
        examples = examples[:MAX_EXAMPLES_PER_VIOLATION]

    print(f"\n{'='*80}")
    print(f"Processing {violation_type} Violations")
    print(f"{'='*80}")
    print(f"Total examples: {len(examples)}\n")

    stats = {'successful': 0, 'failed': 0, 'skipped': 0}

    # Process each example
    for idx, example in enumerate(examples):
        example_id = f"{violation_type}_{idx+1}"

        # Progress bar
        prefix = f"[{violation_type}]"
        suffix = f"({idx+1}/{len(examples)}) {example_id}"
        print_progress_bar(idx, len(examples), prefix=prefix, suffix=suffix)

        print(f"\n[DEBUG] About to call process_example for {example_id}", flush=True)
        sys.stdout.flush()

        result = process_example(workflow, example, example_id, violation_type, output_file, model_name)

        print(f"[DEBUG] process_example returned for {example_id}", flush=True)

        if result.get('skipped'):
            stats['skipped'] += 1
        elif result.get('api_call_success', False):
            stats['successful'] += 1
        else:
            stats['failed'] += 1

        # Delay between requests
        if not result.get('skipped'):
            time.sleep(REQUEST_DELAY_SECONDS)

    # Complete progress bar
    print_progress_bar(len(examples), len(examples),
                      prefix=f'[{violation_type}]',
                      suffix='Complete!')

    # Summary
    log_summary("")
    log_summary("="*80)
    log_summary(f"{violation_type} COMPLETED")
    log_summary("="*80)
    log_summary(f"Total examples: {len(examples)}")
    log_summary(f"  [OK] Successful: {stats['successful']}")
    log_summary(f"  [FAIL] Failed: {stats['failed']}")
    log_summary(f"  [SKIP] Skipped: {stats['skipped']}")
    log_summary(f"Success rate: {stats['successful']/len(examples)*100:.1f}%")
    log_summary("="*80)
    log_summary("")
    log_summary(f"Detailed logs saved to: {log_base_dir / violation_type.lower()}")
    log_summary(f"Results saved to: {output_file}")
    log_summary("")

    print(f"\n{violation_type} Completed:")
    print(f"  [OK] Successful: {stats['successful']}")
    print(f"  [FAIL] Failed: {stats['failed']}")
    print(f"  [SKIP] Skipped: {stats['skipped']}")
    print(f"{'='*80}\n")

    return stats


def run_benchmark():
    """Main benchmark execution using LangGraph workflows"""

    # Validate configuration
    errors = validate_config()
    if errors:
        print("\n[ERROR] Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix errors in benchmark_config.py")
        return 1

    # Print configuration
    print("\n" + "="*80)
    print("BENCHMARK RUNNER (LangGraph Edition)")
    print("="*80)
    print_config_summary()

    # Initialize LangGraph client
    if not init_langgraph_client():
        return 1

    print()

    # Overall stats across all models
    all_models_stats = {}
    overall_start_time = time.time()

    # Process each model
    for model_idx, model_name in enumerate(MODEL_SELECTION, 1):
        print(f"\n{'='*80}")
        print(f"MODEL [{model_idx}/{len(MODEL_SELECTION)}]: {model_name}")
        print(f"{'='*80}\n")

        # Create workflow for this model
        try:
            workflow = create_workflow(WORKFLOW_TYPE, model_name)
            print(f"[OK] Workflow created: {workflow.get_workflow_name()}")
        except Exception as e:
            print(f"[ERROR] Failed to create workflow: {e}")
            continue

        # Setup output for this model
        output_dir = setup_output_directory(model_name)
        output_file = output_dir / OUTPUT_FILENAME

        print(f"Output: {output_file}\n")
        print("="*80)

        # Process each violation type for this model
        model_stats = {
            'total_successful': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'by_violation': {}
        }

        model_start_time = time.time()

        for violation_type in VIOLATION_SELECTION:
            stats = process_violation_type(workflow, violation_type, output_file, model_name)
            model_stats['by_violation'][violation_type] = stats
            model_stats['total_successful'] += stats['successful']
            model_stats['total_failed'] += stats['failed']
            model_stats['total_skipped'] += stats['skipped']

        model_elapsed_time = time.time() - model_start_time

        # Model summary
        print(f"\n{'='*80}")
        print(f"MODEL {model_name} COMPLETED")
        print(f"{'='*80}")
        print(f"Framework: LangGraph + ChatOllama")
        print(f"Workflow: {workflow.get_workflow_name()}")
        print(f"Time: {model_elapsed_time/60:.2f} minutes")
        print(f"Successful: {model_stats['total_successful']}")
        print(f"Failed: {model_stats['total_failed']}")
        print(f"Skipped: {model_stats['total_skipped']}")
        print(f"\nBreakdown by Violation Type:")
        for vtype, stats in model_stats['by_violation'].items():
            print(f"  {vtype}: [OK]{stats['successful']} [FAIL]{stats['failed']} [SKIP]{stats['skipped']}")
        print(f"\nResults saved to: {output_file}")
        print(f"{'='*80}\n")

        # Store stats for this model
        all_models_stats[model_name] = model_stats

        # Small delay between models
        if model_idx < len(MODEL_SELECTION):
            print("Waiting 5 seconds before next model...\n")
            time.sleep(5)

    overall_elapsed_time = time.time() - overall_start_time

    # Final summary across all models
    if len(MODEL_SELECTION) > 1:
        print(f"\n{'='*80}")
        print("ALL MODELS BENCHMARK COMPLETED (LangGraph Edition)")
        print(f"{'='*80}")
        print(f"Total Time: {overall_elapsed_time/60:.2f} minutes")
        print(f"\nResults by Model:")
        for model_name, stats in all_models_stats.items():
            print(f"\n  {model_name}:")
            print(f"    Successful: {stats['total_successful']}")
            print(f"    Failed: {stats['total_failed']}")
            print(f"    Skipped: {stats['total_skipped']}")
        print(f"\n{'='*80}\n")

    return 0

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    sys.exit(run_benchmark())
