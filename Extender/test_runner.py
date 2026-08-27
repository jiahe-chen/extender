#!/usr/bin/env python3
"""
Run Top 30 Longest Code Examples
=================================

This script runs only the top 30 longest code examples from the dataset
based on the code length analysis report.

Usage:
    python run_top30_longest.py
"""

import json
import re
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import from benchmark runner
from benchmark_runner_langgraph import (
    create_workflow,
    process_example,
    setup_output_directory,
    init_langgraph_client,
    print_progress_bar
)

from benchmark_config import (
    MODEL_SELECTION,
    WORKFLOW_TYPE,
    OUTPUT_FILENAME,
    DATASET_DIR,
    ENABLE_STRUCTURAL_ANALYSIS,  # V7: Import structural analysis config
    TOP_N,  # V8: Import top-n detection config
    validate_config,
    print_config_summary
)

# ============================================================================
# TOP 30 LONGEST EXAMPLES (from code_length_analysis_report.txt)
# ============================================================================

# TOP_30_LONGEST = [
#     ("ISP", 7),   # ISP_7 - 17,075 chars
#     ("SRP", 12),  # SRP_12 - 16,985 chars
#     ("SRP", 48),  # SRP_48 - 16,946 chars
#     ("OCP", 7),   # OCP_7 - 16,149 chars
#     ("OCP", 8),   # OCP_8 - 15,864 chars
#     ("OCP", 5),   # OCP_5 - 15,744 chars
#     ("ISP", 19),  # ISP_19 - 15,667 chars
#     ("OCP", 17),  # OCP_17 - 15,628 chars
#     ("OCP", 20),  # OCP_20 - 15,513 chars
#     ("OCP", 19),  # OCP_19 - 14,950 chars
#     ("LSP", 36),  # LSP_36 - 14,758 chars
#     ("SRP", 36),  # SRP_36 - 14,620 chars
#     ("SRP", 24),  # SRP_24 - 14,413 chars
#     ("ISP", 31),  # ISP_31 - 13,948 chars
#     ("SRP", 47),  # SRP_47 - 13,890 chars
#     ("ISP", 43),  # ISP_43 - 13,827 chars
#     ("SRP", 10),  # SRP_10 - 13,357 chars
#     ("SRP", 46),  # SRP_46 - 13,000 chars
#     ("SRP", 22),  # SRP_22 - 12,992 chars
#     ("LSP", 35),  # LSP_35 - 12,785 chars
#     ("SRP", 9),   # SRP_9 - 12,738 chars
#     ("SRP", 11),  # SRP_11 - 12,494 chars
#     ("LSP", 34),  # LSP_34 - 12,199 chars
#     ("SRP", 45),  # SRP_45 - 12,158 chars
#     ("OCP", 41),  # OCP_41 - 11,987 chars
#     ("ISP", 18),  # ISP_18 - 11,756 chars
#     ("OCP", 32),  # OCP_32 - 11,644 chars
#     ("ISP", 5),   # ISP_5 - 11,621 chars
#     ("OCP", 44),  # OCP_44 - 11,552 chars
#     ("ISP", 17),  # ISP_17 - 11,445 chars
# ]


