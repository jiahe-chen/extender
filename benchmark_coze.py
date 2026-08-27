"""
Universal batch evaluation script for ALL SOLID violation types.
This script processes violation types (SRP, OCP, LSP, ISP, DIP) using a single workflow.
Outputs results incrementally to a unified JSON file after each Coze response.

Features:
- Configurable number of queries to process
- Configurable output filename
- Skip already successfully processed queries
- Detection success evaluation (violation_type matching)
- Refactor quality evaluation (ChrF score)
"""

import json
import re
import time
from pathlib import Path
from cozepy import COZE_CN_BASE_URL, Coze, TokenAuth, Stream, WorkflowEvent, WorkflowEventType
from sacrebleu.metrics import CHRF

# ============================================================================
# CONFIGURATION - Modify these settings as needed
# ============================================================================

# Number of queries to process per violation type (None = all queries)
# Default: None (processes all 48 examples per type, total 240)
# Example: Set to 10 to process only first 10 examples per type
# Note: The script will skip already successfully processed queries
MAX_EXAMPLES_PER_TYPE = None  # Set to None to process all examples

# Output filename (will be saved in json_output_demo/)
# Default: 'auto_detection_doubao_1.5_pro.json'
# Examples: 'auto_detection_deepseek_V3.json', 'auto_detection_gpt4.json'
# OUTPUT_FILENAME = 'auto_detection_doubao_1.5_pro.json'
OUTPUT_FILENAME = 'auto_detection_deepseek_V3.json'

# ============================================================================
# API Configuration
# ============================================================================

coze_api_token = 'sat_fliOOZnWPQZNrFIZzP1P0CKtkJtv4VaEDKm3YkkENtv2NnvaZ3IVcjdsFBPpufCr'
coze_api_base = COZE_CN_BASE_URL
workflow_id = '7568307915434508307'  # Universal workflow for all violation types

# Initialize Coze client
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Dataset directory
dataset_dir = Path('/Users/he/jcSOLID/dataset')
results_dir = Path('/Users/he/jcSOLID/json_output_demo')
results_dir.mkdir(exist_ok=True)

# Output file
output_file = results_dir / OUTPUT_FILENAME

# Violation types to process
VIOLATION_TYPES = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']

# Initialize ChrF metric
chrf = CHRF()


def extract_message_content(message):
    """
    Extract just the content field from a message object.
    Handles both dict and object types.
    """
    try:
        # If it's a dict
        if isinstance(message, dict):
            return message.get('content', str(message))

        # If it has a content attribute
        if hasattr(message, 'content'):
            content = message.content
            # If content is a string, try to parse as JSON
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except:
                    return content
            return content

        # Fallback: convert to string and try to extract
        msg_str = str(message)
        if "content='" in msg_str or 'content="' in msg_str:
            # Try to extract content between quotes
            match = re.search(r"content='([^']*)'", msg_str)
            if not match:
                match = re.search(r'content="([^"]*)"', msg_str)
            if match:
                content_str = match.group(1)
                try:
                    return json.loads(content_str)
                except:
                    return content_str

        return str(message)
    except Exception as e:
        print(f"  Warning: Could not extract content from message: {e}")
        return str(message)


def parse_coze_response(coze_response):
    """
    Parse coze_response to extract violation_type and refactored_code.

    Args:
        coze_response: List of response strings from Coze API

    Returns:
        dict: {
            'detected_violation_type': str or None,
            'refactored_code': str or None,
            'parse_error': str or None
        }
    """
    result = {
        'detected_violation_type': None,
        'refactored_code': None,
        'parse_error': None
    }

    if not coze_response or len(coze_response) == 0:
        result['parse_error'] = 'Empty coze_response'
        return result

    # Get the first response
    response_text = coze_response[0] if isinstance(coze_response, list) else coze_response

    if not isinstance(response_text, str):
        response_text = str(response_text)

    response_text = response_text.strip()

    try:
        # Try to parse as JSON
        if response_text.startswith('{'):
            # Try to fix common JSON issues
            # Remove trailing commas before }
            response_text = re.sub(r',\s*}', '}', response_text)
            # Try to parse
            try:
                json_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON manually
                json_data = extract_json_fields(response_text)

            # Extract violation_type (keep all detected violations)
            if 'violation_type' in json_data:
                vtype = json_data['violation_type']
                if isinstance(vtype, str):
                    vtype = vtype.strip()
                    # Keep all violations (e.g., "SRP, DIP" stays as "SRP, DIP")
                    result['detected_violation_type'] = vtype if vtype else None

            # Extract refactored_code
            if 'refactored_code' in json_data:
                code = json_data['refactored_code']
                if isinstance(code, str):
                    # Remove markdown code blocks if present
                    code = re.sub(r'^```\w*\n', '', code)
                    code = re.sub(r'\n```$', '', code)
                    result['refactored_code'] = code.strip() if code else None
        else:
            # Not a JSON, try to extract fields manually
            extracted = extract_json_fields(response_text)
            if extracted:
                if 'violation_type' in extracted:
                    vtype = str(extracted['violation_type']).strip()
                    # Keep all violations
                    result['detected_violation_type'] = vtype if vtype else None
                if 'refactored_code' in extracted:
                    code = str(extracted['refactored_code']).strip()
                    # Remove markdown code blocks
                    code = re.sub(r'^```\w*\n', '', code)
                    code = re.sub(r'\n```$', '', code)
                    result['refactored_code'] = code if code else None

    except Exception as e:
        result['parse_error'] = f'Parse exception: {str(e)}'

    return result


