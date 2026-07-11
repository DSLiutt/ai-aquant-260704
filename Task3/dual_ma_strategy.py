"""
双均线策略回测引擎
====================
实现双均线交叉策略的核心逻辑，包括：
- 加载股价数据
- 计算短/长周期均线
- 生成买卖信号（金叉/死叉）
- 模拟回测交易
- 计算量化指标（MDD、Sharpe Ratio、累计回报等）
"""

import pandas as pd
import numpy as np
import os

# ========== 1. 数据加载 ==========

def load_stock_data(csv_path):
    """加载CSV格式的股价数据"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    # 统一日期格式
    df["trade_date"] = df["trade_date"].astype(str).str.replace("-", "")
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    df = df.sort_values("trade_date").reset_index(drop=True)
    return df


# ========== 2. 均线计算 ==========

def calc_moving_averages(df, short_window=5, long_window=15):
    """
    计算短期和长期移动平均线
    short_window: 短均线周期（如5日）
    long_window: 长均线周期（如15日）
    """
    df = df.copy()
    df[f"MA{short_window}"] = df["close"].rolling(window=short_window).mean()
    df[f"MA{long_window}"] = df["close"].rolling(window=long_window).mean()
    return df


# ========== 3. 信号生成 ==========

def generate_signals(df, short_window=5, long_window=15):
    """
    根据双均线交叉生成买卖信号
    金叉（Golden Cross）：短均线从下方穿越长均线 → 买入信号(+1)
    死叉（Death Cross）：短均线从上方穿越长均线 → 卖出信号(-1)
    """
    df = df.copy()
    ma_short = f"MA{short_window}"
    ma_long = f"MA{long_window}"

    # 判断短均线是否在长均线上方
    df["ma_diff"] = df[ma_short] - df[ma_long]
    # 交叉检测：前一天diff符号与今天不同
    df["ma_diff_prev"] = df["ma_diff"].shift(1)

    # 信号：1=买入(金叉)，-1=卖出(死叉)，0=无操作
    df["signal"] = 0
    # 金叉：前一天短均线在下方，今天在上方
    df.loc[(df["ma_diff_prev"] < 0) & (df["ma_diff"] > 0), "signal"] = 1
    # 死叉：前一天短均线在上方，今天在下方
    df.loc[(df["ma_diff_prev"] > 0) & (df["ma_diff"] < 0), "signal"] = -1

    # 持仓状态：1=持仓，0=空仓
    df["position"] = 0
    current_pos = 0
    for i in range(len(df)):
        if df.loc[i, "signal"] == 1:
            current_pos = 1
        elif df.loc[i, "signal"] == -1:
            current_pos = 0
        df.loc[i, "position"] = current_pos

    return df


# ========== 4. 回测模拟 ==========

def backtest(df, initial_capital=100000):
    """
    模拟交易回测
    策略逻辑：
    - 金叉日以当日收盘价全仓买入
    - 死叉日以当日收盘价全仓卖出
    - 计算策略每日市值与收益率
    """
    df = df.copy()
    capital = float(initial_capital)
    shares = 0.0
    df["strategy_value"] = float(initial_capital)
    df["holdings"] = 0.0
    df["cash"] = float(initial_capital)
    df["trade_price"] = np.nan

    trade_log = []

    for i in range(len(df)):
        price = df.loc[i, "close"]

        if df.loc[i, "signal"] == 1 and shares == 0:
            # 买入：全仓
            shares = float(int(capital // price))
            capital = capital - shares * price
            trade_log.append({
                "date": df.loc[i, "trade_date"],
                "action": "BUY",
                "price": price,
                "shares": int(shares),
                "value": shares * price
            })
            df.loc[i, "trade_price"] = price

        elif df.loc[i, "signal"] == -1 and shares > 0:
            # 卖出：清仓
            capital = capital + shares * price
            trade_log.append({
                "date": df.loc[i, "trade_date"],
                "action": "SELL",
                "price": price,
                "shares": int(shares),
                "value": shares * price
            })
            shares = 0
            df.loc[i, "trade_price"] = price

        # 当日总市值 = 现金 + 持仓市值
        total_value = capital + shares * price
        df.loc[i, "strategy_value"] = total_value
        df.loc[i, "holdings"] = shares * price
        df.loc[i, "cash"] = capital

    # 买入持有基准
    first_price = df.loc[0, "close"]
    bh_shares = float(int(initial_capital // first_price))
    df["buy_hold_value"] = (bh_shares * df["close"]) + (float(initial_capital) - bh_shares * first_price)

    trade_df = pd.DataFrame(trade_log)
    return df, trade_df


# ========== 5. 量化指标计算 ==========

def calc_metrics(df, initial_capital=100000, risk_free_rate=0.02):
    """
    计算策略量化指标
    - 累计回报 (Cumulative Return)
    - 最大回撤 (Maximum Drawdown, MDD)
    - 夏普比率 (Sharpe Ratio)
    - 年化收益率
    - 交易胜率
    """
    metrics = {}

    # --- 策略指标 ---
    final_value = df["strategy_value"].iloc[-1]
    metrics["final_value"] = final_value
    metrics["cumulative_return"] = (final_value - initial_capital) / initial_capital

    # 日收益率
    daily_returns = df["strategy_value"].pct_change().dropna()

    # 年化收益率
    trading_days = len(df)
    if trading_days > 1:
        ann_return = (1 + metrics["cumulative_return"]) ** (252 / trading_days) - 1
    else:
        ann_return = 0
    metrics["annual_return"] = ann_return

    # 最大回撤
    cummax = df["strategy_value"].cummax()
    drawdown = (df["strategy_value"] - cummax) / cummax
    metrics["max_drawdown"] = drawdown.min()

    # 夏普比率
    if daily_returns.std() > 0:
        daily_rf = risk_free_rate / 252
        excess_returns = daily_returns - daily_rf
        sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    else:
        sharpe = 0
    metrics["sharpe_ratio"] = sharpe

    # --- 买入持有基准指标 ---
    bh_final = df["buy_hold_value"].iloc[-1]
    metrics["bh_final_value"] = bh_final
    metrics["bh_cumulative_return"] = (bh_final - initial_capital) / initial_capital

    bh_daily_returns = df["buy_hold_value"].pct_change().dropna()
    bh_cummax = df["buy_hold_value"].cummax()
    bh_drawdown = (df["buy_hold_value"] - bh_cummax) / bh_cummax
    metrics["bh_max_drawdown"] = bh_drawdown.min()

    if bh_daily_returns.std() > 0:
        bh_daily_rf = risk_free_rate / 252
        bh_excess = bh_daily_returns - bh_daily_rf
        metrics["bh_sharpe_ratio"] = np.sqrt(252) * bh_excess.mean() / bh_excess.std()
    else:
        metrics["bh_sharpe_ratio"] = 0

    # 交易次数
    buy_signals = (df["signal"] == 1).sum()
    sell_signals = (df["signal"] == -1).sum()
    metrics["buy_count"] = int(buy_signals)
    metrics["sell_count"] = int(sell_signals)

    return metrics


# ========== 6. 完整策略运行 ==========

def run_strategy(csv_path, short_window=5, long_window=15, initial_capital=100000):
    """
    完整运行双均线策略：加载数据 → 计算均线 → 生成信号 → 回测 → 计算指标
    返回: df(含所有列), trade_df(交易记录), metrics(量化指标)
    """
    df = load_stock_data(csv_path)
    df = calc_moving_averages(df, short_window, long_window)
    df = generate_signals(df, short_window, long_window)
    df, trade_df = backtest(df, initial_capital)
    metrics = calc_metrics(df, initial_capital)
    return df, trade_df, metrics


# ========== 7. 多股票多参数批量测试 ==========

def run_batch_test(data_dir, stocks, param_combos, initial_capital=100000):
    """
    批量运行多股票多参数回测
    stocks: {股票名: csv文件名}
    param_combos: [(短周期, 长周期), ...]
    返回: results_df (所有结果汇总)
    """
    results = []
    detail_data = {}

    for stock_name, csv_file in stocks.items():
        csv_path = os.path.join(data_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"  跳过 {stock_name}: 文件不存在")
            continue

        detail_data[stock_name] = {}

        for short_w, long_w in param_combos:
            df, trade_df, metrics = run_strategy(csv_path, short_w, long_w, initial_capital)
            metrics["stock"] = stock_name
            metrics["short_window"] = short_w
            metrics["long_window"] = long_w
            metrics["param"] = f"MA{short_w}/MA{long_w}"
            results.append(metrics)
            detail_data[stock_name][f"MA{short_w}/MA{long_w}"] = {
                "df": df,
                "trade_df": trade_df,
                "metrics": metrics
            }
            print(f"  {stock_name} | MA{short_w}/MA{long_w} | 累计回报={metrics['cumulative_return']:.2%} | MDD={metrics['max_drawdown']:.2%} | Sharpe={metrics['sharpe_ratio']:.2f}")

    results_df = pd.DataFrame(results)
    return results_df, detail_data


# ========== 主程序入口 ==========

if __name__ == "__main__":
    data_dir = os.path.dirname(os.path.abspath(__file__))

    stocks = {
        "中芯国际": "中芯国际_行情数据.csv",
        "三一重工": "三一重工_行情数据.csv",
        "平安集团": "平安集团_行情数据.csv",
        "贵州茅台": "贵州茅台_行情数据.csv",
        "宁德时代": "宁德时代_行情数据.csv",
        "比亚迪": "比亚迪_行情数据.csv",
    }

    param_combos = [
        (5, 15),
        (5, 20),
        (10, 20),
        (10, 30),
        (5, 30),
    ]

    print("=" * 80)
    print("双均线策略批量回测")
    print("=" * 80)

    results_df, detail_data = run_batch_test(data_dir, stocks, param_combos)

    print("\n" + "=" * 80)
    print("回测结果汇总")
    print("=" * 80)
    display_cols = ["stock", "param", "cumulative_return", "max_drawdown", "sharpe_ratio",
                    "annual_return", "bh_cumulative_return", "bh_max_drawdown", "bh_sharpe_ratio",
                    "buy_count"]
    print(results_df[display_cols].to_string(index=False))

    # 保存结果
    results_df.to_csv(os.path.join(data_dir, "回测结果汇总.csv"), index=False, encoding="utf-8-sig")
    print(f"\n结果已保存至: {os.path.join(data_dir, '回测结果汇总.csv')}")
