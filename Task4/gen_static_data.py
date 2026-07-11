"""
生成静态Dashboard所需的全部JSON数据
=====================================
预计算9只股票 × 5组参数的回测结果，导出为单一JSON文件
供GitHub Pages静态页面使用（无需Flask后端）
"""

import os
import json
import numpy as np
import pandas as pd
from turtle_strategy import (
    load_stock_data, calc_donchian_channel, calc_atr,
    generate_signals, backtest, calc_metrics, run_strategy
)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def safe_float(val):
    if val is None:
        return None
    try:
        if np.isnan(val) or np.isinf(val):
            return None
        return round(float(val), 6)
    except (TypeError, ValueError):
        return None


def get_stock_files():
    files = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith("_行情数据.csv"):
            name = f.replace("_行情数据.csv", "")
            files.append((name, f))
    return files


# 5组参数
PARAM_SETS = [
    {"id": "classic",   "label": "经典海龟 20/10/2.0",  "entry": 20, "exit": 10, "atr": 20, "stop": 2.0},
    {"id": "tight_stop","label": "紧止损 20/10/1.5",     "entry": 20, "exit": 10, "atr": 20, "stop": 1.5},
    {"id": "wide_stop", "label": "宽止损 20/10/3.0",     "entry": 20, "exit": 10, "atr": 20, "stop": 3.0},
    {"id": "long_chan", "label": "长周期 55/20/2.0",     "entry": 55, "exit": 20, "atr": 20, "stop": 2.0},
    {"id": "short_chan","label": "短周期 10/5/2.0",      "entry": 10, "exit": 5,  "atr": 20, "stop": 2.0},
]


