"""
拉取A股太空/航天概念股数据
==========================
- 中国卫星 (600118.SH) — 卫星制造龙头
- 航天电子 (600879.SH) — 航天电子设备
- 航天动力 (600343.SH) — 航天动力系统
"""

import requests
import pandas as pd
from datetime import datetime, timedelta

API_URL = "https://api.tushare.pro"
TOKEN = "e3a2cfe468c90953359a183127273ad04175da9de57308f61a1ca703"

# 与现有数据保持一致的日期范围
start_date = "20240711"
end_date = "20260710"

stocks = [
    ("600118.SH", "中国卫星"),
    ("600879.SH", "航天电子"),
    ("600343.SH", "航天动力"),
]

output_dir = "/Users/liutt/Documents/AI 2026/Workbuddy/BI工作坊-ai量化公益课/Task4"

for ts_code, name in stocks:
    print(f"\n{'='*50}")
    print(f"  拉取 {name} ({ts_code}) {start_date} ~ {end_date}")
    print(f"{'='*50}")

    payload = {
        "api_name": "daily",
        "token": TOKEN,
        "params": {
            "ts_code": ts_code,
            "start_date": start_date,
            "end_date": end_date,
        },
        "fields": "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        result = resp.json()

        if result.get("code") != 0:
            print(f"  API错误: {result.get('msg', '未知错误')}")
            continue

        data = result["data"]
        df = pd.DataFrame(data["items"], columns=data["fields"])
        df = df.sort_values("trade_date").reset_index(drop=True)

        for col in ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        output_path = f"{output_dir}/{name}_行情数据.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print(f"  成功! 共 {len(df)} 条记录")
        print(f"  日期: {df['trade_date'].min()} ~ {df['trade_date'].max()}")
        print(f"  最新收盘: {df['close'].iloc[-1]}")
        print(f"  期间涨跌: {df['close'].iloc[-1] / df['close'].iloc[0] - 1:+.2%}")
        print(f"  保存至: {output_path}")

    except Exception as e:
        print(f"  拉取失败: {e}")

print("\n\n全部完成!")
