"""
生成海龟交易策略 Jupyter Notebook
"""
import json
import nbformat as nbf
import os
import pandas as pd

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

nb = nbf.v4.new_notebook()
cells = []

# ========== 标题 ==========
cells.append(nbf.v4.new_markdown_cell("""# Task4 复刻传奇：海龟交易法则实战演练

**BI工作坊 · AI量化公益课**

本 Notebook 实现海龟交易策略的完整流程：
1. 海龟策略核心思想与关键概念
2. Python 实现：通道计算、ATR、信号生成、回测
3. 可视化：股价通道、交易信号、净值对比、回撤曲线
4. 参数调节与场景分析

---

## 一、海龟策略概述

### 1.1 历史背景

1983年，美国著名交易员**理查德·丹尼斯（Richard Dennis）**与威廉·埃克哈特打了一个赌：伟大的交易员究竟是天生还是后天培养的？丹尼斯坚信交易可以被系统化教授，于是招募了一批学员，称之为**"海龟"**。他用一套完全机械化的交易系统培训这些学员，在随后的4年中，海龟们累计盈利超过1亿美元，创造了华尔街交易史上的传奇。

### 1.2 核心思想

- **趋势跟踪**：不预测市场方向，等待价格突破历史高低点后顺势入场
- **突破入场**：使用唐奇安通道，价格突破20日新高时买入
- **波动率自适应**：通过ATR动态衡量市场波动率，止损和仓位随波动率自动调整
- **严格风控**：每笔交易风险不超过总资金的2%，止损设在入场价-2×ATR处

### 1.3 关键优势

1. **系统化交易，克服人性弱点** — 完全规则化，不依赖主观判断
2. **趋势捕获能力强** — 突破入场确保在大趋势启动时第一时间进场
3. **动态风险控制** — ATR随波动率自动调节，不同市场环境下保持合理风险敞口
4. **明确的资金管理规则** — 2%风险限制+金字塔加仓，亏损可控
5. **可量化、可回测** — 所有规则均可用数学公式表达
6. **跨市场适用性** — 商品期货、股票、外汇等市场均可应用
"""))

# ========== 核心概念 ==========
cells.append(nbf.v4.new_markdown_cell("""## 二、核心概念详解

### 2.1 高低点通道（唐奇安通道 Donchian Channel）

唐奇安通道计算过去N个交易日的最高价和最低价，形成动态价格通道：

- **入场通道（20日）**：
  - 上轨 = max(最高价, 过去20日) → 突破买入
  - 下轨 = min(最低价, 过去20日) → 突破卖出
- **离场通道（10日）**：
  - 下轨 = min(最低价, 过去10日) → 跌破平仓
  - 上轨 = max(最高价, 过去10日) → 突破空头平仓

**为什么入场用20日、离场用10日？** 慢进快出：入场通道较长确保趋势确实形成，离场通道较短一旦反转就果断退出。

### 2.2 平均真实波幅（ATR）

真实波幅（TR）衡量当日价格波动的最大幅度：

```
TR = max(
    当日最高价 - 当日最低价,           # 当日振幅
    |当日最高价 - 前日收盘价|,          # 跳空高开
    |当日最低价 - 前日收盘价|           # 跳空低开
)

ATR = TR 的 N 日移动平均（默认N=20）
```

**ATR 的三大作用：**
1. **动态止损**：止损价 = 买入价 - 2×ATR
2. **仓位管理**：头寸 = (总资金×2%) / (ATR×合约乘数)
3. **金字塔加仓**：每上涨 0.5×ATR 加仓一个单位

### 2.3 止损条件

- **止损价**：买入价 - 2×ATR（波动大则止损宽，波动小则止损紧）
- **仓位大小**：(总资金×2%) / (ATR×合约乘数)，确保单笔亏损不超过2%
- **通道离场**：价格跌破10日最低价时正常平仓（利润兑现）
- **核心哲学**："截断亏损，让利润奔跑" — 2%风险限制确保即使连续亏损20次仍可翻身
"""))

# ========== 导入库 ==========
cells.append(nbf.v4.new_code_cell("""# 导入所需库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# 中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False

print("环境准备完成 ✓")
print(f"pandas version: {pd.__version__}")
print(f"numpy version: {np.__version__}")"""))

