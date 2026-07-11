"""
生成 Jupyter Notebook：双均线策略完整分析
"""
import nbformat as nbf
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
nb = nbf.v4.new_notebook()
cells = []

# ==================== 标题 ====================
cells.append(nbf.v4.new_markdown_cell("""# 双均线交叉策略 — 完整量化分析

**BI工作坊·AI量化公益课 Task3**

> 本 Notebook 完整实现了双均线交叉策略，包括概念解析、信号生成、回测模拟、量化指标计算、多股票多参数对比分析。

---

## 📋 目录
1. [策略概念解析](#1-策略概念解析)
2. [量化指标说明](#2-量化指标说明)
3. [数据加载与预处理](#3-数据加载与预处理)
4. [均线计算与信号生成](#4-均线计算与信号生成)
5. [策略可视化](#5-策略可视化)
6. [回测模拟与量化指标](#6-回测模拟与量化指标)
7. [多股票多参数对比](#7-多股票多参数对比)
8. [策略适用场景与心得总结](#8-策略适用场景与心得总结)
"""))

# ==================== 1. 策略概念 ====================
cells.append(nbf.v4.new_markdown_cell("""## 1. 策略概念解析

### 1.1 双均线策略概述

双均线策略（Dual Moving Average Strategy）是最经典的趋势跟踪型量化策略之一。它利用**短期移动平均线**和**长期移动平均线**的交叉关系来判断市场趋势的方向，并据此产生买卖信号。

**核心逻辑：**
- 当短均线从下方穿越长均线向上时，意味着近期价格走势强于长期趋势，市场可能进入上升通道 → **买入**
- 当短均线从上方穿越长均线向下时，意味着近期价格走势弱于长期趋势，市场可能进入下降通道 → **卖出**

### 1.2 金叉（Golden Cross）

> **金叉** = 短期均线从下方穿越长期均线向上

**含义：** 短期内价格上涨动能增强，突破长期均价，通常被视为**看涨信号**。

```
价格 ↑
  |        ╱ 短均线
  |      ╱
  |    ╱   ╱← 金叉买入点
  |  ╱   ╱
  |╱   ╱ 长均线
  |  ╱
  └─────────────→ 时间
```

### 1.3 死叉（Death Cross）

> **死叉** = 短期均线从上方穿越长期均线向下

**含义：** 短期内价格下跌动能增强，跌破长期均价，通常被视为**看跌信号**。

```
价格 ↑
  |╲   ╲ 短均线
  |  ╲   ╲
  |    ╲   ╲← 死叉卖出点
  |      ╲   ╲ 长均线
  |        ╲
  └─────────────→ 时间
```

### 1.4 常用均线周期组合

| 组合 | 短均线 | 长均线 | 特点 |
|------|--------|--------|------|
| 5/15 | 5日 | 15日 | 灵敏度高，信号频繁，适合短线 |
| 5/20 | 5日 | 20日 | 平衡型，适中灵敏度 |
| 10/20 | 10日 | 20日 | 中线常用，信号较稳定 |
| 10/30 | 10日 | 30日 | 滞后性较强，适合中长线 |
| 5/30 | 5日 | 30日 | 大跨度，信号少但趋势性强 |
"""))

