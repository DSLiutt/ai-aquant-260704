import requests
import json
import pandas as pd
from datetime import datetime, timedelta

# Tushare API 直接调用
API_URL = "https://api.tushare.pro"
TOKEN = "e3a2cfe468c90953359a183127273ad04175da9de57308f61a1ca703"

# 中芯国际 A股代码
ts_code = "688981.SH"
end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

print(f"获取 {ts_code} 从 {start_date} 到 {end_date} 的日线数据...")

payload = {
    "api_name": "daily",
    "token": TOKEN,
    "params": {
        "ts_code": ts_code,
        "start_date": start_date,
        "end_date": end_date
    },
    "fields": "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"
}

resp = requests.post(API_URL, json=payload, timeout=30)
result = resp.json()

if result.get("code") != 0:
    print(f"API返回错误: {result}")
    exit(1)

data = result["data"]
df = pd.DataFrame(data["items"], columns=data["fields"])

# 按交易日期升序排列
df = df.sort_values("trade_date").reset_index(drop=True)

# 转换数据类型
for col in ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 保存到CSV
output_path = "/Users/liutt/Documents/AI 2026/Workbuddy/BI工作坊-ai量化公益课/中芯国际_688981_日线数据.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n数据获取成功！共 {len(df)} 条记录")
print(f"数据已保存至: {output_path}")
print(f"\n数据预览:")
print(df[["trade_date", "open", "high", "low", "close", "vol", "pct_chg"]].head(10).to_string(index=False))
print("...")
print(df[["trade_date", "open", "high", "low", "close", "vol", "pct_chg"]].tail(10).to_string(index=False))
print(f"\n字段列表: {list(df.columns)}")

# 同时输出JSON供HTML使用
json_path = "/Users/liutt/Documents/AI 2026/Workbuddy/BI工作坊-ai量化公益课/中芯国际_688981_日线数据.json"
df.to_json(json_path, orient="records", force_ascii=False)
print(f"\nJSON数据已保存至: {json_path}")
