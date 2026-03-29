from infra.config import config
from data.ingestion.tushare_client import TushareDataFetcher


def register(subparsers):
    data_parser = subparsers.add_parser("data", help="data module")
    data_sub = data_parser.add_subparsers(dest="action")

    update_parser = data_sub.add_parser("update", help="update data")
    update_sub = update_parser.add_subparsers(dest="target")

    stock_parser = update_sub.add_parser("stock", help="update a single stock")
    stock_parser.add_argument("--code", required=True, help="stock code, e.g. 000001.SZ")
    stock_parser.add_argument("--start-date", help="start date YYYY-MM-DD")
    stock_parser.add_argument("--end-date", help="end date YYYY-MM-DD")
    stock_parser.add_argument("--force-refresh", action="store_true", help="ignore local cache and refetch all")
    stock_parser.set_defaults(func=handle_update_stock)

    stocks_parser = update_sub.add_parser("stocks", help="update many stocks")
    stocks_parser.add_argument("--start-date", help="start date YYYY-MM-DD")
    stocks_parser.add_argument("--end-date", help="end date YYYY-MM-DD")
    stocks_parser.add_argument("--limit", type=int, help="only process first N stocks")
    stocks_parser.add_argument("--force-refresh", action="store_true", help="ignore local cache and refetch all")
    stocks_parser.add_argument("--resume", action="store_true", help="kept for compatibility; incremental update is now default")
    stocks_parser.set_defaults(func=handle_update_stocks)

    status_parser = data_sub.add_parser("status", help="show status")
    status_sub = status_parser.add_subparsers(dest="target")
    cache_parser = status_sub.add_parser("cache", help="cache status")
    cache_parser.set_defaults(func=handle_status_cache)


def _resolve_date_range(args):
    start_date = args.start_date or config.get("data.batch_start_date", "2020-01-01")
    end_date = args.end_date or config.get("data.batch_end_date")
    return start_date, end_date


def handle_update_stock(args):
    fetcher = TushareDataFetcher(symbol=args.code)
    start_date, end_date = _resolve_date_range(args)

    price_df = fetcher.fetch_historical_data(
        start_date=start_date,
        end_date=end_date,
        force_refresh=args.force_refresh,
    )
    basic_df = fetcher.fetch_daily_basic(
        start_date=start_date,
        end_date=end_date,
        force_refresh=args.force_refresh,
    )

    if price_df.empty and basic_df.empty:
        print(f"Update failed for {args.code}")
        return

    print(f"\nUpdate finished for {args.code}")
    print(f"  price rows: {len(price_df)}")
    print(f"  basic rows: {len(basic_df)}")


def handle_update_stocks(args):
    fetcher = TushareDataFetcher()
    start_date, end_date = _resolve_date_range(args)

    stock_list = fetcher.get_stock_list()
    if args.limit:
        stock_list = stock_list[:args.limit]
        print(f"Only process first {len(stock_list)} stocks")

    if not stock_list:
        print("No stocks available to update")
        return

    success_count = 0
    failure_count = 0

    for i, symbol in enumerate(stock_list, start=1):
        print(f"\n[{i}/{len(stock_list)}] Update {symbol}")
        fetcher.symbol = symbol

        try:
            price_df = fetcher.fetch_historical_data(
                start_date=start_date,
                end_date=end_date,
                force_refresh=args.force_refresh,
            )
            basic_df = fetcher.fetch_daily_basic(
                start_date=start_date,
                end_date=end_date,
                force_refresh=args.force_refresh,
            )

            if price_df.empty and basic_df.empty:
                failure_count += 1
                print(f"  failed: {symbol}")
                continue

            success_count += 1
            print(f"  price rows: {len(price_df)}")
            print(f"  basic rows: {len(basic_df)}")

        except Exception as e:
            failure_count += 1
            print(f"  failed: {symbol} | {e}")

    print("\nStock update finished")
    print(f"  success: {success_count}")
    print(f"  failed: {failure_count}")


def handle_status_cache(args):
    fetcher = TushareDataFetcher()
    stats = fetcher.check_cache_status()

    print("\nCache status:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
