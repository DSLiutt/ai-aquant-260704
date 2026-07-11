"""
海龟交易策略可视化模块
=====================
生成以下可视化图表：
1. 股价与唐奇安高低点通道
2. ATR 波动率图
3. 交易信号标记图（买卖点 + 止损线）
4. 策略净值 vs 买入持有对比
5. 回撤曲线
6. 多股票多参数对比图
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import os
import json
from turtle_strategy import run_strategy

# 中文显示
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "PingFang SC"]
plt.rcParams["axes.unicode_minus"] = False

# 配色（中国股市惯例：红涨绿跌）
COLOR_UP = "#E74C3C"       # 红色 - 涨
COLOR_DOWN = "#27AE60"     # 绿色 - 跌
COLOR_BUY = "#E74C3C"      # 买入 - 红
COLOR_SELL = "#27AE60"     # 卖出 - 绿
COLOR_CHANNEL = "#3498DB"  # 通道 - 蓝
COLOR_ATR = "#F39C12"      # ATR - 橙
COLOR_STRATEGY = "#8E44AD" # 策略净值 - 紫
COLOR_BH = "#95A5A6"       # 买入持有 - 灰
COLOR_STOP = "#E67E22"     # 止损 - 橙红
COLOR_FILL = "#D5F5E3"     # 填充 - 浅绿


def plot_price_channel(df, stock_name, save_path):
    """图1：股价与唐奇安高低点通道"""
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df["trade_date"], df["close"], color="#2C3E50", linewidth=1.2, label="收盘价")
    ax.plot(df["trade_date"], df["upper_entry"], color=COLOR_CHANNEL, linewidth=1,
            linestyle="--", label="20日最高价通道（入场上轨）", alpha=0.8)
    ax.plot(df["trade_date"], df["lower_entry"], color=COLOR_CHANNEL, linewidth=1,
            linestyle="--", label="20日最低价通道（入场下轨）", alpha=0.8)
    ax.plot(df["trade_date"], df["lower_exit"], color=COLOR_DOWN, linewidth=1,
            linestyle=":", label="10日最低价通道（离场下轨）", alpha=0.8)

    # 通道填充
    ax.fill_between(df["trade_date"], df["upper_entry"], df["lower_entry"],
                    color=COLOR_CHANNEL, alpha=0.06)

    ax.set_title(f"{stock_name} - 股价与唐奇安高低点通道", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.set_ylabel("价格（元）")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def plot_atr(df, stock_name, save_path):
    """图2：ATR 波动率图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw={"height_ratios": [2, 1]})

    # 上图：股价
    ax1.plot(df["trade_date"], df["close"], color="#2C3E50", linewidth=1.2, label="收盘价")
    ax1.set_ylabel("价格（元）")
    ax1.set_title(f"{stock_name} - 股价与ATR波动率", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # 下图：ATR
    ax2.plot(df["trade_date"], df["ATR"], color=COLOR_ATR, linewidth=1.5, label="ATR(20)")
    ax2.fill_between(df["trade_date"], 0, df["ATR"], color=COLOR_ATR, alpha=0.15)
    ax2.set_xlabel("日期")
    ax2.set_ylabel("ATR")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def plot_signals(df, trade_df, stock_name, save_path):
    """图3：交易信号标记图"""
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df["trade_date"], df["close"], color="#2C3E50", linewidth=1, label="收盘价", alpha=0.7)
    ax.plot(df["trade_date"], df["upper_entry"], color=COLOR_CHANNEL, linewidth=0.8,
            linestyle="--", label="20日上轨", alpha=0.6)
    ax.plot(df["trade_date"], df["lower_exit"], color=COLOR_DOWN, linewidth=0.8,
            linestyle=":", label="10日下轨", alpha=0.6)

    # 标记买入信号
    buy_signals = df[df["signal"] == 1]
    sell_signals = df[df["signal"] == -1]

    if len(buy_signals) > 0:
        ax.scatter(buy_signals["trade_date"], buy_signals["close"],
                   color=COLOR_BUY, marker="^", s=120, zorder=5,
                   label=f"买入信号({len(buy_signals)}次)")
    if len(sell_signals) > 0:
        ax.scatter(sell_signals["trade_date"], sell_signals["close"],
                   color=COLOR_SELL, marker="v", s=120, zorder=5,
                   label=f"卖出信号({len(sell_signals)}次)")

    # 止损线
    stop_data = df[df["stop_loss"].notna()]
    if len(stop_data) > 0:
        ax.plot(stop_data["trade_date"], stop_data["stop_loss"],
                color=COLOR_STOP, linewidth=0.8, linestyle="-.", alpha=0.5, label="止损线(2×ATR)")

    ax.set_title(f"{stock_name} - 海龟策略交易信号", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.set_ylabel("价格（元）")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def plot_strategy_vs_buyhold(df, stock_name, save_path, initial_capital=100000):
    """图4：策略净值 vs 买入持有对比"""
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df["trade_date"], df["strategy_value"],
            color=COLOR_STRATEGY, linewidth=1.5, label="海龟策略净值")
    ax.plot(df["trade_date"], df["buy_hold_value"],
            color=COLOR_BH, linewidth=1.5, linestyle="--", label="买入持有基准")

    # 填充策略超出买入持有的部分
    ax.fill_between(df["trade_date"], df["buy_hold_value"], df["strategy_value"],
                    where=df["strategy_value"] >= df["buy_hold_value"],
                    color=COLOR_STRATEGY, alpha=0.15, label="策略超额收益")
    ax.fill_between(df["trade_date"], df["buy_hold_value"], df["strategy_value"],
                    where=df["strategy_value"] < df["buy_hold_value"],
                    color=COLOR_BH, alpha=0.15, label="策略低于基准")

    ax.axhline(y=initial_capital, color="gray", linestyle=":", alpha=0.5, label="初始资金")

    ax.set_title(f"{stock_name} - 海龟策略净值 vs 买入持有", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.set_ylabel("市值（元）")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def plot_drawdown(df, stock_name, save_path):
    """图5：回撤曲线"""
    fig, ax = plt.subplots(figsize=(14, 5))

    cummax = df["strategy_value"].cummax()
    drawdown = (df["strategy_value"] - cummax) / cummax * 100

    bh_cummax = df["buy_hold_value"].cummax()
    bh_drawdown = (df["buy_hold_value"] - bh_cummax) / bh_cummax * 100

    ax.fill_between(df["trade_date"], drawdown, 0,
                    color=COLOR_STRATEGY, alpha=0.3, label="海龟策略回撤")
    ax.plot(df["trade_date"], drawdown, color=COLOR_STRATEGY, linewidth=1)

    ax.fill_between(df["trade_date"], bh_drawdown, 0,
                    color=COLOR_BH, alpha=0.15, label="买入持有回撤")
    ax.plot(df["trade_date"], bh_drawdown, color=COLOR_BH, linewidth=1, linestyle="--")

    ax.set_title(f"{stock_name} - 策略回撤对比", fontsize=14, fontweight="bold")
    ax.set_xlabel("日期")
    ax.set_ylabel("回撤幅度（%）")
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def plot_multi_stock_comparison(results_df, save_path):
    """图6：多股票策略表现对比"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # 只取经典参数（入20/出10/ATR20/止2.0）
    classic = results_df[results_df["param"] == "入20/出10/ATR20/止2.0"].copy()

    if len(classic) == 0:
        classic = results_df.iloc[:6].copy()

    stocks = classic["stock"].tolist()
    x = np.arange(len(stocks))
    width = 0.35

    # 累计回报对比
    ax = axes[0]
    bars1 = ax.bar(x - width/2, classic["cumulative_return"] * 100, width,
                   color=COLOR_STRATEGY, label="海龟策略", alpha=0.85)
    bars2 = ax.bar(x + width/2, classic["bh_cumulative_return"] * 100, width,
                   color=COLOR_BH, label="买入持有", alpha=0.85)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.set_title("累计回报对比（%）", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(stocks, rotation=45, fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # 最大回撤对比
    ax = axes[1]
    ax.bar(x - width/2, classic["max_drawdown"] * 100, width,
           color=COLOR_STRATEGY, label="海龟策略", alpha=0.85)
    ax.bar(x + width/2, classic["bh_max_drawdown"] * 100, width,
           color=COLOR_BH, label="买入持有", alpha=0.85)
    ax.set_title("最大回撤对比（%）", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(stocks, rotation=45, fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # 夏普比率对比
    ax = axes[2]
    ax.bar(x - width/2, classic["sharpe_ratio"], width,
           color=COLOR_STRATEGY, label="海龟策略", alpha=0.85)
    ax.bar(x + width/2, classic["bh_sharpe_ratio"], width,
           color=COLOR_BH, label="买入持有", alpha=0.85)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.set_title("夏普比率对比", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(stocks, rotation=45, fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("海龟策略 vs 买入持有 - 多股票对比（经典参数 20/10/20/2.0）",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def plot_param_comparison(results_df, stock_name, save_path):
    """图7：参数敏感性分析"""
    stock_data = results_df[results_df["stock"] == stock_name].copy()
    if len(stock_data) == 0:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    params = stock_data["param"].tolist()
    x = np.arange(len(params))
    width = 0.35

    # 累计回报
    ax = axes[0]
    ax.bar(x - width/2, stock_data["cumulative_return"] * 100, width,
           color=COLOR_STRATEGY, label="海龟策略", alpha=0.85)
    ax.bar(x + width/2, stock_data["bh_cumulative_return"] * 100, width,
           color=COLOR_BH, label="买入持有", alpha=0.85)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.set_title("累计回报（%）", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(params, rotation=45, fontsize=8, ha="right")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # 最大回撤
    ax = axes[1]
    ax.bar(x, stock_data["max_drawdown"] * 100, width*1.5,
           color=COLOR_DOWN, alpha=0.85)
    ax.set_title("最大回撤（%）", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(params, rotation=45, fontsize=8, ha="right")
    ax.grid(True, alpha=0.3, axis="y")

    # 夏普比率
    ax = axes[2]
    ax.bar(x, stock_data["sharpe_ratio"], width*1.5,
           color=COLOR_ATR, alpha=0.85)
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.set_title("夏普比率", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(params, rotation=45, fontsize=8, ha="right")
    ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle(f"{stock_name} - 参数敏感性分析", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [saved] {save_path}")


def generate_all_charts(data_dir, charts_dir):
    """生成所有可视化图表"""

    stocks = {
        "贵州茅台": "贵州茅台_行情数据.csv",
        "比亚迪": "比亚迪_行情数据.csv",
        "宁德时代": "宁德时代_行情数据.csv",
        "中芯国际": "中芯国际_行情数据.csv",
        "三一重工": "三一重工_行情数据.csv",
        "平安集团": "平安集团_行情数据.csv",
        "中国卫星": "中国卫星_行情数据.csv",
        "航天电子": "航天电子_行情数据.csv",
        "航天动力": "航天动力_行情数据.csv",
    }

    param_combos = [
        (20, 10, 20, 2.0),   # 经典海龟参数
        (20, 10, 20, 1.5),   # 更紧止损
        (20, 10, 20, 3.0),   # 更宽止损
        (55, 20, 20, 2.0),   # 长周期通道
        (10, 5, 20, 2.0),    # 短周期通道
    ]

    # 收集批量结果
    all_results = []
    all_detail = {}

    print("=" * 60)
    print("生成海龟策略可视化图表")
    print("=" * 60)

    for stock_name, csv_file in stocks.items():
        csv_path = os.path.join(data_dir, csv_file)
        print(f"\n--- {stock_name} ---")

        # 经典参数运行
        df, trade_df, metrics = run_strategy(
            csv_path, entry_period=20, exit_period=10,
            atr_period=20, stop_atr_mult=2.0
        )

        all_detail[stock_name] = {"df": df, "trade_df": trade_df, "metrics": metrics}

        # 图1：股价与通道
        plot_price_channel(df, stock_name,
                          os.path.join(charts_dir, f"{stock_name}_通道图.png"))

        # 图2：ATR
        plot_atr(df, stock_name,
                os.path.join(charts_dir, f"{stock_name}_ATR.png"))

        # 图3：交易信号
        plot_signals(df, trade_df, stock_name,
                    os.path.join(charts_dir, f"{stock_name}_交易信号.png"))

        # 图4：策略净值 vs 买入持有
        plot_strategy_vs_buyhold(df, stock_name,
                                 os.path.join(charts_dir, f"{stock_name}_净值对比.png"))

        # 图5：回撤曲线
        plot_drawdown(df, stock_name,
                     os.path.join(charts_dir, f"{stock_name}_回撤.png"))

        # 参数敏感性（多参数跑一次）
        for entry_p, exit_p, atr_p, stop_m in param_combos:
            df_p, trade_p, metrics_p = run_strategy(
                csv_path, entry_p, exit_p, atr_p, stop_m
            )
            metrics_p["stock"] = stock_name
            metrics_p["param"] = f"入{entry_p}/出{exit_p}/ATR{atr_p}/止{stop_m}"
            all_results.append(metrics_p)

    results_df = pd.DataFrame(all_results)

    # 图6：多股票对比
    plot_multi_stock_comparison(results_df,
                               os.path.join(charts_dir, "多股票对比.png"))

    # 图7：参数敏感性分析（选茅台和比亚迪作为代表）
    plot_param_comparison(results_df, "贵州茅台",
                         os.path.join(charts_dir, "茅台_参数敏感性.png"))
    plot_param_comparison(results_df, "比亚迪",
                         os.path.join(charts_dir, "比亚迪_参数敏感性.png"))

    return results_df, all_detail


if __name__ == "__main__":
    data_dir = os.path.dirname(os.path.abspath(__file__))
    charts_dir = os.path.join(data_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    results_df, detail_data = generate_all_charts(data_dir, charts_dir)

    # 保存汇总数据为JSON
    summary = {}
    for stock, data in detail_data.items():
        m = data["metrics"]
        summary[stock] = {
            "cumulative_return": float(m["cumulative_return"]),
            "max_drawdown": float(m["max_drawdown"]),
            "sharpe_ratio": float(m["sharpe_ratio"]),
            "annual_return": float(m["annual_return"]),
            "win_rate": float(m["win_rate"]),
            "buy_count": m["buy_count"],
            "sell_count": m["sell_count"],
            "bh_cumulative_return": float(m["bh_cumulative_return"]),
            "bh_max_drawdown": float(m["bh_max_drawdown"]),
            "bh_sharpe_ratio": float(m["bh_sharpe_ratio"]),
            "trades": data["trade_df"].to_dict("records") if len(data["trade_df"]) > 0 else [],
        }

    with open(os.path.join(data_dir, "strategy_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    # 保存参数测试结果
    results_df.to_csv(os.path.join(data_dir, "海龟策略回测结果.csv"),
                      index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("所有图表和数据生成完毕！")
    print(f"  图表目录: {charts_dir}")
    print(f"  汇总JSON: {os.path.join(data_dir, 'strategy_summary.json')}")
    print(f"  回测CSV: {os.path.join(data_dir, '海龟策略回测结果.csv')}")
    print("=" * 60)