TOP_30_LONGEST = [
    ("SRP", 1),   # ISP_7 - 17,075 chars
    ("SRP", 2),  # SRP_12 - 16,985 chars
    ("SRP", 3),  # SRP_48 - 16,946 chars
    # ("SRP", 4),   # OCP_7 - 16,149 chars
    # ("SRP", 5),   # OCP_8 - 15,864 chars
    # ("SRP", 6),   # OCP_5 - 15,744 chars
    # ("SRP", 7),  # ISP_19 - 15,667 chars
    # ("SRP", 8),   # OCP_17 - 15,628 chars
    # ("SRP", 9),   # OCP_20 - 15,513 chars
    # ("SRP", 10),  # OCP_19 - 14,950 chars
    ("OCP", 1),  # OCP_17 - 15,628 chars
    ("OCP", 2),  # OCP_5 - 15,744 chars
    ("OCP", 3),  # OCP_7 - 16,149 chars
    # ("OCP", 4),  # OCP_8 - 15,864 chars
    # ("OCP", 5),  # OCP_5 - 15,744 chars
    # ("OCP", 6),  # OCP_7 - 16,149 chars
    # ("OCP", 7),  # OCP_8 - 15,864 chars
    # ("OCP", 8),  # OCP_5 - 15,744 chars
    # ("OCP", 9),  # ISP_19 - 15,667 chars
    # ("OCP", 10),  # OCP_17 - 15,628 chars
    ("LSP", 1),  # SRP_36 - 14,620 chars
    ("LSP", 2),  # SRP_36 - 14,620 chars
    ("LSP", 3),  # SRP_36 - 14,620 chars
    # ("LSP", 4),  # SRP_36 - 14,620 chars
    # ("LSP", 5),  # SRP_36 - 14,620 chars
    # ("LSP", 6),  # SRP_36 - 14,620 chars
    # ("LSP", 7),  # SRP_36 - 14,620 chars
    # ("LSP", 8),  # SRP_36 - 14,620 chars
    # ("LSP", 9),  # SRP_36 - 14,620 chars
    # ("LSP", 10), # SRP_36 - 14,620 chars
    ("ISP", 1),  # ISP_31 - 13,948 chars
    ("ISP", 2),  # ISP_31 - 13,948 chars
    ("ISP", 3),  # ISP_31 - 13,948 chars
    # ("ISP", 4),  # ISP_31 - 13,948 chars
    # ("ISP", 5),  # ISP_31 - 13,948 chars
    # ("ISP", 6),  # ISP_31 - 13,948 chars
    # ("ISP", 7),  # ISP_31 - 13,948 chars
    # ("ISP", 8),  # ISP_31 - 13,948 chars
    # ("ISP", 9),  # ISP_31 - 13,948 chars
    # ("ISP", 10), # ISP_31 - 13,948 chars
    ("DIP", 1),  # LSP_35 - 12,785 chars
    ("DIP", 2),  # LSP_35 - 12,785 chars
    ("DIP", 3),  # LSP_35 - 12,785 chars
    # ("DIP", 4),  # LSP_35 - 12,785 chars
    # ("DIP", 5),  # LSP_35 - 12,785 chars
    # ("DIP", 6),  # LSP_35 - 12,785 chars
    # ("DIP", 7),  # LSP_35 - 12,785 chars
    # ("DIP", 8),  # LSP_35 - 12,785 chars
    # ("DIP", 9),  # LSP_35 - 12,785 chars
    # ("DIP", 10), # LSP_35 - 12,785 chars
]

