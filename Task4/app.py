"""
海龟交易策略 - 交互式Dashboard后端
==================================
Flask API服务器，提供：
- 股票列表查询
- 动态参数回测
- K线+通道+信号数据
- 净值曲线+回撤数据
- 新增/删除股票
"""

import os
import io
import json
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_file, Response

from turtle_strategy import (
    load_stock_data, calc_donchian_channel, calc_atr,
    generate_signals, backtest, calc_metrics, run_strategy
)

app = Flask(__name__, static_folder=".", static_url_path="")

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def get_stock_files():
    """扫描目录下所有行情数据CSV文件"""
    files = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith("_行情数据.csv"):
            name = f.replace("_行情数据.csv", "")
            files.append({"name": name, "filename": f})
    return files


def safe_float(val):
    """安全转换NaN/Inf为None，用于JSON序列化"""
    if val is None:
        return None
    try:
        if np.isnan(val) or np.isinf(val):
            return None
        return round(float(val), 4)
    except (TypeError, ValueError):
        return None


@app.route("/")
def index():
    return send_file("dashboard.html")


@app.route("/api/stocks")
def api_stocks():
    """获取所有可用股票列表"""
    stocks = get_stock_files()
    return jsonify(stocks)


@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    """
    运行回测
    POST body: {
        "stock": "贵州茅台",
        "entry_period": 20,
        "exit_period": 10,
        "atr_period": 20,
        "stop_atr_mult": 2.0,
        "initial_capital": 100000
    }
    """
    params = request.get_json()
    stock_name = params.get("stock", "")
    entry_period = int(params.get("entry_period", 20))
    exit_period = int(params.get("exit_period", 10))
    atr_period = int(params.get("atr_period", 20))
    stop_atr_mult = float(params.get("stop_atr_mult", 2.0))
    initial_capital = float(params.get("initial_capital", 100000))

    csv_path = os.path.join(DATA_DIR, f"{stock_name}_行情数据.csv")
    if not os.path.exists(csv_path):
        return jsonify({"error": f"找不到 {stock_name} 的数据文件"}), 404

    df, trade_df, metrics = run_strategy(
        csv_path, entry_period, exit_period, atr_period,
        stop_atr_mult, initial_capital
    )

    # 准备K线数据
    candles = []
    for _, row in df.iterrows():
        candles.append({
            "date": row["trade_date"].strftime("%Y-%m-%d"),
            "open": safe_float(row["open"]),
            "close": safe_float(row["close"]),
            "low": safe_float(row["low"]),
            "high": safe_float(row["high"]),
            "vol": safe_float(row.get("vol", 0)),
        })

    # 通道数据
    channel = {
        "dates": df["trade_date"].dt.strftime("%Y-%m-%d").tolist(),
        "upper_entry": [safe_float(x) for x in df["upper_entry"].tolist()],
        "lower_entry": [safe_float(x) for x in df["lower_entry"].tolist()],
        "upper_exit": [safe_float(x) for x in df["upper_exit"].tolist()],
        "lower_exit": [safe_float(x) for x in df["lower_exit"].tolist()],
        "atr": [safe_float(x) for x in df["ATR"].tolist()],
    }

    # 买卖信号点
    buy_points = []
    sell_points = []
    for _, row in df.iterrows():
        if row.get("signal") == 1:
            buy_points.append({
                "date": row["trade_date"].strftime("%Y-%m-%d"),
                "price": safe_float(row["close"]),
            })
        elif row.get("signal") == -1:
            sell_points.append({
                "date": row["trade_date"].strftime("%Y-%m-%d"),
                "price": safe_float(row["close"]),
            })

    # 净值曲线
    equity = {
        "dates": df["trade_date"].dt.strftime("%Y-%m-%d").tolist(),
        "strategy": [safe_float(x) for x in df["strategy_value"].tolist()],
        "buy_hold": [safe_float(x) for x in df["buy_hold_value"].tolist()],
    }

    # 回撤曲线
    cummax = df["strategy_value"].cummax()
    drawdown = ((df["strategy_value"] - cummax) / cummax * 100).tolist()
    bh_cummax = df["buy_hold_value"].cummax()
    bh_drawdown = ((df["buy_hold_value"] - bh_cummax) / bh_cummax * 100).tolist()

    drawdown_data = {
        "dates": df["trade_date"].dt.strftime("%Y-%m-%d").tolist(),
        "strategy_dd": [safe_float(x) for x in drawdown],
        "bh_dd": [safe_float(x) for x in bh_drawdown],
    }

    # 交易记录
    trades = []
    if len(trade_df) > 0:
        for _, row in trade_df.iterrows():
            trades.append({
                "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
                "action": row["action"],
                "price": safe_float(row["price"]),
                "shares": int(row["shares"]),
                "value": safe_float(row.get("value", 0)),
                "atr": safe_float(row.get("atr", None)),
                "stop_loss": safe_float(row.get("stop_loss", None)),
            })

    # 指标
    result_metrics = {
        "cumulative_return": safe_float(metrics["cumulative_return"]),
        "annual_return": safe_float(metrics["annual_return"]),
        "max_drawdown": safe_float(metrics["max_drawdown"]),
        "sharpe_ratio": safe_float(metrics["sharpe_ratio"]),
        "win_rate": safe_float(metrics["win_rate"]),
        "buy_count": metrics["buy_count"],
        "sell_count": metrics["sell_count"],
        "final_value": safe_float(metrics["final_value"]),
        "bh_cumulative_return": safe_float(metrics["bh_cumulative_return"]),
        "bh_max_drawdown": safe_float(metrics["bh_max_drawdown"]),
        "bh_sharpe_ratio": safe_float(metrics["bh_sharpe_ratio"]),
        "bh_final_value": safe_float(metrics["bh_final_value"]),
    }

    return jsonify({
        "stock": stock_name,
        "params": {
            "entry_period": entry_period,
            "exit_period": exit_period,
            "atr_period": atr_period,
            "stop_atr_mult": stop_atr_mult,
            "initial_capital": initial_capital,
        },
        "metrics": result_metrics,
        "candles": candles,
        "channel": channel,
        "signals": {"buy": buy_points, "sell": sell_points},
        "equity": equity,
        "drawdown": drawdown_data,
        "trades": trades,
        "total_bars": len(df),
    })