def build_detail(stock_name, csv_file, params, initial_capital=100000):
    """构建单只股票的完整详情数据"""
    csv_path = os.path.join(DATA_DIR, csv_file)
    df, trade_df, metrics = run_strategy(
        csv_path,
        entry_period=params["entry"],
        exit_period=params["exit"],
        atr_period=params["atr"],
        stop_atr_mult=params["stop"],
        initial_capital=initial_capital,
    )

    dates = df["trade_date"].dt.strftime("%Y-%m-%d").tolist()

    # K线数据
    candles = []
    for _, row in df.iterrows():
        candles.append({
            "date": row["trade_date"].strftime("%Y-%m-%d"),
            "open": safe_float(row["open"]),
            "high": safe_float(row["high"]),
            "low": safe_float(row["low"]),
            "close": safe_float(row["close"]),
        })

    # 通道数据
    channel = {
        "dates": dates,
        "upper_entry": [safe_float(v) for v in df["upper_entry"].tolist()],
        "lower_entry": [safe_float(v) for v in df["lower_entry"].tolist()],
        "upper_exit":  [safe_float(v) for v in df["upper_exit"].tolist()],
        "lower_exit":  [safe_float(v) for v in df["lower_exit"].tolist()],
        "atr":         [safe_float(v) for v in df["ATR"].tolist()],
    }

    # 买卖信号
    buy_signals = []
    sell_signals = []
    for _, row in df.iterrows():
        if row["signal"] == 1:
            buy_signals.append({
                "date": row["trade_date"].strftime("%Y-%m-%d"),
                "price": safe_float(row["close"]),
            })
        elif row["signal"] == -1:
            sell_signals.append({
                "date": row["trade_date"].strftime("%Y-%m-%d"),
                "price": safe_float(row["close"]),
            })

    # 净值曲线
    equity = {
        "dates": dates,
        "strategy":  [safe_float(v) for v in df["strategy_value"].tolist()],
        "buy_hold":  [safe_float(v) for v in df["buy_hold_value"].tolist()],
    }

    # 回撤曲线
    cummax = df["strategy_value"].cummax()
    strategy_dd = ((df["strategy_value"] - cummax) / cummax * 100).tolist()
    bh_cummax = df["buy_hold_value"].cummax()
    bh_dd = ((df["buy_hold_value"] - bh_cummax) / bh_cummax * 100).tolist()

    drawdown = {
        "dates": dates,
        "strategy_dd": [safe_float(v) for v in strategy_dd],
        "bh_dd":       [safe_float(v) for v in bh_dd],
    }

    # 交易记录
    trades = []
    for _, row in trade_df.iterrows():
        trades.append({
            "date":      row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
            "action":    row["action"],
            "price":     safe_float(row["price"]),
            "shares":    int(row["shares"]),
            "value":     safe_float(row["value"]),
            "atr":       safe_float(row.get("atr")),
            "stop_loss": safe_float(row.get("stop_loss")),
        })

    # Sparkline（降采样到60点）
    n = len(df)
    step = max(1, n // 60)
    sparkline = [safe_float(v) for v in df["strategy_value"].iloc[::step].tolist()]
    bh_sparkline = [safe_float(v) for v in df["buy_hold_value"].iloc[::step].tolist()]
    spark_dates = [d for i, d in enumerate(dates) if i % step == 0]

    # 指标
    m = {
        "cumulative_return":    safe_float(metrics["cumulative_return"]),
        "sharpe_ratio":         safe_float(metrics["sharpe_ratio"]),
        "max_drawdown":         safe_float(metrics["max_drawdown"]),
        "annual_return":        safe_float(metrics["annual_return"]),
        "win_rate":             safe_float(metrics["win_rate"]),
        "buy_count":            int(metrics["buy_count"]),
        "sell_count":           int(metrics["sell_count"]),
        "final_value":          safe_float(metrics["final_value"]),
        "bh_cumulative_return": safe_float(metrics["bh_cumulative_return"]),
        "bh_max_drawdown":      safe_float(metrics["bh_max_drawdown"]),
        "bh_sharpe_ratio":      safe_float(metrics["bh_sharpe_ratio"]),
    }

    return {
        "candles": candles,
        "channel": channel,
        "signals": {"buy": buy_signals, "sell": sell_signals},
        "equity": equity,
        "drawdown": drawdown,
        "trades": trades,
        "metrics": m,
        "sparkline": sparkline,
        "bh_sparkline": bh_sparkline,
        "dates": spark_dates,
    }


def build_overview_item(stock_name, detail_data):
    """从详情数据中提取概览信息"""
    m = detail_data["metrics"]
    return {
        "stock": stock_name,
        "cumulative_return":    m["cumulative_return"],
        "sharpe_ratio":         m["sharpe_ratio"],
        "max_drawdown":         m["max_drawdown"],
        "annual_return":        m["annual_return"],
        "win_rate":             m["win_rate"],
        "buy_count":            m["buy_count"],
        "sell_count":           m["sell_count"],
        "bh_cumulative_return": m["bh_cumulative_return"],
        "bh_max_drawdown":      m["bh_max_drawdown"],
        "bh_sharpe_ratio":      m["bh_sharpe_ratio"],
        "sparkline":            detail_data["sparkline"],
        "bh_sparkline":         detail_data["bh_sparkline"],
        "dates":                detail_data["dates"],
    }


def main():
    stocks = get_stock_files()
    print(f"发现 {len(stocks)} 只股票: {[s[0] for s in stocks]}")

    all_data = {
        "stocks": [s[0] for s in stocks],
        "paramSets": PARAM_SETS,
        "overview": {},   # {paramSetId: [overview_items]}
        "details": {},    # {stockName: detail_data} (default params only)
        "sweeps": {},     # {stockName: [sweep_items]}
    }

    default_params = PARAM_SETS[0]  # 经典海龟参数

    # 1. 为每只股票生成默认参数的详情数据
    for stock_name, csv_file in stocks:
        print(f"  生成详情: {stock_name} (默认参数)...")
        detail = build_detail(stock_name, csv_file, default_params)
        all_data["details"][stock_name] = detail
        all_data["overview"][default_params["id"]] = all_data["overview"].get(default_params["id"], [])
        all_data["overview"][default_params["id"]].append(build_overview_item(stock_name, detail))

    # 2. 为其他参数组生成概览数据
    for params in PARAM_SETS[1:]:
        print(f"  生成概览: {params['label']}...")
        overview_list = []
        for stock_name, csv_file in stocks:
            detail = build_detail(stock_name, csv_file, params)
            overview_list.append(build_overview_item(stock_name, detail))
        all_data["overview"][params["id"]] = overview_list

    # 3. 为每只股票生成参数扫描数据
    for stock_name, csv_file in stocks:
        print(f"  生成参数扫描: {stock_name}...")
        sweep_list = []
        for params in PARAM_SETS:
            csv_path = os.path.join(DATA_DIR, csv_file)
            df, trade_df, metrics = run_strategy(
                csv_path,
                entry_period=params["entry"],
                exit_period=params["exit"],
                atr_period=params["atr"],
                stop_atr_mult=params["stop"],
            )
            sweep_list.append({
                "label": params["label"],
                "cumulative_return": safe_float(metrics["cumulative_return"]),
                "sharpe_ratio":      safe_float(metrics["sharpe_ratio"]),
                "max_drawdown":      safe_float(metrics["max_drawdown"]),
                "win_rate":          safe_float(metrics["win_rate"]),
                "buy_count":         int(metrics["buy_count"]),
            })
        all_data["sweeps"][stock_name] = sweep_list

    # 保存JSON
    output_path = os.path.join(DATA_DIR, "data", "all_data.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, separators=(",", ":"))

    file_size = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n数据生成完毕: {output_path}")
    print(f"文件大小: {file_size:.2f} MB")
    print(f"股票数量: {len(all_data['stocks'])}")
    print(f"参数组数: {len(all_data['paramSets'])}")
    print(f"详情数据: {len(all_data['details'])} 只股票")
    print(f"参数扫描: {len(all_data['sweeps'])} 只股票")


if __name__ == "__main__":
    main()