# TOP_30_LONGEST = [
#     ("SRP", 1),   # ISP_7 - 17,075 chars
#     ("SRP", 2),  # SRP_12 - 16,985 chars
#     ("SRP", 3),  # SRP_48 - 16,946 chars
#     ("SRP", 4),   # OCP_7 - 16,149 chars
#     ("SRP", 5),   # OCP_8 - 15,864 chars
#     ("OCP", 1),  # OCP_17 - 15,628 chars
#     ("OCP", 2),  # OCP_5 - 15,744 chars
#     ("OCP", 3),  # OCP_7 - 16,149 chars
#     ("OCP", 4),  # OCP_8 - 15,864 chars
#     ("OCP", 5),  # OCP_5 - 15,744 chars
#     ("LSP", 1),  # SRP_36 - 14,620 chars
#     ("LSP", 2),  # SRP_36 - 14,620 chars
#     ("LSP", 3),  # SRP_36 - 14,620 chars
#     ("LSP", 4),  # SRP_36 - 14,620 chars
#     ("LSP", 5),  # SRP_36 - 14,620 chars
#     ("ISP", 1),  # ISP_31 - 13,948 chars
#     ("ISP", 2),  # ISP_31 - 13,948 chars
#     ("ISP", 3),  # ISP_31 - 13,948 chars
#     ("ISP", 4),  # ISP_31 - 13,948 chars
#     ("ISP", 5),  # ISP_31 - 13,948 chars
#     ("DIP", 1),  # LSP_35 - 12,785 chars
#     ("DIP", 2),  # LSP_35 - 12,785 chars
#     ("DIP", 3),  # LSP_35 - 12,785 chars
#     ("DIP", 4),  # LSP_35 - 12,785 chars
#     ("DIP", 5),  # LSP_35 - 12,785 chars
# ]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_dataset(violation_type: str) -> Dict:
    """Load dataset for a specific violation type"""
    dataset_file = Path(DATASET_DIR) / f'{violation_type.lower()}_violations.json'

    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}")

    with open(dataset_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_example_by_index(violation_type: str, index: int) -> Optional[Dict]:
    """Get a specific example by violation type and index (1-based)"""
    data = load_dataset(violation_type)
    examples = data.get('code_examples', [])

    # Convert to 0-based index
    array_index = index - 1

    if 0 <= array_index < len(examples):
        return examples[array_index]
    else:
        print(f"[WARN] Example {violation_type}_{index} not found (index out of range)")
        return None


def run_top30_longest():
    """Run benchmark for top 30 longest code examples"""

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
    print("RUN TOP 30 LONGEST CODE EXAMPLES")
    print("="*80)
    print_config_summary()
    print(f"\nTotal examples to process: {len(TOP_30_LONGEST)}")
    print("="*80)

    # Initialize LangGraph client
    if not init_langgraph_client():
        return 1

    print()

    # Overall stats
    overall_start_time = time.time()
    total_successful = 0
    total_failed = 0
    total_skipped = 0

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

        model_start_time = time.time()
        model_successful = 0
        model_failed = 0
        model_skipped = 0

        # Process each example in top 30
        for idx, (violation_type, example_num) in enumerate(TOP_30_LONGEST, 1):
            example_id = f"{violation_type}_{example_num}"

            # Progress bar
            prefix = f"[Top 30]"
            suffix = f"({idx}/{len(TOP_30_LONGEST)}) {example_id}"
            print_progress_bar(idx-1, len(TOP_30_LONGEST), prefix=prefix, suffix=suffix)

            # Load example
            example = get_example_by_index(violation_type, example_num)
            if not example:
                print(f"\n[SKIP] {example_id} - Example not found")
                model_skipped += 1
                continue

            # Get code length for logging
            code_length = len(example.get('input', ''))
            print(f"\n[{idx}/{len(TOP_30_LONGEST)}] Processing {example_id} ({code_length:,} chars)")

            # Process example
            try:
                result = process_example(
                    workflow=workflow,
                    example=example,
                    example_id=example_id,
                    violation_type=violation_type,
                    output_file=output_file,
                    model_name=model_name
                )

                if result.get('skipped'):
                    model_skipped += 1
                    print(f"  [SKIP] Already processed")
                elif result.get('api_call_success', False):
                    model_successful += 1
                    detection_success = result.get('detection_success', False)
                    status = "✓ CORRECT" if detection_success else "✗ INCORRECT"
                    print(f"  [OK] {status}")
                else:
                    model_failed += 1
                    print(f"  [FAIL] Processing failed")

                # Delay between requests
                if not result.get('skipped'):
                    time.sleep(2)  # 2 second delay

            except Exception as e:
                print(f"  [ERROR] {e}")
                model_failed += 1

        # Complete progress bar
        print_progress_bar(len(TOP_30_LONGEST), len(TOP_30_LONGEST),
                          prefix='[Top 30]',
                          suffix='Complete!')

        model_elapsed_time = time.time() - model_start_time

        # Model summary
        print(f"\n{'='*80}")
        print(f"MODEL {model_name} COMPLETED")
        print(f"{'='*80}")
        print(f"Time: {model_elapsed_time/60:.2f} minutes")
        print(f"Successful: {model_successful}")
        print(f"Failed: {model_failed}")
        print(f"Skipped: {model_skipped}")
        print(f"\nResults saved to: {output_file}")
        print(f"{'='*80}\n")

        total_successful += model_successful
        total_failed += model_failed
        total_skipped += model_skipped

        # Small delay between models
        if model_idx < len(MODEL_SELECTION):
            print("Waiting 5 seconds before next model...\n")
            time.sleep(5)

    overall_elapsed_time = time.time() - overall_start_time

    # Final summary
    print(f"\n{'='*80}")
    print("TOP 30 LONGEST EXAMPLES COMPLETED")
    print(f"{'='*80}")
    print(f"Total Time: {overall_elapsed_time/60:.2f} minutes")
    print(f"Total Examples: {len(TOP_30_LONGEST)}")
    print(f"Successful: {total_successful}")
    print(f"Failed: {total_failed}")
    print(f"Skipped: {total_skipped}")
    print(f"{'='*80}\n")

    return 0


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    sys.exit(run_top30_longest())