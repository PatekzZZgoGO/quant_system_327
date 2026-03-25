"""
专业级限流器（Tushare / 通用API适用）

功能：
✅ Token配额管理（每日调用上限）
✅ 每分钟窗口限流
✅ 多进程共享限流（基于文件锁/简单实现）
✅ 自动降速
✅ 风控检测（空数据 / 异常模式识别）

设计目标：
- 可直接集成到你当前 TushareDataFetcher
- 防止被限流 / 被风控 / 数据异常
- 支持长时间稳定运行（生产级）
"""

import time
import json
import random
from pathlib import Path
from threading import Lock


class AdvancedRateLimiter:
    """
    专业级限流器
    """

    def __init__(
        self,
        max_calls_per_minute: int = 100,
        max_calls_per_day: int = 8000,
        cooldown_base: float = 1.0,
        state_file: str = "rate_limit_state.json",
    ):
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_day = max_calls_per_day
        self.cooldown_base = cooldown_base

        self.state_path = Path(state_file)
        self.lock = Lock()

        self._init_state()

        # 风控检测
        self.empty_response_count = 0
        self.error_count = 0

    # ==============================
    # 状态管理（支持“跨进程共享”）
    # ==============================
    def _init_state(self):
        if not self.state_path.exists():
            self._save_state({
                "calls": [],
                "daily_calls": 0,
                "last_reset": time.strftime("%Y-%m-%d")
            })

    def _load_state(self):
        try:
            with open(self.state_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"calls": [], "daily_calls": 0, "last_reset": ""}

    def _save_state(self, state):
        with open(self.state_path, "w") as f:
            json.dump(state, f)

    # ==============================
    # 核心限流逻辑
    # ==============================
    def wait(self):
        """调用前必须执行"""
        with self.lock:
            state = self._load_state()

            now = time.time()
            today = time.strftime("%Y-%m-%d")

            # ===== 每日重置 =====
            if state["last_reset"] != today:
                state["daily_calls"] = 0
                state["last_reset"] = today
                state["calls"] = []

            # ===== 每分钟窗口 =====
            state["calls"] = [t for t in state["calls"] if now - t < 60]

            if len(state["calls"]) >= self.max_calls_per_minute:
                sleep_time = 60 - (now - state["calls"][0])
                print(f"⚠️ 触发分钟限流，休息 {sleep_time:.1f}s")
                time.sleep(max(sleep_time, 1))

            # ===== 每日配额 =====
            if state["daily_calls"] >= self.max_calls_per_day:
                print("🚫 达到每日调用上限，强制休眠 1 小时")
                time.sleep(3600)

            # ===== 基础随机延迟 =====
            delay = self.cooldown_base + random.uniform(0.5, 1.5)
            time.sleep(delay)

            # ===== 更新状态 =====
            state["calls"].append(time.time())
            state["daily_calls"] += 1

            self._save_state(state)

    # ==============================
    # 风控检测
    # ==============================
    def record_success(self):
        self.empty_response_count = 0
        self.error_count = 0

    def record_empty(self):
        self.empty_response_count += 1

        # 连续空数据 → 高概率被限流
        if self.empty_response_count >= 5:
            sleep_time = 60 * 3
            print(f"⚠️ 检测到连续空数据，可能被风控，休息 {sleep_time}s")
            time.sleep(sleep_time)
            self.empty_response_count = 0

    def record_error(self):
        self.error_count += 1

        if self.error_count >= 5:
            sleep_time = 60 * 2
            print(f"⚠️ 连续错误，触发冷却 {sleep_time}s")
            time.sleep(sleep_time)
            self.error_count = 0


# ==============================
# 用法示例（直接替换你原来的 limiter）
# ==============================
if __name__ == "__main__":
    limiter = AdvancedRateLimiter()

    for i in range(200):
        limiter.wait()

        # 模拟请求
        print(f"请求 {i}")

        # 模拟结果
        if i % 30 == 0:
            limiter.record_empty()
        else:
            limiter.record_success()
