#!/usr/bin/env python3
"""
Universal SOLID Detection Benchmark Runner
==========================================

A clean, well-structured script for running SOLID violation detection benchmarks.

Features:
- Configurable model selection (any Ollama model)
- Selectable SOLID violations (SRP, OCP, LSP, ISP, DIP)
- Multiple workflow support (single_agent, two_agent, multi_agent)
- Smart skip/retry mechanism
- Progress tracking and resumable execution
- Centralized prompt management

Usage:
    1. Edit benchmark_config.py to configure your benchmark
    2. Run: python benchmark_runner.py

The script will:
- Skip successfully processed examples
- Retry previously failed examples
- Process new examples
- Save results incrementally
"""

import json
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

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
    validate_config,
    print_config_summary
)

from prompts import get_detection_prompt, format_prompt

# ============================================================================
# INITIALIZATION
# ============================================================================

def init_ollama_client():
    """Initialize Ollama client"""
    try:
        import ollama
        # Test connection
        ollama.list()
        print(f"[OK] Ollama client initialized")
        print(f"  Server: {OLLAMA_BASE_URL}")
        return ollama
    except ImportError:
        print("[ERROR] Ollama package not installed.")
        print("   Install with: pip install ollama")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to connect to Ollama: {e}")
        print("   Make sure Ollama is running with: ollama serve")
        return None

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

# ============================================================================
# PROGRESS BAR
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
# MODEL INTERACTION
# ============================================================================

def call_ollama_model(client, prompt: str, model_name: str) -> Optional[str]:
    """Call Ollama model with prompt"""
    try:
        response = client.generate(
            model=model_name,
            prompt=prompt,
            options={
                'temperature': TEMPERATURE,
                'num_predict': MAX_TOKENS,
            },
            think=False,  # Disable thinking mode for qwen3 models
            format='json',  # Force JSON output format
        )
        result = response.get('response', '')
        if not result:
            print(f"  [WARN] Ollama returned empty response. Full response: {response}")
        return result if result else None
    except Exception as e:
        print(f"  [ERROR] Ollama error: {e}")
        return None

# ============================================================================
# RESPONSE PARSING
# ============================================================================

