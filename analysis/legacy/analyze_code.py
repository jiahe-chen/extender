#!/usr/bin/env python3
"""
SOLID Violation Analyzer - 代码分析脚本
========================================

用法:
    # 分析代码字符串
    python analyze_code.py "your code here"

    # 分析文件
    python analyze_code.py -f path/to/file.py

    # 交互模式
    python analyze_code.py -i

    # 详细模式（显示检测过程）
    python analyze_code.py -v "your code here"

    # 从标准输入读取
    echo "code" | python analyze_code.py --stdin

示例:
    python analyze_code.py "class Foo: pass"
    python analyze_code.py -v -f my_code.java
"""

import sys
import argparse
from multi_agent_workflow_demo import MultiAgentWorkflowOrchestrator


def analyze(code: str, verbose: bool = False, show_report: bool = True):
    """分析代码并返回报告"""
    orchestrator = MultiAgentWorkflowOrchestrator(verbose=verbose)
    report = orchestrator.run(code)

    if show_report:
        orchestrator.output_generator.print_report(report)

    return report


def main():
    parser = argparse.ArgumentParser(
        description='SOLID Violation Analyzer - 自动检测代码中的 SOLID 原则违规',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze_code.py "class Foo: pass"
  python analyze_code.py -f my_code.java
  python analyze_code.py -v -f my_code.java   # 详细模式
  python analyze_code.py -i
  cat code.py | python analyze_code.py --stdin
        """
    )

    parser.add_argument('code', nargs='?', help='要分析的代码字符串')
    parser.add_argument('-f', '--file', help='要分析的代码文件路径')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    parser.add_argument('--stdin', action='store_true', help='从标准输入读取代码')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细模式，显示检测过程')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式，只输出结果')

    args = parser.parse_args()

    code = None

    # 优先级: file > stdin > interactive > code argument
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            print(f"[INFO] 已加载文件: {args.file}\n")
        except FileNotFoundError:
            print(f"[ERROR] 文件未找到: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] 读取文件失败: {e}")
            sys.exit(1)

    elif args.stdin:
        code = sys.stdin.read()

    elif args.interactive:
        print("=" * 60)
        print("SOLID Violation Analyzer - 交互模式")
        print("=" * 60)
        print("请输入要分析的代码 (输入 END 结束):\n")

        lines = []
        while True:
            try:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break

        code = '\n'.join(lines)
        print()

    elif args.code:
        # 处理转义字符
        code = args.code.replace('\\n', '\n').replace('\\t', '\t')

    else:
        parser.print_help()
        sys.exit(0)

    if not code or not code.strip():
        print("[ERROR] 未提供代码")
        sys.exit(1)

    # 运行分析
    analyze(code, verbose=args.verbose, show_report=not args.quiet)


if __name__ == '__main__':
    main()
