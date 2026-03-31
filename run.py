"""Unified CLI entrypoint.

This file stays as a thin compatibility entry layer during the shared/trading
pre-split phase. It should remain focused on command discovery, registration,
dispatch, and interactive argument collection.

New business orchestration should prefer pipeline/application layers instead of
growing directly in this file.
"""

import argparse
import importlib
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

COMMAND_TREE = {
    "data": {
        "help": "数据管理",
        "subcommands": {
            "update": {
                "help": "更新数据",
                "subcommands": {
                    "stock": {"help": "更新单只股票"},
                    "stocks": {"help": "批量更新股票"},
                },
            },
            "status": {
                "help": "查看数据状态",
                "subcommands": {
                    "cache": {"help": "查看缓存状态"},
                },
            },
        },
    },
    "factor": {
        "help": "因子分析",
        "subcommands": {
            "run": {"help": "运行因子选股"},
        },
    },
    "ic": {
        "help": "IC 分析",
    },
    "backtest": {
        "help": "回测",
        "subcommands": {
            "run": {"help": "运行回测"},
        },
    },
}


def auto_register_commands(subparsers) -> None:
    commands_path = PROJECT_ROOT / "scripts" / "commands"

    for file in commands_path.glob("*.py"):
        if file.name.startswith("_"):
            continue

        module_name = f"scripts.commands.{file.stem}"

        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "register"):
                module.register(subparsers)
                print(f"[OK] Loaded command: {file.stem}")
            else:
                print(f"[WARN] {file.stem} has no register()")
        except Exception as exc:
            print(f"[ERROR] Failed loading {file.stem}: {exc}")


def choose_command(commands, path=None):
    if path is None:
        path = []

    print("\n当前路径:", " ".join(path) if path else "(root)")
    keys = list(commands.keys())

    for index, key in enumerate(keys, start=1):
        print(f"{index}. {key} - {commands[key].get('help', '')}")
    print("q. 退出")

    choice = input("选择命令: ").strip()
    if choice == "q":
        sys.exit(0)

    if choice.isdigit():
        idx = int(choice) - 1
        if idx < 0 or idx >= len(keys):
            return choose_command(commands, path)
        key = keys[idx]
    else:
        if choice not in keys:
            return choose_command(commands, path)
        key = choice

    node = commands[key]
    if "subcommands" in node:
        return choose_command(node["subcommands"], path + [key])
    return path + [key]


def _find_parser_for_path(parser: argparse.ArgumentParser, cmd_path):
    current_parser = parser

    for cmd in cmd_path:
        actions = [action for action in current_parser._actions if isinstance(action, argparse._SubParsersAction)]
        if not actions:
            break

        subparser_action = actions[0]
        if cmd not in subparser_action.choices:
            break
        current_parser = subparser_action.choices[cmd]

    return current_parser


def _prompt_optional_value(arg_name: str, default) -> str:
    default_text = "" if default in (None, argparse.SUPPRESS) else f" [默认={default}]"
    return input(f"请输入 {arg_name}{default_text}: ").strip()


def _build_args_interactively(current_parser: argparse.ArgumentParser, cmd_path):
    args_list = list(cmd_path)

    for action in current_parser._actions:
        if not action.option_strings:
            continue

        arg_name = action.option_strings[0]
        if arg_name in ("-h", "--help"):
            continue

        if isinstance(action, argparse._StoreTrueAction):
            enabled = input(f"是否启用 {arg_name}？[y/N]: ").strip().lower()
            if enabled in {"y", "yes"}:
                args_list.append(arg_name)
            continue

        if isinstance(action, argparse._StoreFalseAction):
            disabled = input(f"是否关闭 {arg_name}？[y/N]: ").strip().lower()
            if disabled in {"y", "yes"}:
                args_list.append(arg_name)
            continue

        if action.required:
            user_input = input(f"请输入 {arg_name}（必填）: ").strip()
            if not user_input:
                print(f"[ERROR] {arg_name} 为必填项。")
                return None
        else:
            user_input = _prompt_optional_value(arg_name, action.default)
            if not user_input:
                continue

        if action.nargs in ("+", "*"):
            values = user_input.split()
            if action.required and not values:
                print(f"[ERROR] {arg_name} 至少需要一个值。")
                return None
            args_list.append(arg_name)
            args_list.extend(values)
            continue

        if action.type == int:
            try:
                int(user_input)
            except ValueError:
                print(f"[ERROR] {arg_name} 必须是整数。")
                return None

        if action.type == float:
            try:
                float(user_input)
            except ValueError:
                print(f"[ERROR] {arg_name} 必须是浮点数。")
                return None

        args_list.append(arg_name)
        args_list.append(user_input)

    return args_list


def interactive_main() -> None:
    cmd_path = choose_command(COMMAND_TREE)
    if not cmd_path:
        return

    print(f"\n已选择命令: {' '.join(cmd_path)}")

    parser = argparse.ArgumentParser("Quant System CLI")
    subparsers = parser.add_subparsers(dest="module")
    auto_register_commands(subparsers)

    current_parser = _find_parser_for_path(parser, cmd_path)
    args_list = _build_args_interactively(current_parser, cmd_path)
    if args_list is None:
        return

    cmd = [sys.executable, str(Path(__file__).resolve())] + args_list
    print(f"\n即将执行:\n{' '.join(cmd)}")

    confirm = input("确认执行？[y/N]: ").strip().lower()
    if confirm == "y":
        subprocess.run(cmd, check=False)
    else:
        print("已取消。")


def main() -> None:
    if len(sys.argv) == 1:
        interactive_main()
        return

    parser = argparse.ArgumentParser("Quant System CLI")
    subparsers = parser.add_subparsers(dest="module")
    auto_register_commands(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    main()
