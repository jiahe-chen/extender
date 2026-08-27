"""
SOLID Detection Benchmark Configuration
========================================

This is your main configuration file for running SOLID violation detection benchmarks.
All settings are centralized here for easy modification.

Quick Start:
1. Configure MODEL_SELECTION below (uncomment models you want to test)
2. Configure VIOLATION_SELECTION (uncomment violations you want to test)
3. Set MAX_EXAMPLES_PER_VIOLATION (or None for all)
4. Run: python benchmark_runner.py

Note: Multiple models and violations can be selected. They will be tested sequentially.
Example configurations:

Single model, single violation:
    MODEL_SELECTION = ['deepseek-r1:8b']
    VIOLATION_SELECTION = ['LSP']

Multiple models, single violation:
    MODEL_SELECTION = ['deepseek-r1:8b', 'qwen3:8b', 'llama3.1:8b']
    VIOLATION_SELECTION = ['LSP']

Single model, multiple violations:
    MODEL_SELECTION = ['deepseek-r1:8b']
    VIOLATION_SELECTION = ['LSP', 'SRP', 'DIP']

Multiple models, multiple violations (full benchmark):
    MODEL_SELECTION = ['deepseek-r1:8b', 'qwen3:8b']
    VIOLATION_SELECTION = ['LSP', 'SRP', 'OCP', 'ISP', 'DIP']
"""

import os

import openai

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
# Select models to test. Uncomment the ones you want to use.
# Multiple models will be tested sequentially.

MODEL_SELECTION = [
    # Local (Ollama)
    # 'qwen3:8b',
    'qwen3.5:9b',
    # 'deepseek-r1:8b',
    # 'qwen3:4b',
    # 'llama3.1:8b',
    # 'gemma3:4b',
    # 'llama3.2:3b',
    # 'qwen3:14b',
    # 'deepseek-r1:14b',

    # Cloud (OpenRouter)
    # 'claude-opus-4.6',
    # 'gpt-5.2',
    # 'qwen3.5',
    # 'gemini-3-pro',
    # 'z-glm-5',
    # 'deepseek-r1-cloud',
    # 'qwen3-max',
    # 'qwen3.5-397b'
    # 'minimax'

]

# Short name → OpenRouter model ID mapping
CLOUD_MODELS = {
    'claude-opus-4.6':  'anthropic/claude-opus-4-6',
    'gpt-5.2':            'openai/gpt-5.2-codex',
    'qwen3.5':          'qwen/qwen3.5-plus-02-15',
    'gemini-3-pro':   'google/gemini-3-pro-preview',
    'deepseek-r1-cloud': 'deepseek/deepseek-r1',
    'z-glm-5': 'z-ai/glm-5',
    'qwen3-max': 'qwen/qwen3-max',
    'qwen3.5-397b': 'qwen/qwen3.5-397b-a17b',
    'minimax': 'minimax/minimax-m2.5'
}

# ============================================================================
# VIOLATION TYPE SELECTION
# ============================================================================
# Select which SOLID violations to test. Uncomment the ones you want.
# Each violation has 48 examples in the dataset.
#
# For multi_agent workflow, you can also specify a file path directly:
#   VIOLATION_SELECTION = 'test_cases/dip_easy_input.py'  # Single file
#   VIOLATION_SELECTION = ['test_cases/file1.py', 'test_cases/file2.py']  # Multiple files

VIOLATION_SELECTION = [
    'SRP',  # Single Responsibility Principle
    'OCP',  # Open/Closed Principle
    'LSP',  # Liskov Substitution Principle
    'ISP',  # Interface Segregation Principle
    'DIP',  # Dependency Inversion Principle
]

# For multi_agent mode - specify files directly:
# VIOLATION_SELECTION = 'test_cases/dip_easy_input.py'
# VIOLATION_SELECTION = 'test_cases/dip_difficult_input.py'
# VIOLATION_SELECTION = ['test_cases/dip_easy_input.py', 'test_cases/test_dip_sms.py']

# ============================================================================
# WORKFLOW CONFIGURATION
# ============================================================================
# Select the detection workflow/strategy

# WORKFLOW_TYPE = 'single_agent'   # Single agent detection
# WORKFLOW_TYPE = 'two_agent'      # Detector + Evaluator with feedback loop
WORKFLOW_TYPE = 'diff_eval'      # Diff-based evaluation with iteration