def extract_json_fields(text):
    """
    Manually extract JSON fields from malformed JSON text.
    """
    fields = {}

    # Extract violation_type (handle unquoted values like: "violation_type":SRP, DIP,)
    # First try: quoted value
    match = re.search(r'"violation_type"\s*:\s*["\']([^"\']+)["\']', text)
    if match:
        fields['violation_type'] = match.group(1).strip()
    else:
        # Second try: unquoted value (capture until newline or "explanation")
        # This handles cases like: "violation_type":SRP, DIP,\n"explanation"
        match = re.search(r'"violation_type"\s*:\s*([^\n]+?)(?:,\s*\n|"explanation")', text)
        if match:
            value = match.group(1).strip()
            # Remove trailing comma and whitespace
            value = value.rstrip(',').strip()
            fields['violation_type'] = value

    # Extract refactored_code (look for code between triple backticks or quotes)
    match = re.search(r'"refactored_code"\s*:\s*["\']?```[\w]*\n(.+?)```["\']?', text, re.DOTALL)
    if match:
        fields['refactored_code'] = match.group(1).strip()
    else:
        # Try without backticks
        match = re.search(r'"refactored_code"\s*:\s*["\']((?:.|\n)*?)["\'](?:\s*[,}])', text, re.DOTALL)
        if match:
            fields['refactored_code'] = match.group(1).strip()

    return fields


def calculate_chrf_score(reference, hypothesis):
    """
    Calculate ChrF score between reference and hypothesis.

    Args:
        reference: Ground truth code (string)
        hypothesis: Generated code (string)

    Returns:
        float: ChrF score (0-100), or None if calculation fails
    """
    try:
        if not reference or not hypothesis:
            return None

        # Clean up strings
        reference = reference.strip()
        hypothesis = hypothesis.strip()

        if not reference or not hypothesis:
            return None

        # Calculate sentence-level ChrF score
        score = chrf.sentence_score(hypothesis, [reference])
        return round(score.score, 2)

    except Exception as e:
        print(f"    Warning: ChrF calculation failed: {e}")
        return None


def evaluate_detection(expected_violation_type, detected_violation_type):
    """
    Evaluate if detection was successful.

    Supports multiple violations separated by commas (e.g., "SRP, DIP").
    Detection is successful if the expected type is mentioned in the detected types.

    Args:
        expected_violation_type: Expected violation type from dataset (e.g., "SRP")
        detected_violation_type: Detected violation type from coze_response (e.g., "SRP, DIP")

    Returns:
        bool: True if expected type is found in detected types, False otherwise

    Examples:
        evaluate_detection("SRP", "SRP") -> True
        evaluate_detection("SRP", "SRP, DIP") -> True
        evaluate_detection("DIP", "SRP, DIP") -> True
        evaluate_detection("OCP", "SRP, DIP") -> False
    """
    if not detected_violation_type:
        return False

    # Normalize expected type
    expected = str(expected_violation_type).strip().upper()

    # Normalize detected type and split by comma
    detected_str = str(detected_violation_type).strip().upper()

    # Split by comma and strip whitespace from each type
    detected_types = [vtype.strip() for vtype in detected_str.split(',')]

    # Check if expected type is in the list of detected types
    return expected in detected_types


def handle_workflow_iterator(stream: Stream[WorkflowEvent], example_id: str):
    """
    Handle workflow events and collect only content from results.
    """
    content_results = []
    errors = []

    for event in stream:
        if event.event == WorkflowEventType.MESSAGE:
            content = extract_message_content(event.message)
            print(f"  [Example {example_id}] Got content: {str(content)[:100]}...")
            content_results.append(content)
        elif event.event == WorkflowEventType.ERROR:
            print(f"  [Example {example_id}] Got error: {event.error}")
            errors.append(str(event.error))
        elif event.event == WorkflowEventType.INTERRUPT:
            handle_workflow_iterator(
                coze.workflows.runs.resume(
                    workflow_id=workflow_id,
                    event_id=event.interrupt.interrupt_data.event_id,
                    resume_data="hey",
                    interrupt_type=event.interrupt.interrupt_data.type,
                ),
                example_id
            )

    return {
        'content': content_results,
        'errors': errors
    }


