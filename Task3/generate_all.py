"""
生成所有可视化图表和数据文件
用于 Notebook、HTML页面、PDF报告
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings("ignore")

# 中文字体配置
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "Heiti TC", "PingFang SC", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 导入策略引擎
from dual_ma_strategy import run_strategy, run_batch_test, load_stock_data, calc_moving_averages, generate_signals, backtest, calc_metrics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# 中国股市颜色惯例：涨红跌绿
RED = "#E0364D"
GREEN = "#16A34A"
BLUE = "#2563EB"
ORANGE = "#F59E0B"
PURPLE = "#7C3AED"
GRAY = "#6B7280"

STOCKS = {
    "中芯国际": "中芯国际_行情数据.csv",
    "三一重工": "三一重工_行情数据.csv",
    "平安集团": "平安集团_行情数据.csv",
    "贵州茅台": "贵州茅台_行情数据.csv",
    "宁德时代": "宁德时代_行情数据.csv",
    "比亚迪": "比亚迪_行情数据.csv",
}

PARAM_COMBOS = [
    (5, 15),
    (5, 20),
    (10, 20),
    (10, 30),
    (5, 30),
]

# 默认展示的股票和参数
DEFAULT_STOCK = "中芯国际"
DEFAULT_SHORT = 5
DEFAULT_LONG = 15


def fmt_date(d):
    return pd.Timestamp(d).strftime("%Y-%m-%d")


# ============================================================
# 1. 默认股票的完整策略图表（股价+均线+买卖信号）
# ============================================================
def chart_strategy_overview(stock_name, csv_file, short_w, long_w):
    """绘制策略总览图：股价、长短均线、买卖信号标记"""
    csv_path = os.path.join(BASE_DIR, csv_file)
    df, trade_df, metrics = run_strategy(csv_path, short_w, long_w)

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), height_ratios=[3, 1.2],
                              sharex=True, gridspec_kw={"hspace": 0.08})

    ax1 = axes[0]
    ax1.plot(df["trade_date"], df["close"], color=GRAY, linewidth=1.2, label="收盘价", zorder=2)
    ax1.plot(df["trade_date"], df[f"MA{short_w}"], color=BLUE, linewidth=1.5, label=f"MA{short_w}(短均线)", zorder=3)
    ax1.plot(df["trade_date"], df[f"MA{long_w}"], color=ORANGE, linewidth=1.5, label=f"MA{long_w}(长均线)", zorder=3)

    # 标记买入信号
    buy_signals = df[df["signal"] == 1]
    sell_signals = df[df["signal"] == -1]

    if len(buy_signals) > 0:
        ax1.scatter(buy_signals["trade_date"], buy_signals["close"],
                   color=RED, marker="^", s=120, zorder=5, label="买入信号(金叉)", edgecolors="white", linewidths=0.5)
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals["trade_date"], sell_signals["close"],
                   color=GREEN, marker="v", s=120, zorder=5, label="卖出信号(死叉)", edgecolors="white", linewidths=0.5)

    ax1.set_title(f"{stock_name} 双均线策略 (MA{short_w}/MA{long_w})", fontsize=15, fontweight="bold", pad=12)
    ax1.set_ylabel("股价 (元)", fontsize=12)
    ax1.legend(loc="upper left", fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.fill_between(df["trade_date"], df["close"].min()*0.95, df["close"],
                    where=(df["position"]==1), alpha=0.08, color=RED, label="持仓区间")

    # 下方：成交量
    ax2 = axes[1]
    colors = [RED if df.loc[i, "pct_chg"] >= 0 else GREEN for i in range(len(df))]
    ax2.bar(df["trade_date"], df["vol"]/10000, color=colors, alpha=0.6, width=1)
    ax2.set_ylabel("成交量 (万手)", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)

    plt.tight_layout()
    path = os.path.join(CHART_DIR, f"{stock_name}_MA{short_w}_{long_w}_策略总览.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path, df, trade_df, metrics


# ============================================================
# 2. 策略收益 vs 买入持有 对比图
# ============================================================
def chart_returns_comparison(stock_name, csv_file, short_w, long_w):
    """策略市值 vs 买入持有市值对比"""
    csv_path = os.path.join(BASE_DIR, csv_file)
    df, trade_df, metrics = run_strategy(csv_path, short_w, long_w)

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df["trade_date"], df["strategy_value"], color=RED, linewidth=2,
           label=f"双均线策略 (¥{metrics['final_value']:,.0f})", zorder=3)
    ax.plot(df["trade_date"], df["buy_hold_value"], color=BLUE, linewidth=2,
           label=f"买入持有 (¥{metrics['bh_final_value']:,.0f})", zorder=3, linestyle="--")
    ax.axhline(y=100000, color=GRAY, linewidth=1, linestyle=":", alpha=0.5, label="初始资金(¥100,000)")

    # 标记买卖点
    for _, t in trade_df.iterrows():
        if t["action"] == "BUY":
            val = df[df["trade_date"] == t["date"]]["strategy_value"].iloc[0]
            ax.scatter(t["date"], val, color=RED, marker="^", s=80, zorder=5, edgecolors="white")
        else:
            val = df[df["trade_date"] == t["date"]]["strategy_value"].iloc[0]
            ax.scatter(t["date"], val, color=GREEN, marker="v", s=80, zorder=5, edgecolors="white")

    ax.set_title(f"{stock_name} 策略收益 vs 买入持有 (MA{short_w}/MA{long_w})", fontsize=15, fontweight="bold", pad=12)
    ax.set_ylabel("市值 (¥)", fontsize=12)
    ax.set_xlabel("日期", fontsize=12)
    ax.legend(loc="upper left", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"¥{x:,.0f}"))
    plt.xticks(rotation=30)
    plt.tight_layout()

    path = os.path.join(CHART_DIR, f"{stock_name}_MA{short_w}_{long_w}_收益对比.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============================================================
# 3. 回撤图
# ============================================================
def chart_drawdown(stock_name, csv_file, short_w, long_w):
    """绘制策略和买入持有的回撤对比"""
    csv_path = os.path.join(BASE_DIR, csv_file)
    df, trade_df, metrics = run_strategy(csv_path, short_w, long_w)

    fig, ax = plt.subplots(figsize=(14, 5))

    # 策略回撤
    cummax_s = df["strategy_value"].cummax()
    dd_s = (df["strategy_value"] - cummax_s) / cummax_s * 100
    ax.fill_between(df["trade_date"], dd_s, 0, color=RED, alpha=0.3, label=f"策略回撤 (MDD={metrics['max_drawdown']:.1%})")
    ax.plot(df["trade_date"], dd_s, color=RED, linewidth=1)

    # 买入持有回撤
    cummax_bh = df["buy_hold_value"].cummax()
    dd_bh = (df["buy_hold_value"] - cummax_bh) / cummax_bh * 100
    ax.plot(df["trade_date"], dd_bh, color=BLUE, linewidth=1.5, linestyle="--",
           label=f"买入持有回撤 (MDD={metrics['bh_max_drawdown']:.1%})")

    ax.set_title(f"{stock_name} 最大回撤对比 (MA{short_w}/MA{long_w})", fontsize=15, fontweight="bold", pad=12)
    ax.set_ylabel("回撤 (%)", fontsize=12)
    ax.set_xlabel("日期", fontsize=12)
    ax.legend(loc="lower left", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()

    path = os.path.join(CHART_DIR, f"{stock_name}_MA{short_w}_{long_w}_回撤.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============================================================
# 4. 多股票参数对比柱状图
# ============================================================
def chart_multi_comparison(results_df):
    """多股票多参数累计回报对比"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # 左图：累计回报
    ax1 = axes[0]
    pivot_ret = results_df.pivot(index="stock", columns="param", values="cumulative_return")
    pivot_ret = pivot_ret * 100
    pivot_ret.plot(kind="bar", ax=ax1, width=0.8, edgecolor="white", linewidth=0.5)
    ax1.set_title("各股票不同均线参数 — 累计回报 (%)", fontsize=14, fontweight="bold")
    ax1.set_ylabel("累计回报 (%)", fontsize=12)
    ax1.set_xlabel("")
    ax1.axhline(y=0, color="black", linewidth=0.8)
    ax1.legend(title="均线参数", fontsize=9)
    ax1.grid(True, alpha=0.3, axis="y")
    ax1.tick_params(axis="x", rotation=30)

    # 右图：夏普比率
    ax2 = axes[1]
    pivot_sharpe = results_df.pivot(index="stock", columns="param", values="sharpe_ratio")
    pivot_sharpe.plot(kind="bar", ax=ax2, width=0.8, edgecolor="white", linewidth=0.5)
    ax2.set_title("各股票不同均线参数 — 夏普比率", fontsize=14, fontweight="bold")
    ax2.set_ylabel("夏普比率", fontsize=12)
    ax2.set_xlabel("")
    ax2.axhline(y=0, color="black", linewidth=0.8)
    ax2.axhline(y=1, color=GREEN, linewidth=1, linestyle="--", alpha=0.5, label="Sharpe=1")
    ax2.legend(title="均线参数", fontsize=9)
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    path = os.path.join(CHART_DIR, "多股票参数对比.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============================================================
# 5. 策略 vs 买入持有 散点图
# ============================================================
def chart_strategy_vs_bh(results_df):
    """策略收益 vs 买入持有收益散点图"""
    fig, ax = plt.subplots(figsize=(10, 9))

    for stock in results_df["stock"].unique():
        sub = results_df[results_df["stock"] == stock]
        ax.scatter(sub["bh_cumulative_return"]*100, sub["cumulative_return"]*100,
                  s=80, alpha=0.7, label=stock, edgecolors="white", linewidths=0.5)

    # 对角线
    lim_min = min(results_df["bh_cumulative_return"].min(), results_df["cumulative_return"].min()) * 100 - 5
    lim_max = max(results_df["bh_cumulative_return"].max(), results_df["cumulative_return"].max()) * 100 + 5
    ax.plot([lim_min, lim_max], [lim_min, lim_max], "k--", alpha=0.3, linewidth=1, label="策略=买入持有")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.axvline(x=0, color="black", linewidth=0.5)

    ax.set_xlabel("买入持有累计回报 (%)", fontsize=13)
    ax.set_ylabel("双均线策略累计回报 (%)", fontsize=13)
    ax.set_title("双均线策略 vs 买入持有 — 收益对比", fontsize=15, fontweight="bold", pad=12)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(lim_min, lim_max)
    ax.set_ylim(lim_min, lim_max)

    # 添加象限标注
    ax.text(0.97, 0.97, "策略优于买入持有\n且均盈利", transform=ax.transAxes, fontsize=9,
           ha="right", va="top", color=GREEN, alpha=0.6,
           bbox=dict(boxstyle="round,pad=0.3", facecolor=GREEN, alpha=0.1))
    ax.text(0.03, 0.97, "策略跑赢但\n均亏损", transform=ax.transAxes, fontsize=9,
           ha="left", va="top", color=ORANGE, alpha=0.6,
           bbox=dict(boxstyle="round,pad=0.3", facecolor=ORANGE, alpha=0.1))

    plt.tight_layout()
    path = os.path.join(CHART_DIR, "策略vs买入持有散点.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============================================================
# 6. MDD对比图
# ============================================================
def chart_mdd_comparison(results_df):
    """策略MDD vs 买入持有MDD对比"""
    fig, ax = plt.subplots(figsize=(14, 6))

    pivot_mdd = results_df.pivot(index="stock", columns="param", values="max_drawdown")
    pivot_mdd = pivot_mdd * 100
    pivot_mdd.plot(kind="bar", ax=ax, width=0.8, edgecolor="white", linewidth=0.5)
    ax.set_title("各股票不同均线参数 — 最大回撤 (MDD) 对比", fontsize=14, fontweight="bold")
    ax.set_ylabel("最大回撤 (%)", fontsize=12)
    ax.set_xlabel("")
    ax.legend(title="均线参数", fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")
    ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    path = os.path.join(CHART_DIR, "MDD对比.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ============================================================
# 7. 生成JSON数据供HTML页面使用
# ============================================================
def generate_json_data(results_df, detail_data):
    """生成所有JSON数据供ECharts页面使用"""
    json_data = {
        "stocks": {},
        "summary": {},
        "best_params": {}
    }

    # 每只股票的详细数据
    for stock_name in STOCKS:
        if stock_name not in detail_data:
            continue
        stock_data = {"params": {}}
        for param_key, data in detail_data[stock_name].items():
            df = data["df"]
            m = data["metrics"]
            # 取采样以减少数据量（每隔2-3天取一个点）
            step = max(1, len(df) // 200)
            sampled = df.iloc[::step]

            stock_data["params"][param_key] = {
                "dates": [fmt_date(d) for d in sampled["trade_date"]],
                "close": [round(float(x), 2) for x in sampled["close"]],
                "ma_short": [round(float(x), 2) if not np.isnan(x) else None for x in sampled.iloc[:, sampled.columns.get_loc(f"MA{m['short_window']}")]],
                "ma_long": [round(float(x), 2) if not np.isnan(x) else None for x in sampled.iloc[:, sampled.columns.get_loc(f"MA{m['long_window']}")]],
                "strategy_value": [round(float(x), 2) for x in sampled["strategy_value"]],
                "buy_hold_value": [round(float(x), 2) for x in sampled["buy_hold_value"]],
                "position": [int(x) for x in sampled["position"]],
                "signals": [
                    {"date": fmt_date(df.loc[i, "trade_date"]), "type": "buy" if df.loc[i, "signal"] == 1 else "sell", "price": float(df.loc[i, "close"])}
                    for i in range(len(df)) if df.loc[i, "signal"] != 0
                ],
                "metrics": {
                    "cumulative_return": round(m["cumulative_return"] * 100, 2),
                    "max_drawdown": round(m["max_drawdown"] * 100, 2),
                    "sharpe_ratio": round(m["sharpe_ratio"], 2),
                    "annual_return": round(m["annual_return"] * 100, 2),
                    "final_value": round(m["final_value"], 2),
                    "buy_count": m["buy_count"],
                    "bh_cumulative_return": round(m["bh_cumulative_return"] * 100, 2),
                    "bh_max_drawdown": round(m["bh_max_drawdown"] * 100, 2),
                    "bh_sharpe_ratio": round(m["bh_sharpe_ratio"], 2),
                }
            }
        json_data["stocks"][stock_name] = stock_data

    # 汇总数据
    json_data["summary"]["all_results"] = results_df.to_dict("records")
    json_data["summary"]["stock_names"] = list(STOCKS.keys())
    json_data["summary"]["param_combos"] = [f"MA{s}/MA{l}" for s, l in PARAM_COMBOS]

    # 最佳参数
    best = results_df.loc[results_df["sharpe_ratio"].idxmax()]
    json_data["best_params"] = {
        "stock": best["stock"],
        "param": best["param"],
        "cumulative_return": round(best["cumulative_return"] * 100, 2),
        "sharpe_ratio": round(best["sharpe_ratio"], 2),
        "max_drawdown": round(best["max_drawdown"] * 100, 2),
    }

    json_path = os.path.join(BASE_DIR, "backtest_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"JSON数据已保存: {json_path}")
    return json_path


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("生成所有可视化图表和数据")
    print("=" * 60)

    # 运行批量回测
    print("\n[1/8] 运行批量回测...")
    results_df, detail_data = run_batch_test(BASE_DIR, STOCKS, PARAM_COMBOS)

    # 默认股票策略总览图
    print(f"\n[2/8] 生成 {DEFAULT_STOCK} 策略总览图 (MA{DEFAULT_SHORT}/MA{DEFAULT_LONG})...")
    chart_strategy_overview(DEFAULT_STOCK, STOCKS[DEFAULT_STOCK], DEFAULT_SHORT, DEFAULT_LONG)

    # 生成多只股票的策略总览图
    for stock, csv_file in STOCKS.items():
        print(f"  - {stock} 策略总览图...")
        chart_strategy_overview(stock, csv_file, DEFAULT_SHORT, DEFAULT_LONG)

    # 收益对比图
    print(f"\n[3/8] 生成收益对比图...")
    for stock, csv_file in STOCKS.items():
        chart_returns_comparison(stock, csv_file, DEFAULT_SHORT, DEFAULT_LONG)

    # 回撤图
    print(f"\n[4/8] 生成回撤对比图...")
    for stock, csv_file in STOCKS.items():
        chart_drawdown(stock, csv_file, DEFAULT_SHORT, DEFAULT_LONG)

    # 多股票参数对比
    print(f"\n[5/8] 生成多股票参数对比图...")
    chart_multi_comparison(results_df)

    # 策略 vs 买入持有散点
    print(f"\n[6/8] 生成策略vs买入持有散点图...")
    chart_strategy_vs_bh(results_df)

    # MDD对比
    print(f"\n[7/8] 生成MDD对比图...")
    chart_mdd_comparison(results_df)

    # JSON数据
    print(f"\n[8/8] 生成JSON数据...")
    generate_json_data(results_df, detail_data)

    # 保存结果CSV
    results_df.to_csv(os.path.join(BASE_DIR, "回测结果汇总.csv"), index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("所有图表和数据生成完成!")
    print(f"图表目录: {CHART_DIR}")
    print(f"图表数量: {len(os.listdir(CHART_DIR))}")
    print("=" * 60)
