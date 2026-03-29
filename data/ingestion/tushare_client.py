# data/ingestion/tushare_client.py
"""
A 股数据获取模块（Tushare Pro 版）
基于智能限流 + 多层级错误恢复 + 智能缓存 + 监控告警
需要 Tushare Token 和 120 积分
"""
import os
import sys
import time
import random
import logging
import pickle
import builtins
from datetime import datetime, timedelta
from collections import deque
from typing import List, Dict, Optional, Tuple
from threading import Lock
from pathlib import Path
from data.ingestion.rate_limiter.advanced_rate_limiter import AdvancedRateLimiter

import pandas as pd

# 项目导入
from infra.config import config
from infra.logging.logger import get_logger

# 获取配置
TUSHARE_TOKEN = config.get('tushare.token', '')
REQUEST_DELAY = config.get('tushare.request_delay', 1.0)
MAX_RETRIES = config.get('tushare.max_retries', 5)
CACHE_EXPIRY_DAYS = config.get('tushare.cache_expiry_days', 1)

# 数据目录定义
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'datasets'
DATA_RAW_DIR = DATA_DIR / 'raw'
DATA_PROCESSED_DIR = DATA_DIR / 'processed'
DATA_CACHE_DIR = DATA_DIR / 'cache'
DATA_STOCKS_DIR = DATA_PROCESSED_DIR / 'stocks'
STOCK_LIST_PATH = DATA_PROCESSED_DIR / 'stock_list.csv'

# 初始化日志
logger = get_logger(__name__)


def print(*args, **kwargs):
    try:
        return builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe_args = [
            str(arg).encode(encoding, errors="ignore").decode(encoding, errors="ignore")
            for arg in args
        ]
        return builtins.print(*safe_args, **kwargs)


def ensure_directories():
    """确保所有数据目录存在"""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_STOCKS_DIR.mkdir(parents=True, exist_ok=True)
    STOCK_LIST_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 智能限流系统
# ============================================================================
class SmartRateLimiter:
    """智能请求调控系统"""
    def __init__(self, window_size: int = 10, min_interval: float = 1.0):
        self.request_timestamps = deque(maxlen=window_size)
        self.min_interval = min_interval
        self._lock = Lock()

    def get_delay(self) -> float:
        with self._lock:
            if len(self.request_timestamps) < 2:
                return random.uniform(0.5, 1.0)
            timestamps = list(self.request_timestamps)
            recent_intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            avg_interval = sum(recent_intervals) / len(recent_intervals)
            if avg_interval < self.min_interval:
                return self.min_interval + random.uniform(0.5, 1.5)
            return random.uniform(0.8, 1.2)

    def wait(self):
        delay = self.get_delay()
        time.sleep(delay)
        with self._lock:
            self.request_timestamps.append(time.time())

    def reset(self):
        with self._lock:
            self.request_timestamps.clear()