def save_result_to_file(result, violation_type: str):
    """
    Append a result to the unified JSON file incrementally.
    Organized by violation type.
    """
    # Read existing data
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'configuration': {
                'max_examples_per_type': MAX_EXAMPLES_PER_TYPE,
                'output_filename': OUTPUT_FILENAME
            },
            'total_examples': 0,
            'by_violation_type': {}
        }

    # Initialize violation type if not exists
    if violation_type not in data['by_violation_type']:
        data['by_violation_type'][violation_type] = {
            'results': [],
            'count': 0
        }

    # Append new result to the specific violation type
    data['by_violation_type'][violation_type]['results'].append(result)
    data['by_violation_type'][violation_type]['count'] = len(data['by_violation_type'][violation_type]['results'])

    # Update total count
    data['total_examples'] = sum(v['count'] for v in data['by_violation_type'].values())

    # Write back to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    print(f"  ✓ Result saved to {output_file} ({violation_type}: {data['by_violation_type'][violation_type]['count']}, Total: {data['total_examples']})")


def is_example_successfully_processed(example_id: str, violation_type: str):
    """
    Check if an example has already been successfully processed.
    A query is considered successfully processed if:
    - It exists in the output file
    - api_call_success is True
    - errors list is empty

    Args:
        example_id: ID of the example
        violation_type: Type of violation (SRP, OCP, etc.)

    Returns:
        bool: True if successfully processed, False otherwise
    """
    if not output_file.exists():
        return False

    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if violation type exists
        if violation_type not in data.get('by_violation_type', {}):
            return False

        # Check if example_id exists and is successful
        for result in data['by_violation_type'][violation_type].get('results', []):
            if result.get('example_id') == example_id:
                # Check if it was successfully processed
                api_success = result.get('api_call_success', False)
                errors = result.get('errors', [])

                # Consider successful only if API call succeeded and no errors
                if api_success and len(errors) == 0:
                    return True
                else:
                    # Found but not successful, allow reprocessing
                    return False

        return False

    except Exception as e:
        print(f"  Warning: Could not check existing results: {e}")
        return False


def run_workflow_for_example(example: dict, example_id: str, violation_type: str, idx: int, total: int):
    """
    Run the Coze workflow for a single example and save immediately.
    """
    print(f"\n{'='*80}")
    print(f"Processing [{violation_type}] Example {idx+1}/{total}")
    print(f"  ID: {example_id}")
    print(f"  Level: {example.get('level', 'N/A')}, Language: {example.get('language', 'N/A')}")
    print(f"{'='*80}")

    # Check if already successfully processed
    if is_example_successfully_processed(example_id, violation_type):
        print(f"  ⏭️  Example {example_id} already successfully processed, skipping...")
        return {
            'api_call_success': True,
            'example_id': example_id,
            'skipped': True
        }

    # Prepare parameters for the workflow
    parameters = {
        "input": example.get("input", ""),
        "output": example.get("output", ""),
        "level": example.get("level", ""),
        "language": example.get("language", ""),
        "violation": violation_type,
        "description": example.get("description", "")
    }

    try:
        # Run the workflow
        stream = coze.workflows.runs.stream(
            workflow_id=workflow_id,
            parameters=parameters,
        )

        # Handle the workflow and collect results
        result = handle_workflow_iterator(stream, example_id)

        # Parse coze_response to extract fields
        parsed = parse_coze_response(result['content'])

        # Evaluate detection success
        detection_success = evaluate_detection(
            violation_type,
            parsed['detected_violation_type']
        )

        # Calculate ChrF score for refactoring
        refactor_chrf_score = calculate_chrf_score(
            example.get('output', ''),
            parsed['refactored_code']
        )

        # Determine API call success (no errors)
        api_call_success = len(result['errors']) == 0

        # Build output with proper field ordering
        output = {
            'example_id': example_id,
            'violation_type': violation_type,
            'description': example.get('description', ''),
            'level': example.get('level', ''),
            'language': example.get('language', ''),
            'input': example.get('input', ''),
            'output': example.get('output', ''),
            'coze_response': result['content'],
            'detected_violation_type': parsed['detected_violation_type'],
            'refactored_code': parsed['refactored_code'],
            'detection_success': detection_success,
            'refactor_chrf_score': refactor_chrf_score,
            'api_call_success': api_call_success,
            'errors': result['errors']
        }

        # Print evaluation results
        print(f"  📊 Detection: {'✓ Success' if detection_success else '✗ Failed'} "
              f"(Expected: {violation_type}, Got: {parsed['detected_violation_type']})")
        print(f"  📊 Refactor ChrF: {refactor_chrf_score if refactor_chrf_score is not None else 'N/A'}")
        print(f"  📊 API Call: {'✓ Success' if api_call_success else '✗ Failed'}")

        # Save immediately after receiving response
        save_result_to_file(output, violation_type)

        return output

    except Exception as e:
        print(f"  [Example {example_id}] Exception occurred: {str(e)}")
        output = {
            'example_id': example_id,
            'violation_type': violation_type,
            'description': example.get('description', ''),
            'level': example.get('level', ''),
            'language': example.get('language', ''),
            'input': example.get('input', ''),
            'output': example.get('output', ''),
            'detected_violation_type': None,
            'refactored_code': None,
            'detection_success': False,
            'refactor_chrf_score': None,
            'api_call_success': False,
            'errors': [str(e)]
        }

        # Save error result immediately
        save_result_to_file(output, violation_type)

        return output