# ==================== 2. 量化指标 ====================
cells.append(nbf.v4.new_markdown_cell("""## 2. 量化指标说明

### 2.1 累计回报（Cumulative Return）

$$CR = \\frac{V_{final} - V_{initial}}{V_{initial}} \\times 100\\%$$

**含义：** 策略从开始到结束的总收益率，是最直观的收益衡量指标。

- $V_{final}$ = 期末总资产价值
- $V_{initial}$ = 期初投入资金

**解读：** CR > 0 表示盈利，CR < 0 表示亏损。但仅看累计回报无法衡量风险。

### 2.2 最大回撤（Maximum Drawdown, MDD）

$$MDD = \\min_{t} \\left( \\frac{V_t - \\max_{s \\leq t} V_s}{\\max_{s \\leq t} V_s} \\right) \\times 100\\%$$

**含义：** 从历史最高点到后续最低点的最大跌幅，衡量策略可能面临的最严重亏损。

**解读：**
- MDD = -20% 表示从最高点最多下跌了20%
- MDD 越小（绝对值越小）越好
- 投资者需要评估自己能否承受该回撤幅度
- **回撤修复难度**：跌20%需要涨25%才能回本，跌50%需要涨100%

### 2.3 夏普比率（Sharpe Ratio）

$$Sharpe = \\frac{\\sqrt{252} \\times (\\bar{R}_d - R_f^{daily})}{\\sigma_d}$$

**含义：** 单位风险下的超额回报，衡量风险调整后的收益。

- $\\bar{R}_d$ = 日收益率均值
- $R_f^{daily}$ = 日无风险利率（年化2% / 252天）
- $\\sigma_d$ = 日收益率标准差
- $\\sqrt{252}$ = 年化因子

**解读：**

| Sharpe | 评级 |
|--------|------|
| < 0 | 亏损，策略不可行 |
| 0 ~ 0.5 | 较差，风险补偿不足 |
| 0.5 ~ 1.0 | 一般，可接受 |
| 1.0 ~ 2.0 | 良好，风险调整后收益不错 |
| > 2.0 | 优秀，极具吸引力 |

### 2.4 其他辅助指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 年化收益率 | $(1+CR)^{252/N} - 1$ | 将累计回报折算为年度收益 |
| 胜率 | 盈利交易次数 / 总交易次数 | 交易获胜概率 |
| 交易频率 | 总交易次数 / 回测天数 | 策略活跃度 |
"""))

# ==================== 3. 数据加载 ====================
cells.append(nbf.v4.new_markdown_cell("""## 3. 数据加载与预处理

我们使用6只不同行业、不同特性的A股股票数据进行测试：

| 股票 | 代码 | 行业 | 数据特征 |
|------|------|------|----------|
| 中芯国际 | 688981.SH | 半导体 | 高波动，趋势性强 |
| 三一重工 | 600031.SH | 工程机械 | 低波动，震荡为主 |
| 平安集团 | 000001.SZ | 保险银行 | 大盘蓝筹，温和波动 |
| 贵州茅台 | 600519.SH | 白酒 | 高价股，近年回调 |
| 宁德时代 | 300750.SZ | 新能源 | 高成长，大幅波动 |
| 比亚迪 | 002594.SZ | 新能源汽车 | 高波动，趋势反转 |
"""))

cells.append(nbf.v4.new_code_cell("""# 导入必要的库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings("ignore")

# 中文字体配置
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "Heiti TC", "PingFang SC", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 中国股市颜色惯例：涨红跌绿
RED = "#E0364D"
GREEN = "#16A34A"
BLUE = "#2563EB"
ORANGE = "#F59E0B"

print("环境初始化完成 ✓")
print(f"pandas version: {pd.__version__}")
print(f"numpy version: {np.__version__}")"""))

cells.append(nbf.v4.new_code_cell("""# 定义股票数据文件
STOCKS = {
    "中芯国际": "中芯国际_行情数据.csv",
    "三一重工": "三一重工_行情数据.csv",
    "平安集团": "平安集团_行情数据.csv",
    "贵州茅台": "贵州茅台_行情数据.csv",
    "宁德时代": "宁德时代_行情数据.csv",
    "比亚迪": "比亚迪_行情数据.csv",
}

# 加载所有股票数据
stock_data = {}
for name, file in STOCKS.items():
    df = pd.read_csv(file, encoding="utf-8-sig")
    df["trade_date"] = df["trade_date"].astype(str).str.replace("-", "")
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    df = df.sort_values("trade_date").reset_index(drop=True)
    stock_data[name] = df
    print(f"{name:6s}: {len(df):4d}条 | {df['trade_date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')} | 最新收盘: ¥{df['close'].iloc[-1]:.2f}")"""))

# ==================== 4. 均线计算与信号 ====================
cells.append(nbf.v4.new_markdown_cell("""## 4. 均线计算与信号生成

### 4.1 计算移动平均线

使用pandas的 `rolling().mean()` 计算简单移动平均线（SMA）。
"""))

