from typing import Dict, List, Optional

from data.ingestion.tushare_client import TushareDataFetcher
from infra.config import config


def _resolve_date_range(start_date: Optional[str], end_date: Optional[str]):
    resolved_start = start_date or config.get("data.batch_start_date", "2020-01-01")
    resolved_end = end_date or config.get("data.batch_end_date")
    return resolved_start, resolved_end


def run_update_stock(
    *,
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force_refresh: bool = False,
    fetcher: Optional[TushareDataFetcher] = None,
):
    fetcher = fetcher or TushareDataFetcher(symbol=code)
    start_date, end_date = _resolve_date_range(start_date, end_date)

    price_df = fetcher.fetch_historical_data(
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh,
    )
    basic_df = fetcher.fetch_daily_basic(
        start_date=start_date,
        end_date=end_date,
        force_refresh=force_refresh,
    )

    success = not (price_df.empty and basic_df.empty)
    return {
        "code": code,
        "start_date": start_date,
        "end_date": end_date,
        "force_refresh": force_refresh,
        "price_rows": len(price_df),
        "basic_rows": len(basic_df),
        "success": success,
    }


def run_update_stocks(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    force_refresh: bool = False,
    resume: bool = False,
    fetcher: Optional[TushareDataFetcher] = None,
):
    fetcher = fetcher or TushareDataFetcher()
    start_date, end_date = _resolve_date_range(start_date, end_date)

    stock_list = fetcher.get_stock_list()
    if limit:
        stock_list = stock_list[:limit]

    if not stock_list:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "force_refresh": force_refresh,
            "resume": resume,
            "requested_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "results": [],
        }

    results: List[Dict[str, object]] = []
    success_count = 0
    failure_count = 0

    for symbol in stock_list:
        fetcher.symbol = symbol
        try:
            price_df = fetcher.fetch_historical_data(
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh,
            )
            basic_df = fetcher.fetch_daily_basic(
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh,
            )

            success = not (price_df.empty and basic_df.empty)
            if success:
                success_count += 1
            else:
                failure_count += 1

            results.append(
                {
                    "symbol": symbol,
                    "price_rows": len(price_df),
                    "basic_rows": len(basic_df),
                    "success": success,
                    "error": None,
                }
            )
        except Exception as exc:
            failure_count += 1
            results.append(
                {
                    "symbol": symbol,
                    "price_rows": 0,
                    "basic_rows": 0,
                    "success": False,
                    "error": str(exc),
                }
            )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "force_refresh": force_refresh,
        "resume": resume,
        "requested_count": len(stock_list),
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
    }


def get_cache_status(*, fetcher: Optional[TushareDataFetcher] = None):
    fetcher = fetcher or TushareDataFetcher()
    return {
        "stats": fetcher.check_cache_status(),
    }