# ============================================================================
# EXECUTION LIMITS
# ============================================================================
# Control how many examples to process per violation type

# MAX_EXAMPLES_PER_VIOLATION = 3   # Test with just 3 examples for initial testing
# MAX_EXAMPLES_PER_VIOLATION = 5   # Test with just 5 examples
# MAX_EXAMPLES_PER_VIOLATION = 15  # Test with 10 examples
MAX_EXAMPLES_PER_VIOLATION = None  # None = all examples (48)

# ============================================================================
# MODEL PARAMETERS
# ============================================================================
# Fine-tune model behavior

TEMPERATURE = 0.0           # 0.0 = deterministic, 1.0 = creative
MAX_TOKENS = -1           # Maximum response length
MAX_RETRIES = 3             # Retry failed API calls this many times
RETRY_DELAY_SECONDS = 2     # Wait time between retries
REQUEST_DELAY_SECONDS = 0.5 # Delay between requests to avoid rate limits

# ============================================================================
# TOP-N DETECTION CONFIGURATION
# ============================================================================
# Control how many violations to output (ranked by confidence)
# If any violation in the top-N matches ground truth, detection is successful

# TOP_N = 1  # Output only the most likely violation (traditional behavior)
TOP_N = 2  # Output top 2 most likely violations (default)
# TOP_N = 3  # Output top 3 most likely violations
# TOP_N = 5  # Output all 5 SOLID principles ranked by likelihood

# Note: This applies to single_agent, two_agent, and diff_eval workflows.
# All workflows will output top-N violations ranked by likelihood.

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================
# Ollama server settings

OLLAMA_BASE_URL = 'http://localhost:11434'  # Default Ollama server

# ============================================================================
# OPENROUTER CONFIGURATION (Cloud Models)
# ============================================================================
# OpenRouter API settings for cloud model access.
# Get your API key at: https://openrouter.ai/keys

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'

# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================
# Control where results are saved

OUTPUT_DIR_BASE = 'result/local'  # Base directory for results
OUTPUT_FILENAME = 'detection_results.json'  # Output file name

# Run identifier - set to None for auto-increment, or specify a number/string
# Examples:
# RUN_ID = None      # Auto: run_1, run_2, run_3, ...
# RUN_ID = 1         # Fixed: run_1
# RUN_ID = 'top1_new_model'    # Custom: run_test
RUN_ID = 'ase2026_reproduction'
# RUN_ID = ''        # No run ID (legacy behavior)
# RUN_ID = None

# Results will be organized as:
# result/local/{WORKFLOW_TYPE}/run_{RUN_ID}/{model_name}/detection_results.json
# Example: result/local/single_agent/run_1/qwen3-8b/detection_results.json

# ============================================================================
# SKIP AND RETRY BEHAVIOR
# ============================================================================
# Control how the system handles previously processed examples

SKIP_SUCCESSFUL = True   # Skip examples that completed successfully
RETRY_FAILED = True      # Retry examples that failed previously
PROCESS_NEW = True       # Process examples not yet attempted

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================
# Dataset location (usually no need to change)

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')

