"""
CLI entry points for poly_ren

Provides command-line interface for Renpy text extraction and merging.
"""

def extract_cli():
    """CLI entry point for extraction"""
    from poly_ren.extract import main
    main()


def merge_cli():
    """CLI entry point for merging"""
    from poly_ren.merge import main
    main()


def main():
    """Main CLI dispatcher"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Renpy Translation Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  extract    Extract translatable text from .rpy files
  merge      Merge translated text back into .rpy files
        """
    )

    parser.add_argument(
        'command',
        choices=['extract', 'merge'],
        help='Command to run'
    )

    args, remaining = parser.parse_known_args()

    # Replace sys.argv for the subcommand
    sys.argv = [f'poly-ren-{args.command}'] + remaining

    if args.command == 'extract':
        extract_cli()
    elif args.command == 'merge':
        merge_cli()


if __name__ == '__main__':
    main()