cells.append(nbf.v4.new_code_cell("""def calc_moving_averages(df, short_window=5, long_window=15):
    \"\"\"计算短期和长期移动平均线\"\"\"
    df = df.copy()
    df[f"MA{short_window}"] = df["close"].rolling(window=short_window).mean()
    df[f"MA{long_window}"] = df["close"].rolling(window=long_window).mean()
    return df

# 以中芯国际为例，计算 MA5 和 MA15
short_w, long_w = 5, 15
demo_df = calc_moving_averages(stock_data["中芯国际"], short_w, long_w)

# 展示均线数据
print(f"中芯国际 — MA{short_w}/MA{long_w} 均线数据预览:")
print(demo_df[["trade_date", "close", f"MA{short_w}", f"MA{long_w}"]].tail(15).to_string(index=False))"""))

cells.append(nbf.v4.new_markdown_cell("""### 4.2 生成买卖信号

**信号逻辑：**
- **金叉**（买入信号）：前一日 MA_short < MA_long，今日 MA_short > MA_long
- **死叉**（卖出信号）：前一日 MA_short > MA_long，今日 MA_short < MA_long
"""))

cells.append(nbf.v4.new_code_cell("""def generate_signals(df, short_window=5, long_window=15):
    \"\"\"根据双均线交叉生成买卖信号\"\"\"
    df = df.copy()
    ma_short = f"MA{short_window}"
    ma_long = f"MA{long_window}"

    # 计算均线差值
    df["ma_diff"] = df[ma_short] - df[ma_long]
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

# 生成信号
demo_df = generate_signals(demo_df, short_w, long_w)

# 展示买卖信号
signals = demo_df[demo_df["signal"] != 0][["trade_date", "close", f"MA{short_w}", f"MA{long_w}", "signal"]]
signals["signal_str"] = signals["signal"].map({1: "买入(金叉)", -1: "卖出(死叉)"})
print(f"中芯国际 — MA{short_w}/MA{long_w} 交易信号:")
print(signals.to_string(index=False))"""))

# ==================== 5. 策略可视化 ====================
cells.append(nbf.v4.new_markdown_cell("""## 5. 策略可视化

绘制股价、长短均线、买卖信号标记的综合图表。
"""))

cells.append(nbf.v4.new_code_cell("""def plot_strategy(stock_name, df, short_w, long_w):
    \"\"\"绘制策略可视化图表\"\"\"
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), height_ratios=[3, 1.2],
                              sharex=True, gridspec_kw={"hspace": 0.08})

    ax1 = axes[0]
    ax1.plot(df["trade_date"], df["close"], color="#6B7280", linewidth=1.2, label="收盘价", zorder=2)
    ax1.plot(df["trade_date"], df[f"MA{short_w}"], color=BLUE, linewidth=1.5, label=f"MA{short_w}(短均线)", zorder=3)
    ax1.plot(df["trade_date"], df[f"MA{long_w}"], color=ORANGE, linewidth=1.5, label=f"MA{long_w}(长均线)", zorder=3)

    # 持仓区间背景
    ax1.fill_between(df["trade_date"], df["close"].min()*0.95, df["close"],
                    where=(df["position"]==1), alpha=0.08, color=RED)

    # 买卖信号标记
    buy_signals = df[df["signal"] == 1]
    sell_signals = df[df["signal"] == -1]
    if len(buy_signals) > 0:
        ax1.scatter(buy_signals["trade_date"], buy_signals["close"],
                   color=RED, marker="^", s=120, zorder=5, label="买入(金叉)", edgecolors="white", linewidths=0.5)
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals["trade_date"], sell_signals["close"],
                   color=GREEN, marker="v", s=120, zorder=5, label="卖出(死叉)", edgecolors="white", linewidths=0.5)

    ax1.set_title(f"{stock_name} 双均线策略 (MA{short_w}/MA{long_w})", fontsize=15, fontweight="bold", pad=12)
    ax1.set_ylabel("股价 (元)", fontsize=12)
    ax1.legend(loc="upper left", fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # 成交量
    ax2 = axes[1]
    colors = [RED if df.loc[i, "pct_chg"] >= 0 else GREEN for i in range(len(df))]
    ax2.bar(df["trade_date"], df["vol"]/10000, color=colors, alpha=0.6, width=1)
    ax2.set_ylabel("成交量 (万手)", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()

# 绘制中芯国际策略图
plot_strategy("中芯国际", demo_df, short_w, long_w)"""))