# ========== 1. 加载数据 ==========
cells.append(nbf.v4.new_markdown_cell("## 三、Python 编程实现\n\n### 3.1 加载已存储的股价数据"))
cells.append(nbf.v4.new_code_cell("""# ========== 1. 加载股价数据 ==========

def load_stock_data(csv_path):
    \"\"\"加载CSV格式的股价数据\"\"\"
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    # 统一日期格式
    df['trade_date'] = df['trade_date'].astype(str).str.replace('-', '')
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df

# 加载贵州茅台数据作为示例
data_dir = os.path.dirname(os.path.abspath('.')) if '__file__' not in dir() else os.path.dirname(os.path.abspath(__file__))
csv_path = '贵州茅台_行情数据.csv'
df = load_stock_data(csv_path)

print(f"数据加载完成: {csv_path}")
print(f"数据区间: {df['trade_date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')}")
print(f"交易日数: {len(df)}")
print(f"\\n数据预览:")
df.head(10)"""))

# ========== 2. 计算通道 ==========
cells.append(nbf.v4.new_markdown_cell("### 3.2 计算高低价格通道（唐奇安通道）"))
cells.append(nbf.v4.new_code_cell("""# ========== 2. 计算唐奇安高低点通道 ==========

def calc_donchian_channel(df, entry_period=20, exit_period=10):
    \"\"\"
    计算唐奇安高低点通道
    - 入场通道(entry_period=20): 过去20日最高价/最低价，用于突破入场
    - 离场通道(exit_period=10): 过去10日最高价/最低价，用于通道离场
    - shift(1) 避免使用当日数据(防止未来数据)
    \"\"\"
    df = df.copy()
    # 入场通道（20日）
    df['upper_entry'] = df['high'].rolling(window=entry_period).max().shift(1)
    df['lower_entry'] = df['low'].rolling(window=entry_period).min().shift(1)
    # 离场通道（10日）
    df['upper_exit'] = df['high'].rolling(window=exit_period).max().shift(1)
    df['lower_exit'] = df['low'].rolling(window=exit_period).min().shift(1)
    # 通道中线
    df['channel_mid'] = (df['upper_entry'] + df['lower_entry']) / 2
    return df

# 计算20日通道
df = calc_donchian_channel(df, entry_period=20, exit_period=10)
print("唐奇安通道计算完成 ✓")
print(f"\\n通道数据预览(最后5行):")
df[['trade_date', 'close', 'upper_entry', 'lower_entry', 'lower_exit', 'channel_mid']].tail()"""))

# ========== 3. 计算ATR ==========
cells.append(nbf.v4.new_markdown_cell("### 3.3 计算 ATR（平均真实波幅）"))
cells.append(nbf.v4.new_code_cell("""# ========== 3. 计算 ATR ==========

def calc_atr(df, period=20):
    \"\"\"
    计算平均真实波幅（ATR）
    TR = max(当日振幅, |跳空高开|, |跳空低开|)
    ATR = TR的N日移动平均
    \"\"\"
    df = df.copy()
    prev_close = df['close'].shift(1)
    # 三种波动幅度
    tr1 = df['high'] - df['low']                     # 当日振幅
    tr2 = (df['high'] - prev_close).abs()             # 跳空高开幅度
    tr3 = (df['low'] - prev_close).abs()              # 跳空低开幅度
    # TR取三者最大值
    df['TR'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # ATR = TR的N日移动平均
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df

# 计算ATR
df = calc_atr(df, period=20)
print("ATR计算完成 ✓")
print(f"\\nATR数据预览(最后5行):")
df[['trade_date', 'high', 'low', 'close', 'TR', 'ATR']].tail()"""))