# ============================================================================
# 多层级错误恢复获取器
# ============================================================================
class ResilientTushareFetcher:
    def __init__(self, pro_api, max_attempts: int = 5, base_delay: float = 1.0):
        self.pro = pro_api
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.rate_limiter = AdvancedRateLimiter(
            max_calls_per_minute=100,   # 保守值（建议先低一点）
            max_calls_per_day=8000      # 根据你积分调
        )

    def _validate_data(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        if df is None or len(df) == 0:
            return False
        return all(col in df.columns for col in required_columns)

    def _normalize_request_params(self, ts_code: str, start_date: str, end_date: str) -> Tuple[str, str, str]:
        return (
            str(ts_code).strip(),
            str(start_date).replace('-', ''),
            str(end_date).replace('-', ''),
        )

    def _is_auth_error(self, error_msg: str) -> bool:
        error_msg_lower = error_msg.lower()
        return '权限' in error_msg or '积分' in error_msg or 'token' in error_msg_lower

    def _get_retry_delay(self, attempt: int) -> float:
        backoff = self.base_delay * (2 ** attempt)
        jitter = random.uniform(0.5, 1.5)
        return min(30.0, backoff + jitter)

    def fetch_daily_with_retry(self, ts_code: str, start_date: str, end_date: str,
                            max_attempts: int = None) -> Optional[pd.DataFrame]:
        """
        获取日线数据（生产级增强版）

        🔥 核心能力：
        - 强制类型安全（避免 int / numpy 类型污染）
        - 智能限流（分钟 + 每日 + 随机延迟）
        - 风控检测（空数据识别 = 高概率被限流）
        - 自动降速（连续错误 / 空数据）
        - 多层重试机制（指数退避）

        ⚠️ 为什么要这么复杂？
        因为 Tushare 限制不是简单“频率”，而是：
        - 请求速率
        - 请求总量
        - 行为模式（连续抓全市场）

        👉 这个函数就是专门对抗这些限制的
        """

        max_attempts = max_attempts or self.max_attempts
        required_columns = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']

        # =========================
        # ✅ 强制类型清洗（极其关键）
        # =========================
        ts_code, start_date, end_date = self._normalize_request_params(ts_code, start_date, end_date)

        for attempt in range(max_attempts):
            failure_recorded = False
            try:
                # =========================
                # 🧠 专业限流器（核心）
                # =========================
                self.rate_limiter.wait()

                # debug（只打印第一次，避免刷屏）
                if attempt == 0:
                    logger.debug(
                        f"[Tushare] 请求参数: {ts_code}, {start_date}, {end_date}"
                    )

                # =========================
                # 📡 实际 API 调用
                # =========================
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )

                # =========================
                # 🚨 风控检测（重点！！！）
                # =========================
                if df is None or df.empty:
                    # 👉 很多时候不是“没数据”，而是“被限流”
                    self.rate_limiter.record_empty()
                    failure_recorded = True


                    raise ValueError("返回空数据（可能触发Tushare限流/风控）")

                # =========================
                # ✅ 数据结构校验
                # =========================
                if not self._validate_data(df, required_columns):
                    self.rate_limiter.record_error()
                    failure_recorded = True

                    raise ValueError("返回数据不完整或字段缺失")

                # =========================
                # 🎯 成功（重置风控计数）
                # =========================
                self.rate_limiter.record_success()

                return df

            except Exception as e:
                if not failure_recorded:
                    self.rate_limiter.record_error()
                error_msg = str(e)

                # =========================
                # 🔍 Debug：打印真实类型（查隐藏 bug）
                # =========================
                logger.error(
                    f"[DEBUG] ts_code={ts_code} ({type(ts_code)}), "
                    f"start_date={start_date} ({type(start_date)}), "
                    f"end_date={end_date} ({type(end_date)})"
                )

                # =========================
                # 🚨 权限类错误（直接停止）
                # =========================
                if 'token' in error_msg.lower() or 'permission' in error_msg.lower() or 'point' in error_msg.lower():
                    logger.error(f"Auth or token error, stop retrying: {error_msg}")
                    return None

                # =========================
                # 📉 风控记录（错误）
                # =========================
                if not failure_recorded:
                    self.rate_limiter.record_error()

                # =========================
                # 🔁 指数退避重试
                # =========================
                if attempt < max_attempts - 1:
                    wait_time = self._get_retry_delay(attempt)

                    logger.warning(
                        f"Attempt {attempt + 1} failed, retry in {wait_time:.1f}s | "
                        f"error: {error_msg[:80]}"
                    )

                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} attempts failed: {error_msg}")
                    return None

        return None

    def fetch_daily_basic_with_retry(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        max_attempts: int = None
    ) -> Optional[pd.DataFrame]:

        max_attempts = max_attempts or self.max_attempts

        ts_code, start_date, end_date = self._normalize_request_params(ts_code, start_date, end_date)

        required_columns = ['ts_code', 'trade_date', 'total_mv']

        for attempt in range(max_attempts):
            failure_recorded = False
            try:
                self.rate_limiter.wait()

                df = self.pro.daily_basic(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,trade_date,total_mv,circ_mv,turnover_rate,pe'
                )

                # 🚨 风控检测
                if df is None or df.empty:
                    self.rate_limiter.record_empty()
                    raise ValueError("daily_basic 返回空数据（可能限流）")

                if not all(col in df.columns for col in required_columns):
                    self.rate_limiter.record_error()
                    raise ValueError("daily_basic 字段缺失")

                self.rate_limiter.record_success()
                return df

            except Exception as e:
                if not failure_recorded:
                    self.rate_limiter.record_error()

                if attempt < max_attempts - 1:
                    wait_time = self._get_retry_delay(attempt)
                    logger.warning(f"[daily_basic] 第{attempt+1}次失败，{wait_time:.1f}s后重试: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[daily_basic] 最终失败: {e}")
                    return None

        return None
    def fetch_stock_basic_with_retry(self, max_attempts: int = 3) -> Optional[pd.DataFrame]:
        """
        获取股票基础列表（增强版：限流 + 风控检测 + 类型修复）

        🔥 升级点：
        - 强制限流（统一入口）
        - 自动识别被风控（空数据/异常返回）
        - 指数退避（防封IP）
        - 参数类型防污染
        """

        for attempt in range(max_attempts):
            try:
                # ✅ 统一限流入口（非常关键）
                self.rate_limiter.wait()

                # ✅ 防止隐藏类型污染（极重要）
                exchange = ''
                list_status = 'L'
                fields = 'ts_code,symbol,name,area,industry,list_date'

                # ✅ debug（首轮打印）
                if attempt == 0:
                    logger.debug("[Tushare] 获取股票列表请求发送")

                df = self.pro.stock_basic(
                    exchange=exchange,
                    list_status=list_status,
                    fields=fields
                )

                # =========================
                # 🚨 风控检测（核心升级）
                # =========================
                if df is None:
                    raise ValueError("返回None（疑似风控/限流）")

                if len(df) == 0:
                    raise ValueError("返回空数据（疑似被限流）")

                if 'ts_code' not in df.columns:
                    raise ValueError("字段异常（疑似接口被降级）")

                # ✅ 成功
                logger.info(f"✅ 获取股票列表成功：{len(df)} 条")
                return df

            except Exception as e:
                error_msg = str(e)

                logger.error(f"[StockBasic ERROR] {error_msg}")

                # 🚨 权限错误直接终止
                if '权限' in error_msg or '积分' in error_msg or 'token' in error_msg:
                    logger.error("❌ 权限/Token错误，停止重试")
                    return None

                # =========================
                # 🚀 智能退避（核心）
                # =========================
                if attempt < max_attempts - 1:
                    wait_time = self._get_retry_delay(attempt)

                    logger.warning(
                        f"⚠️ 第{attempt+1}次失败 | {wait_time:.1f}s后重试 | 原因: {error_msg[:80]}"
                    )

                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 获取股票列表最终失败：{error_msg}")
                    return None

        return None


