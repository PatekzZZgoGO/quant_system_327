import sys
from pathlib import Path
import argparse
import subprocess

# 修复导入路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.commands.data import register_data_commands

# ========== 命令树定义（需与 register_data_commands 注册的命令保持一致） ==========
COMMAND_TREE = {
    "data": {
        "help": "数据管理相关命令",
        "subcommands": {
            "update": {
                "help": "更新数据",
                "subcommands": {
                    "stocks": {
                        "help": "更新股票数据",
                        "options": [
                            {"name": "--limit", "type": int, "help": "限制更新数量",
                             "prompt": "请输入限制数量（可选，直接回车跳过）: "},
                            {"name": "--force-refresh", "action": "store_true", "help": "强制刷新",
                             "prompt": "是否强制刷新？(y/n): ", "convert": lambda x: x.lower() == 'y'},
                            {"name": "--start-date", "type": str, "help": "起始日期",
                             "prompt": "起始日期 (YYYY-MM-DD，可选): "},
                            {"name": "--end-date", "type": str, "help": "结束日期",
                             "prompt": "结束日期 (YYYY-MM-DD，可选): "},
                            {"name": "--resume", "action": "store_true", "help": "断点续传",
                             "prompt": "是否启用断点续传？(y/n): ", "convert": lambda x: x.lower() == 'y'}
                        ]
                    }
                }
            }
        }
    }
    # 如果有其他模块，可继续添加
}

# ========== 交互函数 ==========
def choose_command(commands, path=None):
    if path is None:
        path = []

    # 显示当前路径
    if path:
        print(f"\n当前路径: {' '.join(path)}")
    else:
        print("\n当前路径: (根)")

    subcommands = list(commands.keys())
    if not subcommands:
        # 叶子节点，返回路径和空选项（后续收集选项）
        return path, {}

    # 列出子命令
    print("可用的子命令:")
    for i, cmd in enumerate(subcommands, 1):
        help_text = commands[cmd].get("help", "")
        print(f"  {i}. {cmd} - {help_text}")
    print("  q. 退出")

    choice = input("请选择命令编号或名称: ").strip()
    if choice.lower() == 'q':
        sys.exit(0)

    # 解析选择
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(subcommands):
            cmd = subcommands[idx]
        else:
            print("无效编号，请重新选择。")
            return choose_command(commands, path)
    else:
        if choice in subcommands:
            cmd = choice
        else:
            print(f"无效命令名 '{choice}'，请重新选择。")
            return choose_command(commands, path)

    node = commands[cmd]
    if "subcommands" in node:
        # 继续深入
        return choose_command(node["subcommands"], path + [cmd])
    else:
        # 叶子节点，收集选项
        options = node.get("options", [])
        option_values = {}
        for opt in options:
            prompt_msg = opt.get("prompt", f"请输入 {opt['name']}: ")
            user_input = input(prompt_msg).strip()
            if not user_input:
                continue
            if opt.get("action") == "store_true":
                # 布尔选项
                if "convert" in opt:
                    value = opt["convert"](user_input)
                else:
                    value = user_input.lower() in ('y', 'yes', 'true', '1')
                if value:
                    option_values[opt["name"]] = True
            else:
                # 普通选项
                if opt.get("type") == int:
                    try:
                        value = int(user_input)
                        option_values[opt["name"]] = value
                    except ValueError:
                        print("输入无效，跳过该选项。")
                        continue
                else:
                    option_values[opt["name"]] = user_input
        return path + [cmd], option_values

def interactive_main():
    cmd_path, opt_values = choose_command(COMMAND_TREE)
    if not cmd_path:
        return

    # 构造完整的命令参数列表
    script_path = Path(__file__).resolve()
    args_list = [sys.executable, str(script_path)] + cmd_path
    for key, value in opt_values.items():
        if isinstance(value, bool):
            if value:
                args_list.append(key)
        else:
            args_list.append(key)
            args_list.append(str(value))

    print(f"\n即将执行: {' '.join(args_list)}")
    confirm = input("确认执行？(y/n): ").strip().lower()
    if confirm == 'y':
        try:
            subprocess.run(args_list, check=True)
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败，返回码: {e.returncode}")
    else:
        print("已取消。")

# ========== 主入口 ==========
def main():
    # 无参数时进入交互模式
    if len(sys.argv) == 1:
        interactive_main()
        return

    # 正常解析命令行参数
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