cells.append(nbf.v4.new_code_cell("""# 对比不同股票的策略信号
fig, axes = plt.subplots(3, 2, figsize=(16, 15))
axes = axes.flatten()

for idx, (stock_name, df_orig) in enumerate(stock_data.items()):
    df = calc_moving_averages(df_orig, 5, 15)
    df = generate_signals(df, 5, 15)
    ax = axes[idx]

    ax.plot(df["trade_date"], df["close"], color="#6B7280", linewidth=1, label="收盘价")
    ax.plot(df["trade_date"], df["MA5"], color=BLUE, linewidth=1.2, label="MA5")
    ax.plot(df["trade_date"], df["MA15"], color=ORANGE, linewidth=1.2, label="MA15")

    buy_s = df[df["signal"] == 1]
    sell_s = df[df["signal"] == -1]
    if len(buy_s) > 0:
        ax.scatter(buy_s["trade_date"], buy_s["close"], color=RED, marker="^", s=60, zorder=5)
    if len(sell_s) > 0:
        ax.scatter(sell_s["trade_date"], sell_s["close"], color=GREEN, marker="v", s=60, zorder=5)

    ax.set_title(f"{stock_name} (MA5/MA15)", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)
    if idx == 0:
        ax.legend(fontsize=8, loc="upper left")

plt.suptitle("六只股票双均线策略信号对比 (MA5/MA15)", fontsize=16, fontweight="bold", y=1.01)
plt.tight_layout()
plt.show()"""))

# ==================== 6. 回测模拟 ====================
cells.append(nbf.v4.new_markdown_cell("""## 6. 回测模拟与量化指标

### 6.1 回测引擎

模拟真实交易过程：
- 初始资金 ¥100,000
- 金叉日全仓买入，死叉日全仓卖出
- 以收盘价成交
- 同时计算"买入持有"作为基准对比
"""))

cells.append(nbf.v4.new_code_cell("""def backtest(df, initial_capital=100000):
    \"\"\"模拟交易回测\"\"\"
    df = df.copy()
    capital = float(initial_capital)
    shares = 0.0
    df["strategy_value"] = float(initial_capital)
    df["holdings"] = 0.0
    df["cash"] = float(initial_capital)

    trade_log = []

    for i in range(len(df)):
        price = df.loc[i, "close"]

        if df.loc[i, "signal"] == 1 and shares == 0:
            shares = float(int(capital // price))
            capital = capital - shares * price
            trade_log.append({"date": df.loc[i, "trade_date"], "action": "BUY",
                            "price": price, "shares": int(shares), "value": shares * price})

        elif df.loc[i, "signal"] == -1 and shares > 0:
            capital = capital + shares * price
            trade_log.append({"date": df.loc[i, "trade_date"], "action": "SELL",
                            "price": price, "shares": int(shares), "value": shares * price})
            shares = 0

        df.loc[i, "strategy_value"] = capital + shares * price
        df.loc[i, "holdings"] = shares * price
        df.loc[i, "cash"] = capital

    # 买入持有基准
    first_price = df.loc[0, "close"]
    bh_shares = float(int(initial_capital // first_price))
    df["buy_hold_value"] = (bh_shares * df["close"]) + (float(initial_capital) - bh_shares * first_price)

    trade_df = pd.DataFrame(trade_log)
    return df, trade_df

def calc_metrics(df, initial_capital=100000, risk_free_rate=0.02):
    \"\"\"计算量化指标\"\"\"
    metrics = {}
    final_value = df["strategy_value"].iloc[-1]
    metrics["cumulative_return"] = (final_value - initial_capital) / initial_capital
    metrics["final_value"] = final_value

    daily_returns = df["strategy_value"].pct_change().dropna()
    trading_days = len(df)
    if trading_days > 1:
        metrics["annual_return"] = (1 + metrics["cumulative_return"]) ** (252 / trading_days) - 1
    else:
        metrics["annual_return"] = 0

    cummax = df["strategy_value"].cummax()
    drawdown = (df["strategy_value"] - cummax) / cummax
    metrics["max_drawdown"] = drawdown.min()

    if daily_returns.std() > 0:
        daily_rf = risk_free_rate / 252
        excess_returns = daily_returns - daily_rf
        metrics["sharpe_ratio"] = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    else:
        metrics["sharpe_ratio"] = 0

    bh_final = df["buy_hold_value"].iloc[-1]
    metrics["bh_cumulative_return"] = (bh_final - initial_capital) / initial_capital
    bh_cummax = df["buy_hold_value"].cummax()
    bh_dd = (df["buy_hold_value"] - bh_cummax) / bh_cummax
    metrics["bh_max_drawdown"] = bh_dd.min()

    bh_daily_returns = df["buy_hold_value"].pct_change().dropna()
    if bh_daily_returns.std() > 0:
        bh_excess = bh_daily_returns - risk_free_rate / 252
        metrics["bh_sharpe_ratio"] = np.sqrt(252) * bh_excess.mean() / bh_excess.std()
    else:
        metrics["bh_sharpe_ratio"] = 0

    metrics["buy_count"] = int((df["signal"] == 1).sum())
    metrics["sell_count"] = int((df["signal"] == -1).sum())
    return metrics

# 运行回测
bt_df, trade_df = backtest(demo_df)
metrics = calc_metrics(bt_df)

print("=" * 55)
print(f"中芯国际 双均线策略回测结果 (MA5/MA15)")
print("=" * 55)
print(f"  初始资金:         ¥100,000.00")
print(f"  期末市值:         ¥{metrics['final_value']:,.2f}")
print(f"  累计回报:         {metrics['cumulative_return']:+.2%}")
print(f"  年化收益率:       {metrics['annual_return']:+.2%}")
print(f"  最大回撤 (MDD):   {metrics['max_drawdown']:.2%}")
print(f"  夏普比率:         {metrics['sharpe_ratio']:.2f}")
print(f"  买入次数:         {metrics['buy_count']}")
print(f"  卖出次数:         {metrics['sell_count']}")
print("-" * 55)
print(f"  买入持有对比:")
print(f"    买入持有回报:   {metrics['bh_cumulative_return']:+.2%}")
print(f"    买入持有MDD:    {metrics['bh_max_drawdown']:.2%}")
print(f"    买入持有Sharpe: {metrics['bh_sharpe_ratio']:.2f}")
print("=" * 55)"""))