# ============================================================================
# 智能缓存与增量更新
# ============================================================================
class DataCacheManager:
    def __init__(self, cache_dir: str = None, expiry_days: int = 1):
        self.cache_dir = cache_dir or str(DATA_CACHE_DIR / 'tushare')
        self.expiry_days = expiry_days
        os.makedirs(self.cache_dir, exist_ok=True)
        self._lock = Lock()

    def _get_cache_path(self, symbol: str, start_date: str, end_date: str) -> str:
        safe_symbol = symbol.replace('.', '_')
        filename = f"{safe_symbol}_{start_date}_{end_date}.pkl"
        return os.path.join(self.cache_dir, filename)

    def _get_meta_path(self, symbol: str) -> str:
        safe_symbol = symbol.replace('.', '_')
        return os.path.join(self.cache_dir, f"{safe_symbol}_meta.pkl")

    def is_cache_valid(self, cache_path: str) -> bool:
        if not os.path.exists(cache_path):
            return False
        modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return (datetime.now() - modified_time) < timedelta(days=self.expiry_days)

    def load_cache(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        cache_path = self._get_cache_path(symbol, start_date, end_date)
        if self.is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"加载缓存失败：{e}")
                return None
        return None

    def save_cache(self, symbol: str, start_date: str, end_date: str, data: pd.DataFrame) -> bool:
        cache_path = self._get_cache_path(symbol, start_date, end_date)
        try:
            with self._lock:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"保存缓存失败：{e}")
            return False

    def get_last_trade_date(self, symbol: str) -> Optional[str]:
        meta_path = self._get_meta_path(symbol)
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'rb') as f:
                    meta = pickle.load(f)
                    return meta.get('last_trade_date')
            except Exception:
                pass
        return None

    def update_meta(self, symbol: str, last_trade_date: str, record_count: int):
        meta_path = self._get_meta_path(symbol)
        try:
            with self._lock:
                meta = {
                    'last_trade_date': last_trade_date,
                    'last_update_time': datetime.now().isoformat(),
                    'record_count': record_count
                }
                with open(meta_path, 'wb') as f:
                    pickle.dump(meta, f)
        except Exception as e:
            logger.warning(f"更新元数据失败：{e}")

    def get_incremental_range(self, symbol: str, end_date: str) -> Tuple[Optional[str], str]:
        last_date = self.get_last_trade_date(symbol)
        if last_date and last_date < end_date:
            next_date = (datetime.strptime(last_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
            return next_date, end_date
        return None, end_date


# ============================================================================
# 监控与日志（适配项目日志）
# ============================================================================
class DataMonitor:
    def __init__(self, log_file: str = None):
        self.logger = logger  # 直接使用项目日志
        self.error_stats = {
            "total_requests": 0,
            "success_count": 0,
            "failure_count": 0,
            "error_types": {},
            "failing_symbols": set(),
            "start_time": datetime.now()
        }
        self._lock = Lock()

    def log_success(self, symbol: str, record_count: int, duration: float = 0):
        with self._lock:
            self.error_stats["total_requests"] += 1
            self.error_stats["success_count"] += 1
        self.logger.info(f"✅ 成功获取 {symbol} 数据，记录数：{record_count}, 耗时：{duration:.2f}s")

    def log_error(self, symbol: str, error_msg: str):
        with self._lock:
            self.error_stats["total_requests"] += 1
            self.error_stats["failure_count"] += 1
            error_type = error_msg.split(":")[0] if ":" in error_msg else error_msg[:30]
            self.error_stats["error_types"][error_type] = self.error_stats["error_types"].get(error_type, 0) + 1
            self.error_stats["failing_symbols"].add(symbol)
        self.logger.error(f"❌ 获取 {symbol} 失败：{error_msg}")

    def log_warning(self, symbol: str, message: str):
        self.logger.warning(f"⚠️ {symbol}: {message}")

    def get_stats(self) -> Dict:
        with self._lock:
            stats = self.error_stats.copy()
            stats["success_rate"] = (stats["success_count"] / stats["total_requests"] * 100
                                     if stats["total_requests"] > 0 else 0)
            stats["duration"] = (datetime.now() - stats["start_time"]).total_seconds()
        return stats

    def print_summary(self):
        stats = self.get_stats()
        print("\n" + "=" * 70)
        print("📊 数据采集摘要")
        print("=" * 70)
        print(f"   总请求数：{stats['total_requests']}")
        print(f"   成功：{stats['success_count']} ({stats['success_rate']:.1f}%)")
        print(f"   失败：{stats['failure_count']}")
        print(f"   总耗时：{stats['duration']:.1f} 秒")
        print(f"   平均速度：{stats['total_requests']/stats['duration']:.2f} 请求/秒" if stats['duration'] > 0 else "")
        if stats['error_types']:
            print("\n   错误类型统计:")
            for error_type, count in stats['error_types'].items():
                print(f"      - {error_type}: {count} 次")
        if stats['failing_symbols']:
            print(f"\n   失败股票列表（前 10 个）:")
            for symbol in list(stats['failing_symbols'])[:10]:
                print(f"      - {symbol}")
        print("=" * 70)

    def check_health(self, failure_threshold: float = 0.3) -> bool:
        stats = self.get_stats()
        failure_rate = stats["failure_count"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
        if failure_rate > failure_threshold:
            self.logger.warning(f"系统健康度警告：失败率 {failure_rate:.1%} 超过阈值 {failure_threshold:.1%}")
            return False
        return True


# ============================================================================
# 主数据获取器（对外接口）
# ============================================================================
class TushareDataFetcher:
    """A 股数据获取器（Tushare Pro 版）"""
    _initialized = False

    def __init__(self, symbol: str = None):
        self.symbol = symbol
        ensure_directories()
        self._init_tushare()

        if self.tushare_available:
            self.fetcher = ResilientTushareFetcher(self.pro)
            self.cache_manager = DataCacheManager()
        else:
            self.fetcher = None
            self.cache_manager = None

        self.monitor = DataMonitor()
        self.stocks_dir = DATA_STOCKS_DIR
        self.stock_list_path = STOCK_LIST_PATH

        if not TushareDataFetcher._initialized:
            TushareDataFetcher._initialized = True
            market = config.get('data.market', 'CN')
            print(f"✅ Tushare 数据获取器初始化完成")
            print(f"   市场：{market}")
            print(f"   数据目录：{DATA_DIR}")
            print(f"   Tushare: {'✅' if self.tushare_available else '❌'}")
            print(f"   当前积分：{self.tushare_points}")

    def _init_tushare(self):
        try:
            import tushare as ts
            ts.set_token(TUSHARE_TOKEN)
            self.pro = ts.pro_api()
            # 检查积分
            try:
                df = self.pro.user()
                self.tushare_points = df['points'].values[0] if 'points' in df.columns else 120
                if self.tushare_points >= 120:
                    self.tushare_available = True
                    print(f"✅ Tushare 连接成功（积分：{self.tushare_points}）")
                else:
                    print(f"⚠️ Tushare 积分不足：{self.tushare_points}/120")
                    self.tushare_available = True
            except Exception as e:
                print(f"⚠️ 无法查询积分：{e}")
                self.tushare_points = 120
                self.tushare_available = True
        except Exception as e:
            print(f"❌ Tushare 不可用：{str(e)[:60]}")
            self.tushare_available = False
            self.pro = None
            self.tushare_points = 0

    def fetch_historical_data(self, start_date: str, end_date: str = None,
                              use_cache: bool = True, force_refresh: bool = False) -> pd.DataFrame:
        if not self.symbol:
            raise ValueError("请先设置股票代码")

        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # ⚠️ 防御性编程：确保 start_date / end_date 一定是字符串
        # 很多配置文件（yaml/json）会把 20200101 解析成 int，必须强转
        start_date = str(start_date)
        end_date = str(end_date)

        # 去掉 '-'，统一转为 tushare 需要的 YYYYMMDD 格式
        start_fmt = start_date.replace('-', '')
        end_fmt = end_date.replace('-', '')

        cache_file = self._get_stock_cache_path(self.symbol)

        # 从缓存加载
        if use_cache and not force_refresh and cache_file.exists():
            print(f"📂 从缓存加载：{self.symbol}")
            try:
                # ✅ 直接读取，索引会被自动恢复为保存时的索引（datetime）
                df = pd.read_parquet(cache_file)
                # 确保索引是 datetime 类型（如果读取后不是，手动转换）
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                if not df.empty:
                    return df
                # 如果数据为空，直接返回空
                if df.empty:
                    print("   缓存为空")
                    df = pd.DataFrame()
                else:
                    print(f"✅ 加载成功：{len(df)} 条记录")
                    # 增量更新逻辑保持不变（注意：df.index 现在是 datetime）
                    # ...
            except Exception as e:
                self.monitor.log_error(self.symbol, f"缓存读取失败：{e}")
                print(f"⚠️ 缓存读取失败：{e}")
                df = pd.DataFrame()

        # 从 API 获取
        print(f"📡 从 Tushare 获取：{self.symbol}")
        start_time = time.time()
        df = self._fetch_from_api(self.symbol, start_fmt, end_fmt)
        duration = time.time() - start_time

        if df is None or df.empty:
            self.monitor.log_error(self.symbol, "API 获取失败或返回空数据")
            print("⚠️ API 获取失败")
            return pd.DataFrame()

        if use_cache:
            self._save_to_cache(df, cache_file)
            if self.cache_manager:
                self.cache_manager.update_meta(self.symbol, end_fmt, len(df))

        self.monitor.log_success(self.symbol, len(df), duration)
        return df

    def fetch_daily_basic(
        self,
        start_date: str,
        end_date: str,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> pd.DataFrame:

        if not self.symbol:
            raise ValueError("请先设置股票代码")

        start_fmt = str(start_date).replace('-', '')
        end_fmt = str(end_date).replace('-', '')

        cache_file = self._get_basic_cache_path(self.symbol)

        # =========================
        # 📂 1. 从缓存加载
        # =========================
        if use_cache and not force_refresh and cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)

                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)

                if not df.empty:
                    print(f"📂 daily_basic缓存加载成功: {self.symbol} ({len(df)}条)")
                    return df

            except Exception as e:
                self.monitor.log_warning(self.symbol, f"basic缓存读取失败: {e}")

        # =========================
        # 📡 2. 从 API 获取
        # =========================
        print(f"📡 获取 daily_basic: {self.symbol}")

        start_time = time.time()

        df = self.fetcher.fetch_daily_basic_with_retry(
            ts_code=self.symbol,
            start_date=start_fmt,
            end_date=end_fmt
        )

        duration = time.time() - start_time

        if df is None or df.empty:
            self.monitor.log_error(self.symbol, "daily_basic 获取失败")
            return pd.DataFrame()

        # =========================
        # 🧹 3. 数据清洗
        # =========================
        df = self._clean_daily_basic(df)

        # =========================
        # ⚠️ 4. 单位修复（非常重要）
        # =========================
        if 'TotalMV' in df.columns:
            df['TotalMV'] = df['TotalMV'] * 10000  # 万元 → 元

        # =========================
        # 🏷️ 5. 加 symbol（统一格式）
        # =========================
        df['Symbol'] = self.symbol

        # =========================
        # 💾 6. 保存缓存
        # =========================
        if use_cache:
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(cache_file)
            except Exception as e:
                self.monitor.log_warning(self.symbol, f"basic缓存保存失败: {e}")

        # =========================
        # 📊 7. 监控记录
        # =========================
        self.monitor.log_success(self.symbol, len(df), duration)

        return df

    def _clean_daily_basic(self, df: pd.DataFrame) -> pd.DataFrame:

        column_mapping = {
            'trade_date': 'Date',
            'total_mv': 'TotalMV',
            'circ_mv': 'CircMV',
            'turnover_rate': 'TurnoverRate',
            'pe': 'PE'
        }

        df = df.rename(columns=column_mapping)

        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
        # 🔥 核心：T+1 延迟（防未来函数）
        df['Date'] = df['Date'] + pd.Timedelta(days=1)
        df.set_index('Date', inplace=True)

        # 数值转换
        for col in ['TotalMV', 'CircMV', 'TurnoverRate', 'PE']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.sort_index()

        return df

    def _fetch_from_api(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从 Tushare API 获取数据（带完整数据清洗）

        🔥 关键修复：
        - 强制 symbol 为字符串
        - 强制日期格式 YYYYMMDD
        - 防止 None / int / numpy 类型污染
        """

        if not self.tushare_available or self.fetcher is None:
            return pd.DataFrame()

        try:
            # ✅ 强制 symbol 类型
            symbol = str(symbol).strip()

            # ✅ 日期格式统一
            start_date = str(start_date).replace('-', '')
            end_date = str(end_date).replace('-', '')

            # ✅ 防御：长度校验
            if len(start_date) != 8 or len(end_date) != 8:
                raise ValueError(f"日期格式错误: {start_date}, {end_date}")

            # ✅ 防御：非法 symbol
            if '.' not in symbol:
                raise ValueError(f"非法股票代码: {symbol}")

            df = self.fetcher.fetch_daily_with_retry(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                return pd.DataFrame()

            df = self._clean_data(df, symbol)

            print(f"✅ 成功获取 {symbol} 共 {len(df)} 条记录")
            return df

        except Exception as e:
            self.monitor.log_error(symbol, str(e))
            print(f"❌ 获取失败：{str(e)[:80]}")
            return pd.DataFrame()

    def _clean_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        column_mapping = {
            'trade_date': 'Date', 'open': 'Open', 'close': 'Close',
            'high': 'High', 'low': 'Low', 'vol': 'Volume', 'amount': 'Turnover'
        }
        df = df.rename(columns=column_mapping)
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [col for col in required_cols if col in df.columns]
        df = df[available_cols]
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
            # 🔥 核心：T+1 延迟（防未来函数）
            df['Date'] = df['Date'] + pd.Timedelta(days=1)
            df.set_index('Date', inplace=True)
        df = df.dropna()
        df['Symbol'] = symbol
        return df

    def _get_stock_cache_path(self, symbol: str) -> Path:
        safe_symbol = symbol.replace('.', '_')
        return self.stocks_dir / f"{safe_symbol}.parquet"

    def _get_basic_cache_path(self, symbol: str) -> Path:
        """
        基本面数据（daily_basic）
        """
        safe_symbol = symbol.replace('.', '_')
        return self.stocks_dir / f"{safe_symbol}_basic.parquet"

    def _save_to_cache(self, df: pd.DataFrame, cache_file: Path):
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            # ✅ 直接保存，cache_file 已经包含 .parquet 后缀
            df.to_parquet(cache_file)
        except Exception as e:
            self.monitor.log_warning(self.symbol, f"缓存保存失败：{e}")

    def fetch_all_stocks(self, start_date: str = None, end_date: str = None,
                         skip_existing: bool = True, force_refresh: bool = False,
                         stock_list: List[str] = None, resume: bool = True) -> Dict[str, pd.DataFrame]:
        if start_date is None:
            start_date = config.get('data.batch_start_date', '2020-01-01')
        if end_date is None:
            end_date = config.get('data.batch_end_date')
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')

        if stock_list is None:
            stock_list = self.get_stock_list()

        if not stock_list:
            print("❌ 未获取到股票列表")
            return {}

        # 断点续传
        if resume and skip_existing:
            original_count = len(stock_list)
            stock_list = [s for s in stock_list if not self._get_stock_cache_path(s).exists()]
            skipped = original_count - len(stock_list)
            print(f"📂 跳过 {skipped} 只已缓存股票，剩余 {len(stock_list)} 只需要获取")

        if not stock_list:
            print("✅ 所有股票已缓存，无需获取")
            return {}

        print(f"\n📊 开始批量获取股票数据（Tushare Pro 版）")
        print(f"   股票数量：{len(stock_list)}")
        print(f"   日期范围：{start_date} 至 {end_date}")
        print(f"   当前积分：{self.tushare_points}")
        print("-" * 70)

        data_dict = {}
        success_count = 0
        fail_count = 0

        for i, symbol in enumerate(stock_list):
            try:
                self.symbol = symbol
                df = self.fetch_historical_data(
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=True,
                    force_refresh=force_refresh
                )
                if not df.empty:
                    data_dict[symbol] = df
                    success_count += 1
                else:
                    fail_count += 1

                if (i + 1) % 100 == 0:
                    print(f"\n⏳ 已获取 {i+1} 只，等待 10 秒...")
                    time.sleep(10)
            except KeyboardInterrupt:
                print(f"\n\n⚠️ 用户中断，已获取 {success_count} 只股票")
                print(f"💡 再次运行将自动断点续传")
                break
            except Exception as e:
                self.monitor.log_error(symbol, str(e))
                print(f"\n❌ 获取 {symbol} 失败：{str(e)[:80]}")
                fail_count += 1
                time.sleep(5)

        self.monitor.print_summary()
        return data_dict

    def get_stock_list(self, refresh: bool = False) -> List[str]:
        if not refresh and self.stock_list_path.exists():
            try:
                df = pd.read_csv(self.stock_list_path, dtype={'code': str, 'symbol': str})
                if 'symbol' in df.columns:
                    stock_list = df['symbol'].astype(str).tolist()
                elif 'code' in df.columns:
                    stock_list = []
                    for _, row in df.iterrows():
                        code = str(row['code'])
                        market = row.get('market', '')
                        market_code = 'SZ' if market == '1' else 'SH'
                        stock_list.append(f"{code}.{market_code}")
                else:
                    return []
                stock_list = [s for s in stock_list if s and len(s) > 5]
                print(f"📂 从缓存加载股票列表：{len(stock_list)} 只")
                return stock_list
            except Exception as e:
                print(f"⚠️ 股票列表读取失败：{e}")

        if not self.tushare_available or self.fetcher is None:
            print("❌ Tushare 不可用，无法获取股票列表")
            return []

        print("📡 从 Tushare 获取股票列表...")
        try:
            df = self.fetcher.fetch_stock_basic_with_retry()
            if df is None or df.empty:
                return []
            stock_list = df['ts_code'].astype(str).tolist()
            print(f"✅ 获取股票列表：{len(stock_list)} 只")
            self._save_stock_list(stock_list, df)
            return stock_list
        except Exception as e:
            print(f"⚠️ 获取股票列表失败：{e}")
            return []

    def _save_stock_list(self, stock_list: List[str], df: pd.DataFrame):
        try:
            save_df = pd.DataFrame({
                'code': [s.split('.')[0] for s in stock_list],
                'symbol': stock_list,
                'market': ['SZ' if s.endswith('.SZ') else 'SH' for s in stock_list]
            })
            self.stock_list_path.parent.mkdir(parents=True, exist_ok=True)
            save_df.to_csv(self.stock_list_path, index=False)
            print(f"💾 股票列表已保存：{self.stock_list_path}")
        except Exception as e:
            print(f"⚠️ 保存股票列表失败：{e}")

    def check_cache_status(self) -> Dict:
        if not self.stocks_dir.exists():
            return {'total': 0, 'cached': 0, 'missing': 0}
        stock_list = self.get_stock_list()
        cached = sum(1 for s in stock_list if self._get_stock_cache_path(s).exists())
        missing = len(stock_list) - cached
        return {
            'total': len(stock_list),
            'cached': cached,
            'missing': missing,
            'coverage': f"{cached/len(stock_list)*100:.1f}%" if stock_list else "0%"
        }
