"""Compatibility command entry for shared data management."""

from pipelines.data_pipeline import (
    run_data_status_cache_pipeline,
    run_data_update_stock_pipeline,
    run_data_update_stocks_pipeline,
)


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


def print_update_stock_result(payload):
    if not payload["success"]:
        print(f"Update failed for {payload['code']}")
        return

    print(f"\nUpdate finished for {payload['code']}")
    print(f"  price rows: {payload['price_rows']}")
    print(f"  basic rows: {payload['basic_rows']}")


def print_update_stocks_result(payload):
    if payload["limit"]:
        print(f"Only process first {payload['requested_count']} stocks")

    if payload["requested_count"] == 0:
        print("No stocks available to update")
        return

    for index, result in enumerate(payload["results"], start=1):
        print(f"\n[{index}/{payload['requested_count']}] Update {result['symbol']}")
        if result["success"]:
            print(f"  price rows: {result['price_rows']}")
            print(f"  basic rows: {result['basic_rows']}")
        elif result["error"]:
            print(f"  failed: {result['symbol']} | {result['error']}")
        else:
            print(f"  failed: {result['symbol']}")

    print("\nStock update finished")
    print(f"  success: {payload['success_count']}")
    print(f"  failed: {payload['failure_count']}")


def print_cache_status_result(payload):
    print("\nCache status:")
    for key, value in payload["stats"].items():
        print(f"  {key}: {value}")


def handle_update_stock(args):
    payload = run_data_update_stock_pipeline(
        code=args.code,
        start_date=args.start_date,
        end_date=args.end_date,
        force_refresh=args.force_refresh,
    )
    print_update_stock_result(payload)


def handle_update_stocks(args):
    payload = run_data_update_stocks_pipeline(
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit,
        force_refresh=args.force_refresh,
        resume=args.resume,
    )
    print_update_stocks_result(payload)


def handle_status_cache(args):
    payload = run_data_status_cache_pipeline()
    print_cache_status_result(payload)