# ========== 4. 生成信号 ==========
cells.append(nbf.v4.new_markdown_cell("### 3.4 计算买入卖出交易信号"))
cells.append(nbf.v4.new_code_cell("""# ========== 4. 生成交易信号 ==========

def generate_signals(df, entry_period=20, exit_period=10, atr_period=20, stop_atr_mult=2.0):
    \"\"\"
    生成海龟策略交易信号
    - 买入: 收盘价 > 20日最高价(突破入场)
    - 卖出(满足任一): 收盘价 < 10日最低价(通道离场) 或 收盘价 < 止损价(2×ATR止损)
    \"\"\"
    df = df.copy()
    df['signal'] = 0       # 1=买入, -1=卖出, 0=无操作
    df['position'] = 0     # 1=持仓, 0=空仓
    df['stop_loss'] = np.nan   # 止损价
    df['entry_price'] = np.nan # 买入价

    current_pos = 0
    entry_price = 0.0
    stop_price = 0.0

    for i in range(len(df)):
        if pd.isna(df.loc[i, 'upper_entry']) or pd.isna(df.loc[i, 'ATR']):
            df.loc[i, 'position'] = current_pos
            continue

        close = df.loc[i, 'close']
        atr = df.loc[i, 'ATR']

        if current_pos == 0:  # 空仓状态
            if close > df.loc[i, 'upper_entry']:  # 突破20日新高 → 买入
                df.loc[i, 'signal'] = 1
                current_pos = 1
                entry_price = close
                stop_price = close - stop_atr_mult * atr  # 止损价 = 买入价 - 2×ATR
                df.loc[i, 'entry_price'] = entry_price
                df.loc[i, 'stop_loss'] = stop_price

        elif current_pos == 1:  # 持仓状态
            # 条件1: 跌破10日最低价 → 通道离场
            if close < df.loc[i, 'lower_exit']:
                df.loc[i, 'signal'] = -1
                current_pos = 0
            # 条件2: 触及止损价 → 止损离场
            elif close < stop_price:
                df.loc[i, 'signal'] = -1
                current_pos = 0

        df.loc[i, 'position'] = current_pos
        if current_pos == 1 and pd.isna(df.loc[i, 'stop_loss']):
            df.loc[i, 'stop_loss'] = stop_price
            df.loc[i, 'entry_price'] = entry_price

    return df

# 生成信号
df = generate_signals(df, entry_period=20, exit_period=10, atr_period=20, stop_atr_mult=2.0)

buy_count = (df['signal'] == 1).sum()
sell_count = (df['signal'] == -1).sum()
print(f"信号生成完成 ✓")
print(f"买入信号: {buy_count}次")
print(f"卖出信号: {sell_count}次")
print(f"\\n信号明细:")
df[df['signal'] != 0][['trade_date', 'close', 'signal', 'ATR', 'stop_loss']].head(20)"""))

# ========== 5. 可视化 ==========
cells.append(nbf.v4.new_markdown_cell("### 3.5 可视化：股价、通道、交易信号"))
cells.append(nbf.v4.new_code_cell("""# ========== 5. 可视化 ==========

fig, axes = plt.subplots(3, 1, figsize=(14, 14), gridspec_kw={'height_ratios': [3, 1, 2]})

# --- 图1: 股价与唐奇安通道 + 交易信号 ---
ax1 = axes[0]
ax1.plot(df['trade_date'], df['close'], color='#2C3E50', linewidth=1.2, label='收盘价')
ax1.plot(df['trade_date'], df['upper_entry'], color='#3498DB', linewidth=1, linestyle='--', label='20日上轨(入场)', alpha=0.8)
ax1.plot(df['trade_date'], df['lower_entry'], color='#3498DB', linewidth=1, linestyle='--', label='20日下轨(入场)', alpha=0.8)
ax1.plot(df['trade_date'], df['lower_exit'], color='#27AE60', linewidth=1, linestyle=':', label='10日下轨(离场)', alpha=0.8)
ax1.fill_between(df['trade_date'], df['upper_entry'], df['lower_entry'], color='#3498DB', alpha=0.06)

# 标记买卖信号
buy_signals = df[df['signal'] == 1]
sell_signals = df[df['signal'] == -1]
if len(buy_signals) > 0:
    ax1.scatter(buy_signals['trade_date'], buy_signals['close'], color='#E74C3C', marker='^', s=120, zorder=5, label=f'买入({len(buy_signals)}次)')
if len(sell_signals) > 0:
    ax1.scatter(sell_signals['trade_date'], sell_signals['close'], color='#27AE60', marker='v', s=120, zorder=5, label=f'卖出({len(sell_signals)}次)')

# 止损线
stop_data = df[df['stop_loss'].notna()]
if len(stop_data) > 0:
    ax1.plot(stop_data['trade_date'], stop_data['stop_loss'], color='#E67E22', linewidth=0.8, linestyle='-.', alpha=0.5, label='止损线(2×ATR)')

ax1.set_title('贵州茅台 - 股价、唐奇安通道与交易信号', fontsize=14, fontweight='bold')
ax1.set_ylabel('价格(元)')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

# --- 图2: ATR ---
ax2 = axes[1]
ax2.plot(df['trade_date'], df['ATR'], color='#F39C12', linewidth=1.5, label='ATR(20)')
ax2.fill_between(df['trade_date'], 0, df['ATR'], color='#F39C12', alpha=0.15)
ax2.set_title('ATR 波动率', fontsize=12, fontweight='bold')
ax2.set_ylabel('ATR')
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

# --- 图3: 持仓状态 ---
ax3 = axes[2]
ax3.fill_between(df['trade_date'], df['position'], color='#8E44AD', alpha=0.3)
ax3.plot(df['trade_date'], df['position'], color='#8E44AD', linewidth=1)
ax3.set_title('持仓状态 (1=持仓, 0=空仓)', fontsize=12, fontweight='bold')
ax3.set_ylabel('持仓')
ax3.set_xlabel('日期')
ax3.set_yticks([0, 1])
ax3.grid(True, alpha=0.3)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

plt.tight_layout()
plt.savefig('贵州茅台_策略可视化.png', dpi=150, bbox_inches='tight')
plt.show()
print('可视化图表生成完成 ✓')"""))