def process_all_violations():
    """
    Process all SOLID violation types.
    """
    print(f"\n{'='*80}")
    print("UNIVERSAL SOLID VIOLATIONS BATCH EVALUATION")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  Max examples per type: {MAX_EXAMPLES_PER_TYPE if MAX_EXAMPLES_PER_TYPE else 'All (48 per type)'}")
    print(f"  Output file: {output_file}")
    print(f"  Processing violation types: {', '.join(VIOLATION_TYPES)}")
    print(f"{'='*80}\n")

    overall_stats = {
        'total_successful': 0,
        'total_failed': 0,
        'total_skipped': 0,
        'by_violation': {}
    }

    # Process each violation type
    for violation_type in VIOLATION_TYPES:
        dataset_file = dataset_dir / f'{violation_type.lower()}_violations.json'

        if not dataset_file.exists():
            print(f"⚠️  Warning: Dataset file not found: {dataset_file}")
            continue

        print(f"\n{'='*80}")
        print(f"Processing {violation_type} Violations")
        print(f"{'='*80}")

        # Load the JSON file
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        examples = data.get('code_examples', [])

        # Limit examples if MAX_EXAMPLES_PER_TYPE is set
        if MAX_EXAMPLES_PER_TYPE is not None:
            examples = examples[:MAX_EXAMPLES_PER_TYPE]
            print(f"Limiting to first {MAX_EXAMPLES_PER_TYPE} examples")

        print(f"Processing {len(examples)} {violation_type} examples\n")

        # Initialize stats for this violation type
        stats = {
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }

        # Process each example
        for idx, example in enumerate(examples):
            example_id = f"{violation_type}_{idx+1}"

            result = run_workflow_for_example(example, example_id, violation_type, idx, len(examples))

            if result.get('skipped'):
                stats['skipped'] += 1
            elif result.get('api_call_success', False):
                stats['successful'] += 1
            else:
                stats['failed'] += 1

            # Small delay to avoid rate limiting (skip if example was already processed)
            if not result.get('skipped'):
                time.sleep(1)

            # Progress update
            print(f"  Progress: {idx+1}/{len(examples)} | Success: {stats['successful']} | Failed: {stats['failed']} | Skipped: {stats['skipped']}")

        # Store stats for this violation type
        overall_stats['by_violation'][violation_type] = stats
        overall_stats['total_successful'] += stats['successful']
        overall_stats['total_failed'] += stats['failed']
        overall_stats['total_skipped'] += stats['skipped']

        # Summary for this violation type
        print(f"\n{violation_type} Completed:")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"{'='*80}\n")

    # Final overall summary
    print(f"\n{'='*80}")
    print("OVERALL BATCH EVALUATION COMPLETED")
    print(f"{'='*80}")
    print(f"Total Successful: {overall_stats['total_successful']}")
    print(f"Total Failed: {overall_stats['total_failed']}")
    print(f"Total Skipped: {overall_stats['total_skipped']}")
    print(f"\nBreakdown by Violation Type:")
    for vtype, stats in overall_stats['by_violation'].items():
        print(f"  {vtype}: Success={stats['successful']}, Failed={stats['failed']}, Skipped={stats['skipped']}")
    print(f"\nResults saved to: {output_file}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    print("Starting Universal SOLID Violations Batch Evaluation...\n")
    process_all_violations()
    print("Universal batch evaluation completed!")