def parse_model_response(response_text: str) -> Dict:
    """
    Parse model response to extract violation detection results.

    Returns:
        dict: {
            'detected_violation_type': str or None,
            'explanation': str or None,
            'parse_error': str or None
        }
    """
    result = {
        'detected_violation_type': None,
        'explanation': None,
        'parse_error': None
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

        try:
            json_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            json_data = extract_json_fields_manual(json_text)
            if not json_data:
                result['parse_error'] = f'JSON parse error: {str(e)}'
                return result

        # Extract fields
        is_detected = json_data.get('is_detected', json_data.get('if_detected', False))

        if is_detected and 'violation_type' in json_data:
            vtype = json_data['violation_type']
            if isinstance(vtype, str):
                vtype = vtype.strip()
                if vtype.lower() in ['none', 'null', ''] or vtype == '':
                    result['detected_violation_type'] = None
                else:
                    result['detected_violation_type'] = vtype
            elif vtype is None:
                result['detected_violation_type'] = None
        else:
            result['detected_violation_type'] = None

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

# ============================================================================
# EVALUATION
# ============================================================================

def evaluate_detection(expected_violation_type: str, detected_violation_type: str) -> bool:
    """Check if detection was successful"""
    if not detected_violation_type:
        return False

    expected = str(expected_violation_type).strip().upper()
    detected_str = str(detected_violation_type).strip().upper()
    detected_types = [vtype.strip() for vtype in detected_str.split(',')]

    return expected in detected_types

# ============================================================================
# FILE I/O
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
    """Save a single result incrementally, replacing existing record if same example_id"""
    try:
        data = load_existing_results(output_file, model_name)

        # Initialize violation type if needed
        if violation_type not in data['by_violation_type']:
            data['by_violation_type'][violation_type] = {
                'results': [],
                'count': 0
            }

        # Find and replace existing result with same example_id, or append new
        results = data['by_violation_type'][violation_type]['results']
        example_id = result.get('example_id')

        # Remove any existing record with same example_id
        results = [r for r in results if r.get('example_id') != example_id]

        # Add new result
        results.append(result)

        # Sort by example_id (extract number for proper sorting)
        def extract_id_num(r):
            eid = r.get('example_id', '')
            # Extract number from e.g. "OCP_1" -> 1
            parts = eid.split('_')
            if len(parts) >= 2 and parts[-1].isdigit():
                return int(parts[-1])
            return 0

        results.sort(key=extract_id_num)

        data['by_violation_type'][violation_type]['results'] = results
        data['by_violation_type'][violation_type]['count'] = len(results)

        # Update total count
        data['total_examples'] = sum(v['count'] for v in data['by_violation_type'].values())

        # Write back
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"\n[ERROR] Error saving result: {e}")  # Show error for debugging


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
# EXAMPLE PROCESSING
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
    client,
    example: Dict,
    example_id: str,
    violation_type: str,
    output_file: Path,
    model_name: str
) -> Dict:
    """Process a single example"""

    # Check status
    status = get_example_status(example_id, violation_type, output_file, model_name)

    if not should_process_example(status):
        return {
            'example_id': example_id,
            'status': status,
            'skipped': True
        }

    # Get and format prompt
    prompt_template = get_detection_prompt(WORKFLOW_TYPE)
    prompt = format_prompt(prompt_template, input_code=example.get('input', ''))

    # Call model with retries
    start_time = time.time()
    response_text = None
    last_error = None

    for retry in range(MAX_RETRIES):
        try:
            response_text = call_ollama_model(client, prompt, model_name)
            if response_text:
                break
        except Exception as e:
            last_error = e
            if retry < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
            continue

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
            'processing_time_seconds': round(elapsed_time, 2)
        }
        # Save failed result too
        save_result_to_file(result, violation_type, output_file, model_name)
        return result

    # Parse response
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
        'processing_time_seconds': round(elapsed_time, 2)
    }

    # Save immediately
    print(f"\n  Saving {example_id} to {output_file}...")
    save_result_to_file(result, violation_type, output_file, model_name)
    print(f"  [OK] Saved {example_id}")

    return result

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_violation_type(client, violation_type: str, output_file: Path, model_name: str) -> Dict:
    """Process all examples for a violation type"""

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

        result = process_example(client, example, example_id, violation_type, output_file, model_name)

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
    print(f"\n{violation_type} Completed:")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"{'='*80}\n")

    return stats


def run_benchmark():
    """Main benchmark execution"""

    # Validate configuration
    errors = validate_config()
    if errors:
        print("\n[ERROR] Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix errors in benchmark_config.py")
        return 1

    # Print configuration
    print_config_summary()

    # Initialize client
    client = init_ollama_client()
    if client is None:
        return 1

    # Overall stats across all models
    all_models_stats = {}
    overall_start_time = time.time()

    # Process each model
    for model_idx, model_name in enumerate(MODEL_SELECTION, 1):
        print(f"\n{'='*80}")
        print(f"MODEL [{model_idx}/{len(MODEL_SELECTION)}]: {model_name}")
        print(f"{'='*80}\n")

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
            stats = process_violation_type(client, violation_type, output_file, model_name)
            model_stats['by_violation'][violation_type] = stats
            model_stats['total_successful'] += stats['successful']
            model_stats['total_failed'] += stats['failed']
            model_stats['total_skipped'] += stats['skipped']

        model_elapsed_time = time.time() - model_start_time

        # Model summary
        print(f"\n{'='*80}")
        print(f"MODEL {model_name} COMPLETED")
        print(f"{'='*80}")
        print(f"Time: {model_elapsed_time/60:.2f} minutes")
        print(f"Successful: {model_stats['total_successful']}")
        print(f"Failed: {model_stats['total_failed']}")
        print(f"Skipped: {model_stats['total_skipped']}")
        print(f"\nBreakdown by Violation Type:")
        for vtype, stats in model_stats['by_violation'].items():
            print(f"  {vtype}: OK={stats['successful']} FAIL={stats['failed']} SKIP={stats['skipped']}")
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
        print("ALL MODELS BENCHMARK COMPLETED")
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
