"""
CLI entry points for poly_bench

Provides command-line interface for model comparison and benchmarking.
"""

import sys
from pathlib import Path

# Add src directory to path for imports during transition
sys.path.insert(0, str(Path(__file__).parent.parent))


def compare_cli():
    """CLI entry point for model comparison (speed test)"""
    from src.poly_bench.compare import main
    main()


def benchmark_cli():
    """CLI entry point for model benchmarking (BLEU quality test)"""
    from src.poly_bench.benchmark import main
    main()


def main():
    """Main CLI dispatcher"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Translation Model Comparison and Benchmarking Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  compare     Compare translation speed across all models
  benchmark   Benchmark translation quality using BLEU scores
        """
    )

    parser.add_argument(
        'command',
        choices=['compare', 'benchmark'],
        help='Command to run'
    )

    args, remaining = parser.parse_known_args()

    # Replace sys.argv for the subcommand
    sys.argv = [f'poly-bench-{args.command}'] + remaining

    if args.command == 'compare':
        compare_cli()
    elif args.command == 'benchmark':
        benchmark_cli()


if __name__ == '__main__':
    main()
