"""
海龟交易策略回测引擎
====================
实现海龟交易法则的核心逻辑，包括：
- 加载股价数据
- 计算唐奇安高低点通道（Donchian Channel）
- 计算平均真实波幅（ATR）
- 生成买入/卖出交易信号（突破入场 + 通道突破离场 + ATR 止损）
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


# ========== 2. 高低价格通道（唐奇安通道）==========

def calc_donchian_channel(df, entry_period=20, exit_period=10):
    """
    计算唐奇安高低点通道
    ------------------------------------------------
    海龟策略使用两套通道：
    - 入场通道（entry_period=20）：过去20日的最高价/最低价
      突破上轨 → 买入信号；突破下轨 → 卖出信号
    - 离场通道（exit_period=10）：过去10日的最高价/最低价
      跌破10日最低价 → 多头平仓离场
      突破10日最高价 → 空头平仓离场

    注意：计算时排除当日，使用 shift(1) 避免未来数据
    """
    df = df.copy()
    # 入场通道（20日）
    df["upper_entry"] = df["high"].rolling(window=entry_period).max().shift(1)
    df["lower_entry"] = df["low"].rolling(window=entry_period).min().shift(1)
    # 离场通道（10日）
    df["upper_exit"] = df["high"].rolling(window=exit_period).max().shift(1)
    df["lower_exit"] = df["low"].rolling(window=exit_period).min().shift(1)
    # 通道中线
    df["channel_mid"] = (df["upper_entry"] + df["lower_entry"]) / 2
    return df


# ========== 3. 平均真实波幅（ATR）==========

def calc_atr(df, period=20):
    """
    计算平均真实波幅（ATR）
    ------------------------------------------------
    真实波幅（True Range, TR）衡量当日价格波动的最大幅度：
      TR = max(
          high - low,                    # 当日振幅
          |high - prev_close|,           # 当日最高价与前收盘的差距
          |low - prev_close|             # 当日最低价与前收盘的差距
      )

    ATR = TR 的 N 日移动平均（海龟策略默认使用20日）

    ATR 的作用：
    1. 动态止损：止损价 = 买入价 - 2 × ATR
    2. 仓位管理：每手合约风险 = ATR × 合约乘数
       仓位单位 = (总资金 × 风险比例) / (ATR × 合约乘数)
    3. 加仓规则：每上涨 0.5 × ATR 加仓一个单位
    """
    df = df.copy()
    # 前一日收盘价
    prev_close = df["close"].shift(1)
    # 三种波动幅度
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - prev_close).abs()
    tr3 = (df["low"] - prev_close).abs()
    # 真实波幅取三者最大值
    df["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # ATR = TR 的 N 日移动平均
    df["ATR"] = df["TR"].rolling(window=period).mean()
    return df


# ========== 4. 交易信号生成 ==========

def generate_signals(df, entry_period=20, exit_period=10, atr_period=20, stop_atr_mult=2.0):
    """
    生成海龟策略交易信号
    ------------------------------------------------
    买入条件：当日收盘价 > 入场通道上轨（突破20日新高）
    卖出条件（满足任一即卖出）：
      1. 当日收盘价 < 离场通道下轨（跌破10日新低）
      2. 当日收盘价 < 止损价（跌破 买入价 - 2×ATR）

    signal: 1=买入, -1=卖出, 0=无操作
    position: 1=持仓, 0=空仓
    """
    df = df.copy()
    df["signal"] = 0
    df["position"] = 0
    df["stop_loss"] = np.nan  # 止损价
    df["entry_price"] = np.nan  # 买入价

    current_pos = 0
    entry_price = 0.0
    stop_price = 0.0

    for i in range(len(df)):
        if pd.isna(df.loc[i, "upper_entry"]) or pd.isna(df.loc[i, "ATR"]):
            df.loc[i, "position"] = current_pos
            continue

        close = df.loc[i, "close"]
        atr = df.loc[i, "ATR"]

        if current_pos == 0:
            # 空仓 → 判断是否买入（突破入场通道上轨）
            if close > df.loc[i, "upper_entry"]:
                df.loc[i, "signal"] = 1
                current_pos = 1
                entry_price = close
                stop_price = close - stop_atr_mult * atr  # 止损价 = 买入价 - 2×ATR
                df.loc[i, "entry_price"] = entry_price
                df.loc[i, "stop_loss"] = stop_price

        elif current_pos == 1:
            # 持仓 → 判断是否卖出
            # 条件1：跌破离场通道下轨（10日最低价）
            exit_signal = False
            if close < df.loc[i, "lower_exit"]:
                exit_signal = True
            # 条件2：触及止损价
            elif close < stop_price:
                exit_signal = True

            if exit_signal:
                df.loc[i, "signal"] = -1
                current_pos = 0
                entry_price = 0.0
                stop_price = 0.0

        df.loc[i, "position"] = current_pos
        # 持仓期间持续更新止损价记录
        if current_pos == 1 and pd.isna(df.loc[i, "stop_loss"]):
            df.loc[i, "stop_loss"] = stop_price
            df.loc[i, "entry_price"] = entry_price

    return df


# ========== 5. 回测模拟 ==========

def backtest(df, initial_capital=100000, risk_ratio=0.02):
    """
    海龟策略模拟交易回测
    ------------------------------------------------
    资金管理（海龟法则核心）：
    - 每笔交易最大风险 = 总资金 × risk_ratio（默认2%）
    - 买入手数 = 仓位风险金额 / (ATR × 每股风险因子)
      此处简化为：买入手数 = (总资金 × risk_ratio) / (ATR × stop_mult)
    - 全仓进出模式（简化版，便于与双均线策略对比）

    回测逻辑：
    - 买入信号日以当日收盘价建仓
    - 卖出信号日以当日收盘价清仓
    - 每日更新策略市值
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
            # 买入：全仓建仓
            shares = float(int(capital // price))
            capital = capital - shares * price
            trade_log.append({
                "date": df.loc[i, "trade_date"],
                "action": "BUY",
                "price": price,
                "shares": int(shares),
                "value": shares * price,
                "atr": df.loc[i, "ATR"],
                "stop_loss": df.loc[i, "stop_loss"]
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


# ========== 6. 量化指标计算 ==========

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

    # 交易统计
    buy_signals = (df["signal"] == 1).sum()
    sell_signals = (df["signal"] == -1).sum()
    metrics["buy_count"] = int(buy_signals)
    metrics["sell_count"] = int(sell_signals)

    # 交易胜率（通过交易记录计算）
    buy_prices = df.loc[df["signal"] == 1, "close"].values
    sell_prices = df.loc[df["signal"] == -1, "close"].values
    if len(buy_prices) > 0 and len(sell_prices) > 0:
        min_len = min(len(buy_prices), len(sell_prices))
        wins = (sell_prices[:min_len] > buy_prices[:min_len]).sum()
        metrics["win_rate"] = wins / min_len if min_len > 0 else 0
    else:
        metrics["win_rate"] = 0

    return metrics


# ========== 7. 完整策略运行 ==========

def run_strategy(csv_path, entry_period=20, exit_period=10, atr_period=20,
                 stop_atr_mult=2.0, initial_capital=100000):
    """
    完整运行海龟交易策略：
    加载数据 → 计算通道 → 计算ATR → 生成信号 → 回测 → 计算指标
    返回: df(含所有列), trade_df(交易记录), metrics(量化指标)
    """
    df = load_stock_data(csv_path)
    df = calc_donchian_channel(df, entry_period, exit_period)
    df = calc_atr(df, atr_period)
    df = generate_signals(df, entry_period, exit_period, atr_period, stop_atr_mult)
    df, trade_df = backtest(df, initial_capital)
    metrics = calc_metrics(df, initial_capital)
    return df, trade_df, metrics


# ========== 8. 多股票多参数批量测试 ==========

def run_batch_test(data_dir, stocks, param_combos, initial_capital=100000):
    """
    批量运行多股票多参数回测
    stocks: {股票名: csv文件名}
    param_combos: [(entry_period, exit_period, atr_period, stop_mult), ...]
    """
    results = []
    detail_data = {}

    for stock_name, csv_file in stocks.items():
        csv_path = os.path.join(data_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"  跳过 {stock_name}: 文件不存在")
            continue

        detail_data[stock_name] = {}

        for entry_p, exit_p, atr_p, stop_m in param_combos:
            df, trade_df, metrics = run_strategy(
                csv_path, entry_p, exit_p, atr_p, stop_m, initial_capital
            )
            metrics["stock"] = stock_name
            metrics["entry_period"] = entry_p
            metrics["exit_period"] = exit_p
            metrics["atr_period"] = atr_p
            metrics["stop_mult"] = stop_m
            metrics["param"] = f"入{entry_p}/出{exit_p}/ATR{atr_p}/止{stop_m}"
            results.append(metrics)
            detail_data[stock_name][metrics["param"]] = {
                "df": df,
                "trade_df": trade_df,
                "metrics": metrics
            }
            print(f"  {stock_name} | 入{entry_p}/出{exit_p}/ATR{atr_p}/止{stop_m} | "
                  f"累计回报={metrics['cumulative_return']:.2%} | "
                  f"MDD={metrics['max_drawdown']:.2%} | "
                  f"Sharpe={metrics['sharpe_ratio']:.2f}")

    results_df = pd.DataFrame(results)
    return results_df, detail_data


# ========== 主程序入口 ==========

if __name__ == "__main__":
    data_dir = os.path.dirname(os.path.abspath(__file__))

    stocks = {
        "贵州茅台": "贵州茅台_行情数据.csv",
        "比亚迪": "比亚迪_行情数据.csv",
        "宁德时代": "宁德时代_行情数据.csv",
        "中芯国际": "中芯国际_行情数据.csv",
        "三一重工": "三一重工_行情数据.csv",
        "平安集团": "平安集团_行情数据.csv",
    }

    param_combos = [
        (20, 10, 20, 2.0),   # 经典海龟参数
        (20, 10, 20, 1.5),   # 更紧止损
        (20, 10, 20, 3.0),   # 更宽止损
        (55, 20, 20, 2.0),   # 长周期通道
        (10, 5, 20, 2.0),    # 短周期通道
    ]

    print("=" * 80)
    print("海龟交易策略批量回测")
    print("=" * 80)

    results_df, detail_data = run_batch_test(data_dir, stocks, param_combos)

    print("\n" + "=" * 80)
    print("回测结果汇总")
    print("=" * 80)
    display_cols = ["stock", "param", "cumulative_return", "max_drawdown", "sharpe_ratio",
                    "annual_return", "win_rate", "buy_count",
                    "bh_cumulative_return", "bh_max_drawdown", "bh_sharpe_ratio"]
    print(results_df[display_cols].to_string(index=False))

    # 保存结果
    results_df.to_csv(os.path.join(data_dir, "海龟策略回测结果.csv"), index=False, encoding="utf-8-sig")
    print(f"\n结果已保存至: {os.path.join(data_dir, '海龟策略回测结果.csv')}")
