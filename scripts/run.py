import sys
from pathlib import Path
import argparse

# ✅ 关键：修复 import 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.commands.data import register_data_commands


def main():
    parser = argparse.ArgumentParser("Quant System CLI")

    subparsers = parser.add_subparsers(dest="module")

    register_data_commands(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()