# ========== 6. 回测 ==========
cells.append(nbf.v4.new_markdown_cell("### 3.6 模拟交易回测与量化指标计算"))
cells.append(nbf.v4.new_code_cell("""# ========== 6. 回测模拟 ==========

def backtest(df, initial_capital=100000):
    \"\"\"海龟策略回测：买入信号全仓建仓，卖出信号清仓\"\"\"
    df = df.copy()
    capital = float(initial_capital)
    shares = 0.0
    df['strategy_value'] = float(initial_capital)
    df['holdings'] = 0.0
    df['cash'] = float(initial_capital)
    df['trade_price'] = np.nan
    trade_log = []

    for i in range(len(df)):
        price = df.loc[i, 'close']

        if df.loc[i, 'signal'] == 1 and shares == 0:
            shares = float(int(capital // price))
            capital = capital - shares * price
            trade_log.append({
                'date': df.loc[i, 'trade_date'], 'action': 'BUY',
                'price': price, 'shares': int(shares), 'value': shares * price
            })
            df.loc[i, 'trade_price'] = price

        elif df.loc[i, 'signal'] == -1 and shares > 0:
            capital = capital + shares * price
            trade_log.append({
                'date': df.loc[i, 'trade_date'], 'action': 'SELL',
                'price': price, 'shares': int(shares), 'value': shares * price
            })
            shares = 0
            df.loc[i, 'trade_price'] = price

        total_value = capital + shares * price
        df.loc[i, 'strategy_value'] = total_value
        df.loc[i, 'holdings'] = shares * price
        df.loc[i, 'cash'] = capital

    # 买入持有基准
    first_price = df.loc[0, 'close']
    bh_shares = float(int(initial_capital // first_price))
    df['buy_hold_value'] = (bh_shares * df['close']) + (float(initial_capital) - bh_shares * first_price)

    trade_df = pd.DataFrame(trade_log)
    return df, trade_df

# 执行回测
df, trade_df = backtest(df, initial_capital=100000)
print(f"回测完成 ✓ 交易记录: {len(trade_df)}笔")
print(f"\\n交易明细:")
trade_df"""))

