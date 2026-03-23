# scripts/update_data.py
"""
数据更新脚本
用法: python scripts/update_data.py [--start 2020-01-01] [--end 2023-12-31] [--force]
"""
import sys
import argparse
from pathlib import Path

# 将项目根目录加入 sys.path（确保模块导入正确）
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.config import config
from data.ingestion.tushare_client import TushareDataFetcher


def main():
    parser = argparse.ArgumentParser(description='更新 A 股历史数据')
    parser.add_argument('--start', default=None, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', default=None, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--force', action='store_true', help='强制刷新所有数据')
    parser.add_argument('--stock', type=str, help='仅更新单只股票（如 000001.SZ）')
    args = parser.parse_args()

    # 从配置获取默认日期
    start_date = args.start or config.get('data.batch_start_date', '2020-01-01')
    end_date = args.end or config.get('data.batch_end_date')  # None 表示获取到最新

    fetcher = TushareDataFetcher()

    if args.stock:
        fetcher.symbol = args.stock
        df = fetcher.fetch_historical_data(
            start_date=start_date,
            end_date=end_date,
            force_refresh=args.force
        )
        if not df.empty:
            print(f"\n✅ 股票 {args.stock} 数据已更新，共 {len(df)} 条记录")
        else:
            print(f"❌ 股票 {args.stock} 数据更新失败")
    else:
        fetcher.fetch_all_stocks(
            start_date=start_date,
            end_date=end_date,
            force_refresh=args.force,
            skip_existing=not args.force
        )


if __name__ == '__main__':
    main()