@app.route("/api/backtest_all", methods=["POST"])
def api_backtest_all():
    """
    批量回测所有股票（用于卡片概览）
    POST body: {
        "entry_period": 20,
        "exit_period": 10,
        "atr_period": 20,
        "stop_atr_mult": 2.0,
        "initial_capital": 100000
    }
    """
    params = request.get_json()
    entry_period = int(params.get("entry_period", 20))
    exit_period = int(params.get("exit_period", 10))
    atr_period = int(params.get("atr_period", 20))
    stop_atr_mult = float(params.get("stop_atr_mult", 2.0))
    initial_capital = float(params.get("initial_capital", 100000))

    stocks = get_stock_files()
    results = []

    for s in stocks:
        csv_path = os.path.join(DATA_DIR, s["filename"])
        df, trade_df, metrics = run_strategy(
            csv_path, entry_period, exit_period, atr_period,
            stop_atr_mult, initial_capital
        )

        # 计算净值曲线的采样（每30天取一个点，避免数据过大）
        step = max(1, len(df) // 60)
        equity_sampled = df.iloc[::step]
        sparkline = [safe_float(x) for x in equity_sampled["strategy_value"].tolist()]
        bh_sparkline = [safe_float(x) for x in equity_sampled["buy_hold_value"].tolist()]

        results.append({
            "stock": s["name"],
            "cumulative_return": safe_float(metrics["cumulative_return"]),
            "annual_return": safe_float(metrics["annual_return"]),
            "max_drawdown": safe_float(metrics["max_drawdown"]),
            "sharpe_ratio": safe_float(metrics["sharpe_ratio"]),
            "win_rate": safe_float(metrics["win_rate"]),
            "buy_count": metrics["buy_count"],
            "sell_count": metrics["sell_count"],
            "final_value": safe_float(metrics["final_value"]),
            "bh_cumulative_return": safe_float(metrics["bh_cumulative_return"]),
            "bh_max_drawdown": safe_float(metrics["bh_max_drawdown"]),
            "bh_sharpe_ratio": safe_float(metrics["bh_sharpe_ratio"]),
            "sparkline": sparkline,
            "bh_sparkline": bh_sparkline,
            "dates": equity_sampled["trade_date"].dt.strftime("%Y-%m-%d").tolist(),
        })

    return jsonify(results)


@app.route("/api/stock/add", methods=["POST"])
def api_add_stock():
    """
    新增股票数据（上传CSV）
    POST body (multipart/form-data): file=xxx.csv
    """
    if "file" not in request.files:
        return jsonify({"error": "未收到文件"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "仅支持CSV文件"}), 400

    stock_name = file.filename.replace(".csv", "").replace("_行情数据", "")
    save_path = os.path.join(DATA_DIR, f"{stock_name}_行情数据.csv")
    file.save(save_path)

    # 验证文件格式
    try:
        df = pd.read_csv(save_path, encoding="utf-8-sig")
        required_cols = ["trade_date", "open", "high", "low", "close"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            os.remove(save_path)
            return jsonify({"error": f"CSV缺少必要列: {missing}"}), 400
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({"error": f"文件解析失败: {str(e)}"}), 400

    return jsonify({"success": True, "stock": stock_name, "filename": f"{stock_name}_行情数据.csv"})


@app.route("/api/stock/delete", methods=["POST"])
def api_delete_stock():
    """删除股票数据文件"""
    data = request.get_json()
    stock_name = data.get("stock", "")
    file_path = os.path.join(DATA_DIR, f"{stock_name}_行情数据.csv")
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"success": True})
    return jsonify({"error": "文件不存在"}), 404