# ========== 量化指标 ==========
cells.append(nbf.v4.new_code_cell("""# ========== 量化指标计算 ==========

def calc_metrics(df, initial_capital=100000, risk_free_rate=0.02):
    \"\"\"计算策略量化指标\"\"\"
    metrics = {}

    # 累计回报
    final_value = df['strategy_value'].iloc[-1]
    metrics['cumulative_return'] = (final_value - initial_capital) / initial_capital
    metrics['final_value'] = final_value

    # 日收益率
    daily_returns = df['strategy_value'].pct_change().dropna()

    # 年化收益率
    trading_days = len(df)
    if trading_days > 1:
        metrics['annual_return'] = (1 + metrics['cumulative_return']) ** (252 / trading_days) - 1
    else:
        metrics['annual_return'] = 0

    # 最大回撤 MDD
    cummax = df['strategy_value'].cummax()
    drawdown = (df['strategy_value'] - cummax) / cummax
    metrics['max_drawdown'] = drawdown.min()

    # 夏普比率 Sharpe Ratio
    if daily_returns.std() > 0:
        daily_rf = risk_free_rate / 252
        excess_returns = daily_returns - daily_rf
        metrics['sharpe_ratio'] = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    else:
        metrics['sharpe_ratio'] = 0

    # 买入持有基准
    bh_final = df['buy_hold_value'].iloc[-1]
    metrics['bh_cumulative_return'] = (bh_final - initial_capital) / initial_capital
    metrics['bh_final_value'] = bh_final

    bh_cummax = df['buy_hold_value'].cummax()
    bh_drawdown = (df['buy_hold_value'] - bh_cummax) / bh_cummax
    metrics['bh_max_drawdown'] = bh_drawdown.min()

    bh_daily_returns = df['buy_hold_value'].pct_change().dropna()
    if bh_daily_returns.std() > 0:
        bh_daily_rf = risk_free_rate / 252
        bh_excess = bh_daily_returns - bh_daily_rf
        metrics['bh_sharpe_ratio'] = np.sqrt(252) * bh_excess.mean() / bh_excess.std()
    else:
        metrics['bh_sharpe_ratio'] = 0

    # 交易统计
    metrics['buy_count'] = int((df['signal'] == 1).sum())
    metrics['sell_count'] = int((df['signal'] == -1).sum())

    # 胜率
    buy_prices = df.loc[df['signal'] == 1, 'close'].values
    sell_prices = df.loc[df['signal'] == -1, 'close'].values
    if len(buy_prices) > 0 and len(sell_prices) > 0:
        min_len = min(len(buy_prices), len(sell_prices))
        wins = (sell_prices[:min_len] > buy_prices[:min_len]).sum()
        metrics['win_rate'] = wins / min_len if min_len > 0 else 0
    else:
        metrics['win_rate'] = 0

    return metrics

# 计算指标
metrics = calc_metrics(df, initial_capital=100000)

print("=" * 50)
print("海龟策略回测结果 - 贵州茅台")
print("=" * 50)
print(f"\\n【策略表现】")
print(f"  初始资金:     100,000.00元")
print(f"  最终市值:     {metrics['final_value']:>14.2f}元")
print(f"  累计回报:     {metrics['cumulative_return']:>14.2%}")
print(f"  年化收益率:   {metrics['annual_return']:>14.2%}")
print(f"  最大回撤MDD:  {metrics['max_drawdown']:>14.2%}")
print(f"  夏普比率:     {metrics['sharpe_ratio']:>14.2f}")
print(f"  交易次数:     买{metrics['buy_count']}次/卖{metrics['sell_count']}次")
print(f"  胜率:         {metrics['win_rate']:>14.2%}")

print(f"\\n【买入持有基准】")
print(f"  最终市值:     {metrics['bh_final_value']:>14.2f}元")
print(f"  累计回报:     {metrics['bh_cumulative_return']:>14.2%}")
print(f"  最大回撤MDD:  {metrics['bh_max_drawdown']:>14.2%}")
print(f"  夏普比率:     {metrics['bh_sharpe_ratio']:>14.2f}")"""))

# ========== 净值对比图 ==========
cells.append(nbf.v4.new_code_cell("""# 净值对比与回撤可视化
fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [2, 1]})

# 净值对比
ax1 = axes[0]
ax1.plot(df['trade_date'], df['strategy_value'], color='#8E44AD', linewidth=1.5, label='海龟策略净值')
ax1.plot(df['trade_date'], df['buy_hold_value'], color='#95A5A6', linewidth=1.5, linestyle='--', label='买入持有基准')
ax1.fill_between(df['trade_date'], df['buy_hold_value'], df['strategy_value'],
                 where=df['strategy_value'] >= df['buy_hold_value'],
                 color='#8E44AD', alpha=0.15, label='策略超额收益')
ax1.axhline(y=100000, color='gray', linestyle=':', alpha=0.5, label='初始资金')
ax1.set_title('贵州茅台 - 海龟策略净值 vs 买入持有', fontsize=14, fontweight='bold')
ax1.set_ylabel('市值(元)')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

# 回撤对比
ax2 = axes[1]
cummax = df['strategy_value'].cummax()
drawdown = (df['strategy_value'] - cummax) / cummax * 100
bh_cummax = df['buy_hold_value'].cummax()
bh_drawdown = (df['buy_hold_value'] - bh_cummax) / bh_cummax * 100

ax2.fill_between(df['trade_date'], drawdown, 0, color='#8E44AD', alpha=0.3, label='海龟策略回撤')
ax2.fill_between(df['trade_date'], bh_drawdown, 0, color='#95A5A6', alpha=0.15, label='买入持有回撤')
ax2.set_title('回撤对比', fontsize=12, fontweight='bold')
ax2.set_ylabel('回撤(%)')
ax2.set_xlabel('日期')
ax2.legend(loc='lower left', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

plt.tight_layout()
plt.savefig('贵州茅台_净值与回撤.png', dpi=150, bbox_inches='tight')
plt.show()"""))