# Dataset files expected:
# - lsp_violations.json (48 examples)
# - srp_violations.json (48 examples)
# - ocp_violations.json (48 examples)
# - isp_violations.json (48 examples)
# - dip_violations.json (48 examples)

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration before running"""
    errors = []

    # Check model selection
    if not MODEL_SELECTION:
        errors.append("MODEL_SELECTION must have at least one model")
    elif not isinstance(MODEL_SELECTION, list):
        errors.append("MODEL_SELECTION must be a list of model names")

    # Check OpenRouter API key if any cloud model is selected
    if isinstance(MODEL_SELECTION, list):
        cloud_models_selected = [m for m in MODEL_SELECTION if m in CLOUD_MODELS]
        if cloud_models_selected and not OPENROUTER_API_KEY:
            errors.append(
                f"OPENROUTER_API_KEY is required for cloud models: {', '.join(cloud_models_selected)}. "
                "Set it via environment variable or .env file."
            )

    # Check workflow type
    if WORKFLOW_TYPE not in ['single_agent', 'two_agent', 'multi_agent', 'diff_eval']:
        errors.append(f"Invalid WORKFLOW_TYPE: {WORKFLOW_TYPE}")

    # Validate based on workflow type
    if WORKFLOW_TYPE == 'multi_agent':
        # For multi_agent, VIOLATION_SELECTION can be:
        # - A file path (string)
        # - A list of file paths
        # - A list of SOLID principles
        if isinstance(VIOLATION_SELECTION, str):
            # Single file path
            if not os.path.exists(VIOLATION_SELECTION):
                errors.append(f"File not found: {VIOLATION_SELECTION}")
        elif isinstance(VIOLATION_SELECTION, list):
            valid_violations = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP', 'ALL']
            for v in VIOLATION_SELECTION:
                if v not in valid_violations:
                    # Check if it's a file path
                    if not os.path.exists(v):
                        errors.append(f"Invalid violation type or file not found: {v}")

        # Validate MULTI_AGENT_FOCUS
        valid_focus = ['ALL', 'SRP', 'OCP', 'LSP', 'ISP', 'DIP']
        for f in MULTI_AGENT_FOCUS:
            if f not in valid_focus:
                errors.append(f"Invalid MULTI_AGENT_FOCUS: {f}. Must be one of {valid_focus}")
    else:
        # For single_agent and two_agent
        if not VIOLATION_SELECTION:
            errors.append("VIOLATION_SELECTION must have at least one violation type")

        valid_violations = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
        if isinstance(VIOLATION_SELECTION, list):
            for v in VIOLATION_SELECTION:
                if v not in valid_violations:
                    errors.append(f"Invalid violation type: {v}. Must be one of {valid_violations}")

    return errors

# ============================================================================
# CONFIGURATION SUMMARY
# ============================================================================

def print_config_summary():
    """Print current configuration"""
    print("\n" + "="*80)
    print("BENCHMARK CONFIGURATION")
    print("="*80)
    print(f"Workflow: {WORKFLOW_TYPE}")
    print(f"Models: {', '.join(MODEL_SELECTION) if isinstance(MODEL_SELECTION, list) else MODEL_SELECTION}")

    if WORKFLOW_TYPE == 'multi_agent':
        if isinstance(VIOLATION_SELECTION, str):
            print(f"Input File: {VIOLATION_SELECTION}")
        elif isinstance(VIOLATION_SELECTION, list):
            # Check if it's file paths or violation types
            if VIOLATION_SELECTION and os.path.exists(str(VIOLATION_SELECTION[0])):
                print(f"Input Files: {VIOLATION_SELECTION}")
            else:
                print(f"Violations: {', '.join(VIOLATION_SELECTION)}")
        print(f"Focus Principles: {', '.join(MULTI_AGENT_FOCUS)}")
        print(f"Concurrent Workers: {MULTI_AGENT_WORKERS}")
        print(f"Output: logs/")
    elif WORKFLOW_TYPE == 'diff_eval':
        # V8: Show diff_eval specific configuration
        print(f"Violations: {', '.join(VIOLATION_SELECTION) if isinstance(VIOLATION_SELECTION, list) else VIOLATION_SELECTION}")
        print(f"Top-N Detection: {TOP_N} (output top {TOP_N} most likely violations)")
        print(f"Run ID: {RUN_ID if RUN_ID is not None else 'Auto'}")
        print(f"Max Examples/Violation: {MAX_EXAMPLES_PER_VIOLATION if MAX_EXAMPLES_PER_VIOLATION else 'All (48)'}")
        print(f"Skip Successful: {SKIP_SUCCESSFUL}")
        print(f"Retry Failed: {RETRY_FAILED}")
        print(f"Process New: {PROCESS_NEW}")
    else:
        # V8: Show single_agent and two_agent specific configuration
        print(f"Violations: {', '.join(VIOLATION_SELECTION) if isinstance(VIOLATION_SELECTION, list) else VIOLATION_SELECTION}")
        print(f"Top-N Detection: {TOP_N} (output top {TOP_N} most likely violations)")
        print(f"Run ID: {RUN_ID if RUN_ID is not None else 'Auto'}")
        print(f"Max Examples/Violation: {MAX_EXAMPLES_PER_VIOLATION if MAX_EXAMPLES_PER_VIOLATION else 'All (48)'}")
        print(f"Skip Successful: {SKIP_SUCCESSFUL}")
        print(f"Retry Failed: {RETRY_FAILED}")
        print(f"Process New: {PROCESS_NEW}")

    print(f"Temperature: {TEMPERATURE}")
    print("="*80 + "\n")
