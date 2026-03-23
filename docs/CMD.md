# 数据获取

        # 单只股票
        python scripts/update_data.py --stock 000001.SZ --start 2023-01-01 --end 2023-12-31
        # 全量更新（默认日期范围）
        python scripts/update_data.py --start 2020-01-01 --end 2023-12-31
        # 强制刷新（忽略缓存）
        python scripts/update_data.py --force