# ========== 多股票对比 ==========
cells.append(nbf.v4.new_markdown_cell("""## 四、多股票多参数对比分析\n\n### 4.1 多股票批量回测"""))
cells.append(nbf.v4.new_code_cell("""# 导入完整策略引擎
from turtle_strategy import run_strategy, run_batch_test

# 股票列表
stocks = {
    '贵州茅台': '贵州茅台_行情数据.csv',
    '比亚迪': '比亚迪_行情数据.csv',
    '宁德时代': '宁德时代_行情数据.csv',
    '中芯国际': '中芯国际_行情数据.csv',
    '三一重工': '三一重工_行情数据.csv',
    '平安集团': '平安集团_行情数据.csv',
}

# 参数组合
param_combos = [
    (20, 10, 20, 2.0),   # 经典海龟参数
    (20, 10, 20, 1.5),   # 更紧止损
    (20, 10, 20, 3.0),   # 更宽止损
    (55, 20, 20, 2.0),   # 长周期通道
    (10, 5, 20, 2.0),    # 短周期通道
]

print("=" * 80)
print("海龟交易策略 - 多股票多参数批量回测")
print("=" * 80)

results_df, detail_data = run_batch_test('.', stocks, param_combos)
print("\\n回测完成 ✓")
print(f"共测试 {len(stocks)} 只股票 × {len(param_combos)} 组参数 = {len(results_df)} 个结果")"""))

# ========== 结果汇总 ==========
cells.append(nbf.v4.new_code_cell("""# 经典参数对比表
classic = results_df[results_df['param'] == '入20/出10/ATR20/止2.0'].copy()
display_cols = ['stock', 'cumulative_return', 'max_drawdown', 'sharpe_ratio',
                'annual_return', 'win_rate', 'buy_count',
                'bh_cumulative_return', 'bh_max_drawdown', 'bh_sharpe_ratio']

print("=" * 100)
print("经典参数(20/10/20/2.0) 多股票回测结果")
print("=" * 100)
classic[display_cols].to_string(index=False)"""))

# ========== 参数分析 ==========
cells.append(nbf.v4.new_markdown_cell("""### 4.2 参数敏感性分析

通过调节核心参数，观察收益变化："""))
cells.append(nbf.v4.new_code_cell("""# 贵州茅台参数敏感性
print("=" * 80)
print("贵州茅台 - 参数敏感性分析")
print("=" * 80)
maotai = results_df[results_df['stock'] == '贵州茅台']
display_cols2 = ['param', 'cumulative_return', 'max_drawdown', 'sharpe_ratio', 'annual_return', 'win_rate', 'buy_count']
maotai[display_cols2].to_string(index=False)"""))

cells.append(nbf.v4.new_code_cell("""# 比亚迪参数敏感性
print("=" * 80)
print("比亚迪 - 参数敏感性分析")
print("=" * 80)
byd = results_df[results_df['stock'] == '比亚迪']
byd[display_cols2].to_string(index=False)"""))

