# scripts/commands/data.py

from infra.config import config
from data.ingestion.tushare_client import TushareDataFetcher


def register_data_commands(subparsers):
    # 一级：data
    data_parser = subparsers.add_parser("data", help="数据模块")
    data_sub = data_parser.add_subparsers(dest="action")

    # ==================================================
    # 二级：update
    # ==================================================
    update_parser = data_sub.add_parser("update", help="更新数据")
    update_sub = update_parser.add_subparsers(dest="target")

    # ----------------------
    # data update stock
    # ----------------------
    stock_parser = update_sub.add_parser("stock", help="更新单只股票")
    stock_parser.add_argument("--code", required=True, help="股票代码，如 000001.SZ")
    stock_parser.add_argument("--start")
    stock_parser.add_argument("--end")
    stock_parser.add_argument("--force", action="store_true")

    stock_parser.set_defaults(func=handle_update_stock)

    # ----------------------
    # data update stocks
    # ----------------------
    stocks_parser = update_sub.add_parser("stocks", help="更新多只股票")
    stocks_parser.add_argument("--start")
    stocks_parser.add_argument("--end")
    stocks_parser.add_argument("--limit", type=int, help="仅更新前 N 只股票")
    stocks_parser.add_argument("--force", action="store_true")

    stocks_parser.set_defaults(func=handle_update_stocks)

    # ==================================================
    # 二级：status
    # ==================================================
    status_parser = data_sub.add_parser("status", help="查看状态")
    status_sub = status_parser.add_subparsers(dest="target")

    cache_parser = status_sub.add_parser("cache", help="缓存状态")
    cache_parser.set_defaults(func=handle_status_cache)


# ==================================================
# handlers
# ==================================================

def handle_update_stock(args):
    fetcher = TushareDataFetcher(symbol=args.code)

    start_date = args.start or config.get('data.batch_start_date', '2020-01-01')
    end_date = args.end or config.get('data.batch_end_date')

    df = fetcher.fetch_historical_data(
        start_date=start_date,
        end_date=end_date,
        force_refresh=args.force
    )

    if not df.empty:
        print(f"\n✅ 股票 {args.code} 更新完成，共 {len(df)} 条记录")
    else:
        print(f"❌ 股票 {args.code} 更新失败")


def handle_update_stocks(args):
    fetcher = TushareDataFetcher()

    start_date = args.start or config.get('data.batch_start_date', '2020-01-01')
    end_date = args.end or config.get('data.batch_end_date')

    stock_list = None
    if args.limit:
        all_stocks = fetcher.get_stock_list()
        stock_list = all_stocks[:args.limit]
        print(f"🎯 仅处理前 {len(stock_list)} 只股票")

    fetcher.fetch_all_stocks(
        start_date=start_date,
        end_date=end_date,
        force_refresh=args.force,
        skip_existing=not args.force,
        stock_list=stock_list
    )


def handle_status_cache(args):
    fetcher = TushareDataFetcher()
    stats = fetcher.check_cache_status()

    print("\n📊 缓存状态：")
    for k, v in stats.items():
        print(f"   {k}: {v}")