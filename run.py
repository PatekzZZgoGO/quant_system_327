import logging
logging.basicConfig(level=logging.INFO)
import sys
from pathlib import Path
import argparse
import subprocess
import importlib

# 修复路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


# =========================
# 🧩 UI 命令树（仅展示，不存参数）
# =========================
COMMAND_TREE = {
    "data": {
        "help": "数据管理",
        "subcommands": {
            "update": {
                "help": "更新数据",
                "subcommands": {
                    "stocks": {
                        "help": "更新股票数据"
                    }
                }
            }
        }
    },
    "factor": {
        "help": "因子模块",
        "subcommands": {
            "run": {
                "help": "运行因子选股"
            },
            "ic": {
                "help": "IC 分析",
                "subcommands": {
                    "run": {
                        "help": "计算 IC time series"
                    },
                    "summary": {
                        "help": "IC 统计指标"
                    }
                }
            }
        }
    }
}


# =========================
# 🚀 自动注册 commands（插件系统）
# =========================
def auto_register_commands(subparsers):
    commands_path = PROJECT_ROOT / "scripts" / "commands"

    for file in commands_path.glob("*.py"):
        if file.name.startswith("_"):
            continue

        module_name = f"scripts.commands.{file.stem}"

        try:
            module = importlib.import_module(module_name)

            if hasattr(module, "register"):
                module.register(subparsers)
                print(f"[✔] Loaded command: {file.stem}")
            else:
                print(f"[WARN] {file.stem} has no register()")

        except Exception as e:
            print(f"[ERROR] Failed loading {file.stem}: {e}")


# =========================
# 🧠 UI 选择命令（只负责路径）
# =========================
def choose_command(commands, path=None):
    if path is None:
        path = []

    print("\n当前路径:", " ".join(path) if path else "(root)")

    keys = list(commands.keys())

    for i, k in enumerate(keys, 1):
        print(f"{i}. {k} - {commands[k].get('help', '')}")
    print("q. 退出")

    choice = input("选择命令: ").strip()

    if choice == 'q':
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
    else:
        return path + [key]


# =========================
# 🚀 交互入口（UI + CLI 参数）
# =========================
def interactive_main():
    cmd_path = choose_command(COMMAND_TREE)

    if not cmd_path:
        return

    print(f"\n👉 已选择命令: {' '.join(cmd_path)}")

    # =========================
    # 🧠 构建 parser（关键）
    # =========================
    parser = argparse.ArgumentParser("Quant System CLI")
    subparsers = parser.add_subparsers(dest="module")

    auto_register_commands(subparsers)

    # =========================
    # 🧠 找到对应子 parser
    # =========================
    current_parser = parser

    for cmd in cmd_path:
        actions = [
            a for a in current_parser._actions
            if isinstance(a, argparse._SubParsersAction)
        ]

        if not actions:
            break

        subparser_action = actions[0]

        if cmd in subparser_action.choices:
            current_parser = subparser_action.choices[cmd]
        else:
            break

    # =========================
    # 🧠 读取参数定义并交互输入
    # =========================
    args_list = cmd_path.copy()

    for action in current_parser._actions:
        if not action.option_strings:
            continue

        arg_name = action.option_strings[0]

        # 👉 跳过 help
        if arg_name in ("-h", "--help"):
            continue

        default = action.default
        required = action.required

        # =========================
        # 🧠 构造 prompt
        # =========================
        if required:
            prompt = f"请输入 {arg_name} (必填): "
        else:
            prompt = f"请输入 {arg_name} [默认={default}]: "

        user_input = input(prompt).strip()

        if not user_input:
            if required:
                print("❌ 必填参数不能为空")
                return
            else:
                continue

        # =========================
        # 类型转换
        # =========================
        if action.type == int:
            try:
                user_input = int(user_input)
            except ValueError:
                print("❌ 输入必须是整数")
                return

        args_list.append(arg_name)
        args_list.append(str(user_input))

    # =========================
    # 🚀 执行
    # =========================
    cmd = [sys.executable, str(Path(__file__).resolve())] + args_list

    print(f"\n🚀 即将执行:\n{' '.join(cmd)}")

    confirm = input("确认执行？(y/n): ").strip().lower()

    if confirm == 'y':
        subprocess.run(cmd)
    else:
        print("已取消")

# =========================
# 🧠 主入口（CLI）
# =========================
def main():
    # 👉 无参数 → UI模式
    if len(sys.argv) == 1:
        interactive_main()
        return

    parser = argparse.ArgumentParser("Quant System CLI")

    subparsers = parser.add_subparsers(dest="module")

    # 👉 自动加载所有 commands
    auto_register_commands(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()