# ========== 多股票对比图 ==========
cells.append(nbf.v4.new_code_cell("""# 多股票对比可视化
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

stocks_list = classic['stock'].tolist()
x = np.arange(len(stocks_list))
width = 0.35

# 累计回报对比
ax = axes[0]
ax.bar(x - width/2, classic['cumulative_return']*100, width, color='#8E44AD', label='海龟策略', alpha=0.85)
ax.bar(x + width/2, classic['bh_cumulative_return']*100, width, color='#95A5A6', label='买入持有', alpha=0.85)
ax.axhline(y=0, color='gray', linewidth=0.5)
ax.set_title('累计回报对比(%)', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(stocks_list, rotation=45, fontsize=9)
ax.legend(fontsize=8); ax.grid(True, alpha=0.3, axis='y')

# 最大回撤对比
ax = axes[1]
ax.bar(x - width/2, classic['max_drawdown']*100, width, color='#8E44AD', label='海龟策略', alpha=0.85)
ax.bar(x + width/2, classic['bh_max_drawdown']*100, width, color='#95A5A6', label='买入持有', alpha=0.85)
ax.set_title('最大回撤对比(%)', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(stocks_list, rotation=45, fontsize=9)
ax.legend(fontsize=8); ax.grid(True, alpha=0.3, axis='y')

# 夏普比率对比
ax = axes[2]
ax.bar(x - width/2, classic['sharpe_ratio'], width, color='#8E44AD', label='海龟策略', alpha=0.85)
ax.bar(x + width/2, classic['bh_sharpe_ratio'], width, color='#95A5A6', label='买入持有', alpha=0.85)
ax.axhline(y=0, color='gray', linewidth=0.5)
ax.set_title('夏普比率对比', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(stocks_list, rotation=45, fontsize=9)
ax.legend(fontsize=8); ax.grid(True, alpha=0.3, axis='y')

fig.suptitle('海龟策略 vs 买入持有 - 多股票对比(经典参数20/10/20/2.0)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('多股票对比.png', dpi=150, bbox_inches='tight')
plt.show()"""))

# ========== 总结 ==========
cells.append(nbf.v4.new_markdown_cell("""## 五、参数调节总结与使用心得

### 5.1 适应场景

| 场景 | 是否适合 | 原因 |
|------|----------|------|
| 强趋势市场 | ✅ 非常适合 | 突破信号可靠性高，能捕获大趋势 |
| 高波动成长股 | ✅ 适合 | ATR机制充分发挥作用，宁德时代+29.89% |
| 周期股 | ✅ 适合 | 趋势性强，三一重工Sharpe达1.07 |
| 震荡市场 | ❌ 不适合 | 突破信号频繁失效，连续止损 |
| 低流动性品种 | ❌ 不适合 | 滑点大，突破时无法理想成交 |
| 短线交易 | ❌ 不适合 | 信号频率低，持仓周期数周到数月 |

### 5.2 使用心得

1. **纪律性是灵魂** — 策略不难，难在严格执行。程序化交易的价值在于它不会犹豫
2. **"截断亏损，让利润奔跑"** — 胜率30-50%不高，但少数大赢覆盖多数小亏
3. **参数不宜过度优化** — 经典20/10/2.0参数已经不错，过度优化容易过拟合
4. **ATR是最被低估的指标** — 让策略自动适应不同波动率环境
5. **不期待跑赢牛市买入持有** — 海龟价值在于风险调整后收益和熊市防御
6. **多品种分散风险** — 构建多股票组合，避免重仓单一标的
7. **A股需要适配** — T+1、涨跌停限制、做空受限等特性影响效果

### 5.3 最终结论

海龟交易法则的核心价值不在于神秘的技术指标，而在于把**趋势跟踪 + 风险管理 + 资金管理**三者完美结合成了一套可执行的系统。本次回测验证了：

- **宁德时代**：策略 +29.89%，趋势跟踪在高波动成长股上表现优异
- **比亚迪**：策略 +4.28% vs 买入持有 -64.41%，暴跌行情中展现强大防御力
- **三一重工**：Sharpe 1.07，MDD仅-11.14%，周期股上风控效果最佳
- **中芯国际**：胜率75%，半导体高波动股票上趋势跟踪有效

**海龟策略给我们的最大启示：交易不是预测，而是应对。你不需要知道市场往哪走，你只需要知道——如果市场往上涨你该怎么做，如果往下跌你该怎么做。然后，严格执行。**
"""))

# 写入Notebook
nb['cells'] = cells
nb_path = os.path.join(DATA_DIR, '海龟策略实战演练.ipynb')
with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook已生成: {nb_path}")
print(f"单元格数: {len(cells)}")