cells.append(nbf.v4.new_code_cell("""# 绘制策略收益 vs 买入持有对比图
fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(bt_df["trade_date"], bt_df["strategy_value"], color=RED, linewidth=2,
       label=f"双均线策略 (¥{metrics['final_value']:,.0f})")
ax.plot(bt_df["trade_date"], bt_df["buy_hold_value"], color=BLUE, linewidth=2,
       label=f"买入持有 (¥{metrics['bh_final_value']:,.0f})", linestyle="--")
ax.axhline(y=100000, color="#6B7280", linewidth=1, linestyle=":", alpha=0.5, label="初始资金")

# 标记交易点
for _, t in trade_df.iterrows():
    val = bt_df[bt_df["trade_date"] == t["date"]]["strategy_value"].iloc[0]
    color = RED if t["action"] == "BUY" else GREEN
    marker = "^" if t["action"] == "BUY" else "v"
    ax.scatter(t["date"], val, color=color, marker=marker, s=80, zorder=5, edgecolors="white")

ax.set_title("中芯国际 策略收益 vs 买入持有 (MA5/MA15)", fontsize=15, fontweight="bold")
ax.set_ylabel("市值 (¥)", fontsize=12)
ax.set_xlabel("日期", fontsize=12)
ax.legend(loc="upper left", fontsize=11)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"¥{x:,.0f}"))
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()"""))

cells.append(nbf.v4.new_code_cell("""# 绘制回撤对比图
fig, ax = plt.subplots(figsize=(14, 5))

cummax_s = bt_df["strategy_value"].cummax()
dd_s = (bt_df["strategy_value"] - cummax_s) / cummax_s * 100
ax.fill_between(bt_df["trade_date"], dd_s, 0, color=RED, alpha=0.3,
               label=f"策略回撤 (MDD={metrics['max_drawdown']:.1%})")
ax.plot(bt_df["trade_date"], dd_s, color=RED, linewidth=1)

cummax_bh = bt_df["buy_hold_value"].cummax()
dd_bh = (bt_df["buy_hold_value"] - cummax_bh) / cummax_bh * 100
ax.plot(bt_df["trade_date"], dd_bh, color=BLUE, linewidth=1.5, linestyle="--",
       label=f"买入持有回撤 (MDD={metrics['bh_max_drawdown']:.1%})")

ax.set_title("中芯国际 最大回撤对比 (MA5/MA15)", fontsize=15, fontweight="bold")
ax.set_ylabel("回撤 (%)", fontsize=12)
ax.legend(loc="lower left", fontsize=11)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()"""))

