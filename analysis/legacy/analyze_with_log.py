#!/usr/bin/env python3
"""
SOLID Detection with Detailed Logging - Comprehensive Mode
===========================================================

Runs SOLID detection for ALL 5 principles, saves detailed logs,
and returns the result with highest confidence.

Usage:
    python analyze_with_log.py -f <code_file>
    python analyze_with_log.py "code string"
    python analyze_with_log.py -f test_input.py -o logs/my_analysis.log
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

from multi_agent_workflow_demo import MultiAgentWorkflowOrchestrator

SOLID_PRINCIPLES = ["SRP", "OCP", "LSP", "ISP", "DIP"]


def run_analysis_with_logging(code: str, output_file: str = None, verbose: bool = True):
    """
    Run SOLID analysis for ALL 5 principles and capture all output to a log file.
    Returns the result with highest confidence.

    Args:
        code: The code to analyze
        output_file: Path to save log file (if None, auto-generate)
        verbose: Whether to show verbose output

    Returns:
        tuple: (best_report, log_content, all_reports)
    """
    # Auto-generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        output_file = logs_dir / f"solid_comprehensive_{timestamp}.log"
    else:
        output_file = Path(output_file)
        output_file.parent.mkdir(exist_ok=True, parents=True)

    # Create string buffer to capture output
    log_buffer = StringIO()

    # Storage for all reports
    all_reports = {}

    # Capture both stdout and stderr
    with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
        # Print header
        print("=" * 80)
        print("COMPREHENSIVE SOLID DETECTION - ALL PRINCIPLES")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Code length: {len(code)} characters")
        print(f"Testing principles: {', '.join(SOLID_PRINCIPLES)}")
        print("=" * 80)
        print()

        # Print the code being analyzed
        print("CODE BEING ANALYZED:")
        print("-" * 80)
        print(code)
        print("-" * 80)
        print()

        # Initialize orchestrator
        orchestrator = MultiAgentWorkflowOrchestrator(verbose=verbose)

        # Test each principle separately
        for idx, principle in enumerate(SOLID_PRINCIPLES, 1):
            print("\n\n")
            print("=" * 80)
            print(f"TEST {idx}/{len(SOLID_PRINCIPLES)}: {principle} DETECTION")
            print("=" * 80)
            print()

            # Run analysis for this specific principle
            report = orchestrator._run_sequential(code, principle)
            all_reports[principle] = report

            # Print summary for this principle
            print()
            print("-" * 80)
            print(f"SUMMARY FOR {principle}")
            print("-" * 80)

            # Scenario used
            if hasattr(report, 'scenario') and report.scenario:
                print(f"\nScenario:")
                print(f"  Type: {report.scenario.get('type')}")
                prompt = report.scenario.get('prompt', 'N/A')
                print(f"  Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"  Prompt: {prompt}")

            # Diff metrics
            if hasattr(report, 'metrics'):
                print(f"\nDiff Metrics:")
                print(f"  Lines added: {report.metrics.diff.lines_added}")
                print(f"  Lines removed: {report.metrics.diff.lines_removed}")
                print(f"  Lines changed: {report.metrics.diff.lines_changed}")
                if hasattr(report.metrics, 'changed_classes') and report.metrics.changed_classes:
                    print(f"  Classes changed: {', '.join(report.metrics.changed_classes)}")

            # Violations detected
            print(f"\nViolations Detected: {len(report.violations)}")
            for v in report.violations:
                print(f"  [{v['severity'].upper()}] {v['principle']}")

            # Risk assessment
            print(f"\nRisk Assessment: {report.risk_assessment}")

            # Modified code by LLM for this test
            if hasattr(report, 'modified_code') and report.modified_code:
                print(f"\nModified Code (by LLM) - First 1000 chars:")
                print("  " + "-" * 76)
                modified_preview = report.modified_code[:1000].replace('\n', '\n  ')
                print(f"  {modified_preview}")
                if len(report.modified_code) > 1000:
                    print("  ... (truncated)")
                print("  " + "-" * 76)

            # Full diff for this test
            if hasattr(report, 'diff_text') and report.diff_text:
                print(f"\nFull Diff - First 800 chars:")
                print("  " + "-" * 76)
                diff_preview = report.diff_text[:800].replace('\n', '\n  ')
                print(f"  {diff_preview}")
                if len(report.diff_text) > 800:
                    print("  ... (truncated)")
                print("  " + "-" * 76)

            print("-" * 80)

        # Now determine which result has highest confidence
        print("\n\n")
        print("=" * 80)
        print("CONFIDENCE COMPARISON")
        print("=" * 80)
        print()

        best_principle = None
        best_confidence = 0.0
        best_report = None

        for principle, report in all_reports.items():
            # Extract confidence from risk_assessment string
            # Format: "Low/Medium/High risk (score: X.XX) with XX% confidence"
            import re
            confidence_match = re.search(r'with (\d+)% confidence', report.risk_assessment)
            confidence = float(confidence_match.group(1)) / 100.0 if confidence_match else 0.5

            risk_match = re.search(r'score: ([\d.]+)', report.risk_assessment)
            risk_score = float(risk_match.group(1)) if risk_match else 0.0

            print(f"{principle}:")
            print(f"  Confidence: {confidence:.0%}")
            print(f"  Risk Score: {risk_score:.2f}")
            print(f"  Violations: {len(report.violations)}")
            print()

            if confidence > best_confidence:
                best_confidence = confidence
                best_principle = principle
                best_report = report

        print("=" * 80)
        print(f"BEST RESULT: {best_principle} (Confidence: {best_confidence:.0%})")
        print("=" * 80)
        print()

        # Print the best report in detail
        print("\n")
        print("=" * 80)
        print(f"FINAL REPORT - BASED ON {best_principle} DETECTION")
        print("=" * 80)
        orchestrator.output_generator.print_report(best_report)

        # Print additional details for best result
        print("\n")
        print("=" * 80)
        print(f"ADDITIONAL DETAILS - {best_principle}")
        print("=" * 80)

        if hasattr(best_report, 'scenario') and best_report.scenario:
            print("\nScenario Used:")
            print(f"  Type: {best_report.scenario.get('type')}")
            print(f"  Expected Behavior: {best_report.scenario.get('expected_behavior', 'N/A')}")
            print(f"\n  Full Prompt:")
            print("  " + "-" * 76)
            prompt = best_report.scenario.get('prompt', 'N/A')
            for line in prompt.split('\n'):
                print(f"  {line}")
            print("  " + "-" * 76)
            print(f"\n  Constraints:")
            for constraint in best_report.scenario.get('constraints', []):
                print(f"    - {constraint}")

        if hasattr(best_report, 'modified_code') and best_report.modified_code:
            print("\nModified Code (by LLM):")
            print("-" * 80)
            print(best_report.modified_code[:1000])
            if len(best_report.modified_code) > 1000:
                print("... (truncated, see full diff above)")
            print("-" * 80)

        if hasattr(best_report, 'diff_text') and best_report.diff_text:
            print("\nFull Diff:")
            print("-" * 80)
            print(best_report.diff_text)
            print("-" * 80)

        print("\n")
        print("=" * 80)
        print("END OF COMPREHENSIVE ANALYSIS")
        print("=" * 80)

    # Get log content
    log_content = log_buffer.getvalue()

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(log_content)

    # Also print to console
    print(log_content)
    print(f"\n[INFO] Comprehensive log saved to: {output_file}")

    return best_report, log_content, all_reports


def main():
    parser = argparse.ArgumentParser(
        description='Run comprehensive SOLID detection for all principles and return highest confidence result',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_with_log.py -f test_input.py
  python analyze_with_log.py -f test_input.py -o logs/my_analysis.log
  python analyze_with_log.py "class Foo: pass"
  python analyze_with_log.py -f test_input.py --no-verbose
        """
    )

    parser.add_argument('code', nargs='?', help='Code string to analyze')
    parser.add_argument('-f', '--file', help='Code file to analyze')
    parser.add_argument('-o', '--output', help='Output log file path (default: auto-generate)')
    parser.add_argument('--no-verbose', action='store_true', help='Disable verbose output')

    args = parser.parse_args()

    # Get code
    code = None
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            print(f"[INFO] Loaded file: {args.file}\n")
        except FileNotFoundError:
            print(f"[ERROR] File not found: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to read file: {e}")
            sys.exit(1)
    elif args.code:
        code = args.code.replace('\\n', '\n').replace('\\t', '\t')
    else:
        parser.print_help()
        sys.exit(0)

    if not code or not code.strip():
        print("[ERROR] No code provided")
        sys.exit(1)

    # Run comprehensive analysis with logging
    verbose = not args.no_verbose
    best_report, log_content, all_reports = run_analysis_with_logging(
        code=code,
        output_file=args.output,
        verbose=verbose
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