@app.route("/api/param_sweep", methods=["POST"])
def api_param_sweep():
    """
    参数扫描：对选定股票进行多参数组合回测
    POST body: {
        "stock": "宁德时代",
        "initial_capital": 100000
    }
    """
    params = request.get_json()
    stock_name = params.get("stock", "")
    initial_capital = float(params.get("initial_capital", 100000))

    csv_path = os.path.join(DATA_DIR, f"{stock_name}_行情数据.csv")
    if not os.path.exists(csv_path):
        return jsonify({"error": f"找不到 {stock_name}"}), 404

    param_combos = [
        (20, 10, 20, 2.0),
        (20, 10, 20, 1.5),
        (20, 10, 20, 3.0),
        (55, 20, 20, 2.0),
        (10, 5, 20, 2.0),
    ]

    results = []
    for entry_p, exit_p, atr_p, stop_m in param_combos:
        df, trade_df, metrics = run_strategy(
            csv_path, entry_p, exit_p, atr_p, stop_m, initial_capital
        )
        results.append({
            "label": f"入{entry_p}/出{exit_p}/止{stop_m}",
            "entry_period": entry_p,
            "exit_period": exit_p,
            "atr_period": atr_p,
            "stop_mult": stop_m,
            "cumulative_return": safe_float(metrics["cumulative_return"]),
            "max_drawdown": safe_float(metrics["max_drawdown"]),
            "sharpe_ratio": safe_float(metrics["sharpe_ratio"]),
            "win_rate": safe_float(metrics["win_rate"]),
            "buy_count": metrics["buy_count"],
        })

    return jsonify(results)


if __name__ == "__main__":
    print("=" * 60)
    print("  海龟交易策略 - 交互式Dashboard")
    print("  访问地址: http://127.0.0.1:5005")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5005, debug=True)