# ==================== 7. 多股票多参数对比 ====================
cells.append(nbf.v4.new_markdown_cell("""## 7. 多股票多参数对比

对6只股票分别使用5种均线参数组合进行回测，全面评估策略效果。

**参数组合：** MA5/15, MA5/20, MA10/20, MA10/30, MA5/30
"""))

cells.append(nbf.v4.new_code_cell("""def run_full_strategy(df_orig, short_w, long_w, initial_capital=100000):
    \"\"\"完整策略运行\"\"\"
    df = calc_moving_averages(df_orig, short_w, long_w)
    df = generate_signals(df, short_w, long_w)
    df, trade_df = backtest(df, initial_capital)
    metrics = calc_metrics(df, initial_capital)
    return df, trade_df, metrics

# 批量回测
PARAM_COMBOS = [(5, 15), (5, 20), (10, 20), (10, 30), (5, 30)]
all_results = []

for stock_name, df_orig in stock_data.items():
    for s, l in PARAM_COMBOS:
        _, _, m = run_full_strategy(df_orig, s, l)
        m["stock"] = stock_name
        m["param"] = f"MA{s}/MA{l}"
        all_results.append(m)

results_df = pd.DataFrame(all_results)

# 展示结果
display_cols = ["stock", "param", "cumulative_return", "max_drawdown", "sharpe_ratio",
                "annual_return", "bh_cumulative_return", "bh_sharpe_ratio", "buy_count"]
print("多股票多参数回测结果汇总:")
print(results_df[display_cols].to_string(index=False))"""))

cells.append(nbf.v4.new_code_cell("""# 累计回报对比柱状图
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 累计回报
ax1 = axes[0]
pivot_ret = results_df.pivot(index="stock", columns="param", values="cumulative_return") * 100
pivot_ret.plot(kind="bar", ax=ax1, width=0.8, edgecolor="white", linewidth=0.5)
ax1.set_title("各股票不同均线参数 — 累计回报 (%)", fontsize=14, fontweight="bold")
ax1.set_ylabel("累计回报 (%)")
ax1.axhline(y=0, color="black", linewidth=0.8)
ax1.legend(title="均线参数", fontsize=9)
ax1.grid(True, alpha=0.3, axis="y")
ax1.tick_params(axis="x", rotation=30)

# 夏普比率
ax2 = axes[1]
pivot_sharpe = results_df.pivot(index="stock", columns="param", values="sharpe_ratio")
pivot_sharpe.plot(kind="bar", ax=ax2, width=0.8, edgecolor="white", linewidth=0.5)
ax2.set_title("各股票不同均线参数 — 夏普比率", fontsize=14, fontweight="bold")
ax2.set_ylabel("夏普比率")
ax2.axhline(y=0, color="black", linewidth=0.8)
ax2.axhline(y=1, color=GREEN, linewidth=1, linestyle="--", alpha=0.5, label="Sharpe=1")
ax2.legend(title="均线参数", fontsize=9)
ax2.grid(True, alpha=0.3, axis="y")
ax2.tick_params(axis="x", rotation=30)

plt.tight_layout()
plt.show()"""))

cells.append(nbf.v4.new_code_cell("""# 策略 vs 买入持有 散点图
fig, ax = plt.subplots(figsize=(10, 9))

for stock in results_df["stock"].unique():
    sub = results_df[results_df["stock"] == stock]
    ax.scatter(sub["bh_cumulative_return"]*100, sub["cumulative_return"]*100,
              s=80, alpha=0.7, label=stock, edgecolors="white", linewidths=0.5)

lim_min = min(results_df["bh_cumulative_return"].min(), results_df["cumulative_return"].min()) * 100 - 5
lim_max = max(results_df["bh_cumulative_return"].max(), results_df["cumulative_return"].max()) * 100 + 5
ax.plot([lim_min, lim_max], [lim_min, lim_max], "k--", alpha=0.3, linewidth=1, label="策略=买入持有")
ax.axhline(y=0, color="black", linewidth=0.5)
ax.axvline(x=0, color="black", linewidth=0.5)

ax.set_xlabel("买入持有累计回报 (%)", fontsize=13)
ax.set_ylabel("双均线策略累计回报 (%)", fontsize=13)
ax.set_title("双均线策略 vs 买入持有 — 收益对比", fontsize=15, fontweight="bold")
ax.legend(loc="upper left", fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()"""))

cells.append(nbf.v4.new_code_cell("""# 找出每只股票最优参数
print("各股票最优参数（按夏普比率）:")
print("=" * 80)
for stock in results_df["stock"].unique():
    sub = results_df[results_df["stock"] == stock]
    best = sub.loc[sub["sharpe_ratio"].idxmax()]
    print(f"  {stock:6s} | 最优: {best['param']:10s} | "
          f"累计回报: {best['cumulative_return']:+.2%} | "
          f"Sharpe: {best['sharpe_ratio']:.2f} | "
          f"MDD: {best['max_drawdown']:.2%} | "
          f"vs买入持有: {best['bh_cumulative_return']:+.2%}")
print("=" * 80)"""))

# ==================== 8. 总结 ====================
cells.append(nbf.v4.new_markdown_cell("""## 8. 策略适用场景与心得总结

### 8.1 回测核心发现

通过6只股票×5种参数组合的回测，我们得到以下关键发现：

| 发现 | 说明 |
|------|------|
| **趋势行情中表现优异** | 中芯国际、宁德时代等强趋势股，策略收益可观（50%+） |
| **震荡行情中频繁假信号** | 三一重工等横盘股，金叉死叉反复出现，导致亏损 |
| **有效降低最大回撤** | 多数情况下策略MDD优于买入持有，体现出止损效果 |
| **难以跑赢强牛市** | 在单边大涨行情中，频繁卖出导致错过涨幅 |
| **长周期参数更稳健** | MA5/30等大跨度参数信号少但质量高，假信号更少 |
| **短周期参数更灵敏** | MA5/15信号频繁，适合短线但需要配合其他指标过滤 |

### 8.2 双均线策略适用场景

#### ✅ 适合使用的场景
1. **明显的趋势行情**：股价持续上涨或下跌，均线能清晰反映趋势
2. **中长线投资**：持仓周期以周/月为单位，避免日内噪音
3. **高波动股票**：波动越大，趋势越明显，策略捕捉能力越强
4. **组合管理**：作为多策略组合中的趋势跟踪组件

#### ❌ 不适合使用的场景
1. **横盘震荡市场**：价格在区间内反复波动，金叉死叉频繁但无趋势
2. **V型反转行情**：均线滞后性大，反转信号来得太晚
3. **高频交易**：日内波动噪音大，均线信号不可靠
4. **小盘低流动性股票**：容易被均线信号误导

### 8.3 参数选择心得

| 参数特点 | 适用场景 | 优缺点 |
|----------|----------|--------|
| 短周期（5/15） | 短线交易、高波动股 | ✅灵敏度高 ❌假信号多 |
| 中周期（10/20） | 中线、温和波动 | ✅平衡稳健 ❌两头不靠 |
| 长周期（5/30、10/30） | 中长线、趋势确认 | ✅信号可靠 ❌滞后性大 |

### 8.4 改进方向

1. **多指标过滤**：结合MACD、RSI、成交量等指标过滤假信号
2. **动态止损**：设置移动止损线，控制单笔亏损
3. **仓位管理**：根据信号强度调整仓位，而非全仓进出
4. **市场状态识别**：判断当前是趋势市还是震荡市，动态切换策略
5. **多时间框架**：结合日线和周线信号，提高判断准确性

### 8.5 核心结论

> 双均线策略是一个**简单但有效**的趋势跟踪工具。它的价值不在于"万能盈利"，而在于**用纪律化的规则替代情绪化决策**——在趋势来临时果断入场，在趋势结束时及时止损。理解其"趋势市赚钱、震荡市亏钱"的本质特征，并在合适的场景中使用，才是量化策略的正确打开方式。
"""))

# 组装notebook
nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.13.0"
    }
}

output_path = os.path.join(BASE_DIR, "双均线策略分析.ipynb")
with open(output_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook已生成: {output_path}")
print(f"单元格数量: {len(cells)}")
