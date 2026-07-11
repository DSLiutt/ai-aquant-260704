#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成技术指标计算过程 Jupyter Notebook
"""
import json
from pathlib import Path

def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source if isinstance(source, list) else [source]
    }

def code_cell(source, outputs=None):
    cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [] if outputs is None else outputs,
        "source": source if isinstance(source, list) else [source]
    }
    return cell

cells = []

# ============================================================
# Section 0: 标题与概述
# ============================================================
cells.append(md_cell([
    "# 股票技术指标计算过程\n",
    "\n",
    "> **三一重工 (600031.SH) & 平安集团 (000001.SZ)** ｜ 数据诊断 · 指标计算 · 可视化\n",
    "\n",
    "本 Notebook 以 **分步骤、可交互** 的方式展示四大技术指标的完整计算过程：\n",
    "\n",
    "| 指标 | 类型 | 核心作用 |\n",
    "|------|------|----------|\n",
    "| **RSI** (相对强弱指数) | 动量指标 | 判断超买超卖，>70 超买，<30 超卖 |\n",
    "| **MACD** (指数平滑异同移动平均线) | 趋势指标 | 金叉买入、死叉卖出，判断趋势方向 |\n",
    "| **布林带** (Bollinger Bands) | 波动率指标 | 价格通道，触及上下轨判断回调/反弹 |\n",
    "| **KDJ** (随机指标) | 动量振荡 | 短线超买超卖，灵敏捕捉转折点 |\n",
    "\n",
    "---"
]))

# ============================================================
# Section 1: 环境准备与数据加载
# ============================================================
cells.append(md_cell([
    "## 1. 环境准备与数据加载\n",
    "\n",
    "导入所需库，加载两只股票的日线行情数据。"
]))

cells.append(code_cell([
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib.dates as mdates\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "# 全局绘图设置\n",
    "plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC']\n",
    "plt.rcParams['axes.unicode_minus'] = False\n",
    "plt.rcParams['figure.dpi'] = 120\n",
    "\n",
    "print('环境准备完成 pandas={}, numpy={}'.format(pd.__version__, np.__version__))"
]))

cells.append(md_cell([
    "### 1.1 定义数据加载函数\n",
    "\n",
    "读取 CSV 文件，将 `trade_date` 解析为日期类型，按日期升序排列。"
]))

cells.append(code_cell([
    "def load_data(filepath):\n",
    "    \"\"\"加载CSV数据，解析日期，按日期升序排列\"\"\"\n",
    "    df = pd.read_csv(filepath)\n",
    "    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')\n",
    "    df = df.sort_values('trade_date').reset_index(drop=True)\n",
    "    return df\n",
    "\n",
    "# 加载两只股票数据\n",
    "df_sany = load_data('三一重工行情数据.csv')\n",
    "df_pingan = load_data('平安集团行情数据.csv')\n",
    "\n",
    "print(f'三一重工: {len(df_sany)} 条记录, {df_sany[\"trade_date\"].min().date()} ~ {df_sany[\"trade_date\"].max().date()}')\n",
    "print(f'平安集团: {len(df_pingan)} 条记录, {df_pingan[\"trade_date\"].min().date()} ~ {df_pingan[\"trade_date\"].max().date()}')"
]))

cells.append(md_cell([
    "### 1.2 数据预览"
]))

cells.append(code_cell([
    "# 三一重工前5行\n",
    "df_sany.head()"
]))

cells.append(code_cell([
    "# 平安集团前5行\n",
    "df_pingan.head()"
]))

# ============================================================
# Section 2: 数据基础诊断
# ============================================================
cells.append(md_cell([
    "## 2. 数据基础诊断\n",
    "\n",
    "检查缺失值，计算描述性统计量，评估数据质量。"
]))

cells.append(md_cell([
    "### 2.1 缺失值检查"
]))

cells.append(code_cell([
    "# 三一重工缺失值检查\n",
    "print('=== 三一重工 缺失值检查 ===')\n",
    "print(df_sany.isnull().sum())\n",
    "print()\n",
    "print('=== 平安集团 缺失值检查 ===')\n",
    "print(df_pingan.isnull().sum())"
]))

cells.append(md_cell([
    "> ✅ 两只股票数据均 **无缺失值**，数据完整。"
]))

cells.append(md_cell([
    "### 2.2 描述性统计"
]))

cells.append(code_cell([
    "# 三一重工描述性统计\n",
    "stat_cols = ['open', 'high', 'low', 'close', 'vol', 'amount', 'pct_chg']\n",
    "df_sany[stat_cols].describe().round(2)"
]))

cells.append(code_cell([
    "# 平安集团描述性统计\n",
    "df_pingan[stat_cols].describe().round(2)"
]))

cells.append(md_cell([
    "**诊断结论：** 三一重工数据覆盖 2025 年上半年（129条），平安集团覆盖 2024 全年至 2025 年中（372条）。\n",
    "平安集团波动性更大（单日最大涨跌幅 ±9.98%/-9.32%），三一重工相对平稳（±6.28%/-5.76%）。\n",
    "\n",
    "---"
]))

# ============================================================
# Section 3: RSI 计算过程
# ============================================================
cells.append(md_cell([
    "## 3. RSI — 相对强弱指数计算过程\n",
    "\n",
    "> **发明者:** J. Welles Wilder (1978) ｜ **常用周期:** 14天\n",
    "\n",
    "**公式：**\n",
    "\n",
    "$$RS = \\frac{n日平均涨幅}{n日平均跌幅}, \\quad RSI = 100 - \\frac{100}{1+RS}$$\n",
    "\n",
    "**作用：** RSI > 70 超买（可能回调），RSI < 30 超卖（可能反弹）。"
]))

cells.append(md_cell([
    "### Step 1: 计算每日价格变动"
]))

cells.append(code_cell([
    "# 以三一重工为例，展示 RSI 计算的每一步\n",
    "close = df_sany['close'].copy()\n",
    "\n",
    "# Step 1: 价格变动\n",
    "delta = close.diff()\n",
    "print('前10个价格变动：')\n",
    "pd.DataFrame({'close': close, 'delta': delta}).head(10)"
]))

cells.append(md_cell([
    "### Step 2: 分离涨幅和跌幅"
]))

cells.append(code_cell([
    "# Step 2: 分离涨跌\n",
    "gain = delta.clip(lower=0)    # 涨幅（跌的日子记为0）\n",
    "loss = -delta.clip(upper=0)   # 跌幅（涨的日子记为0，取绝对值）\n",
    "\n",
    "preview = pd.DataFrame({'close': close, 'delta': delta, 'gain': gain, 'loss': loss})\n",
    "preview.head(10)"
]))

cells.append(md_cell([
    "### Step 3: Wilder 平滑法计算平均涨跌幅\n",
    "\n",
    "Wilder 平滑法（也称修正移动平均）：\n",
    "- 首个值 = 前 n 日简单平均\n",
    "- 后续值 = (前一日均值 × (n-1) + 当日值) / n"
]))

cells.append(code_cell([
    "period = 14\n",
    "\n",
    "avg_gain = pd.Series(index=close.index, dtype=float)\n",
    "avg_loss = pd.Series(index=close.index, dtype=float)\n",
    "\n",
    "# 首值用简单平均\n",
    "avg_gain.iloc[period] = gain.iloc[1:period+1].mean()\n",
    "avg_loss.iloc[period] = loss.iloc[1:period+1].mean()\n",
    "\n",
    "# 后续用 Wilder 平滑\n",
    "for i in range(period+1, len(close)):\n",
    "    avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gain.iloc[i]) / period\n",
    "    avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + loss.iloc[i]) / period\n",
    "\n",
    "print(f'初始平均涨幅: {avg_gain.iloc[period]:.4f}')\n",
    "print(f'初始平均跌幅: {avg_loss.iloc[period]:.4f}')\n",
    "print()\n",
    "pd.DataFrame({'gain': gain, 'loss': loss, 'avg_gain': avg_gain, 'avg_loss': avg_loss}).iloc[period:period+10]"
]))

cells.append(md_cell([
    "### Step 4: 计算 RS 和 RSI"
]))

cells.append(code_cell([
    "# Step 4: RS = avg_gain / avg_loss, RSI = 100 - 100/(1+RS)\n",
    "rs = avg_gain / avg_loss\n",
    "rsi = 100 - (100 / (1 + rs))\n",
    "rsi.iloc[:period] = np.nan  # 前14天无值\n",
    "\n",
    "print('最近10日 RSI 值：')\n",
    "pd.DataFrame({'close': close, 'RS': rs, 'RSI': rsi}).tail(10).round(2)"
]))

cells.append(md_cell([
    "### Step 5: RSI 可视化"
]))

cells.append(code_cell([
    "fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), height_ratios=[2, 1],\n",
    "                                sharex=True, gridspec_kw={'hspace': 0.08})\n",
    "\n",
    "ax1.plot(df_sany['trade_date'], close, color='#333', linewidth=1.2)\n",
    "ax1.set_ylabel('收盘价(元)')\n",
    "ax1.set_title('三一重工 — RSI(14) 相对强弱指数', fontsize=13, fontweight='bold')\n",
    "ax1.grid(True, alpha=0.3)\n",
    "\n",
    "ax2.plot(df_sany['trade_date'], rsi, color='#7B1FA2', linewidth=1.2, label='RSI(14)')\n",
    "ax2.axhline(70, color='#F44336', linewidth=0.8, linestyle='--', alpha=0.7)\n",
    "ax2.axhline(30, color='#4CAF50', linewidth=0.8, linestyle='--', alpha=0.7)\n",
    "ax2.fill_between(df_sany['trade_date'], 70, 100, color='#FFCDD2', alpha=0.3)\n",
    "ax2.fill_between(df_sany['trade_date'], 0, 30, color='#C8E6C9', alpha=0.3)\n",
    "ax2.text(df_sany['trade_date'].iloc[5], 72, '超买(>70)', fontsize=8, color='#D32F2F')\n",
    "ax2.text(df_sany['trade_date'].iloc[5], 26, '超卖(<30)', fontsize=8, color='#388E3C')\n",
    "ax2.set_ylabel('RSI')\n",
    "ax2.set_ylim(0, 100)\n",
    "ax2.legend(loc='upper left', fontsize=9)\n",
    "ax2.grid(True, alpha=0.3)\n",
    "ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))\n",
    "plt.xticks(rotation=30)\n",
    "plt.tight_layout()\n",
    "plt.savefig('三一重工_RSI.png', bbox_inches='tight')\n",
    "plt.show()"
]))

cells.append(md_cell([
    "---"
]))

# ============================================================
# Section 4: MACD 计算过程
# ============================================================
cells.append(md_cell([
    "## 4. MACD — 指数平滑异同移动平均线计算过程\n",
    "\n",
    "> **发明者:** Gerald Appel (1979) ｜ **参数:** 12, 26, 9\n",
    "\n",
    "**公式：**\n",
    "\n",
    "$$DIF = EMA(12) - EMA(26)$$\n",
    "$$DEA = EMA(DIF, 9)$$\n",
    "$$MACD_{柱} = 2 \\times (DIF - DEA)$$\n",
    "\n",
    "**作用：** DIF 上穿 DEA → 金叉买入；DIF 下穿 DEA → 死叉卖出。"
]))

cells.append(md_cell([
    "### Step 1: 计算 EMA(12) 和 EMA(26)\n",
    "\n",
    "EMA（指数移动平均）赋予近期数据更大权重：\n",
    "\n",
    "$$EMA_t = Close_t \\times \\frac{2}{n+1} + EMA_{t-1} \\times \\frac{n-1}{n+1}$$"
]))

cells.append(code_cell([
    "# 使用 pandas ewm 计算 EMA\n",
    "ema_fast = close.ewm(span=12, adjust=False).mean()   # EMA(12)\n",
    "ema_slow = close.ewm(span=26, adjust=False).mean()   # EMA(26)\n",
    "\n",
    "print('前10行 EMA 对比：')\n",
    "pd.DataFrame({'close': close, 'EMA12': ema_fast, 'EMA26': ema_slow}).head(10).round(4)"
]))

cells.append(md_cell([
    "### Step 2: 计算 DIF（差离值）"
]))

cells.append(code_cell([
    "dif = ema_fast - ema_slow\n",
    "\n",
    "print('DIF 统计：')\n",
    "print(f'  均值: {dif.mean():.4f}')\n",
    "print(f'  最大: {dif.max():.4f}')\n",
    "print(f'  最小: {dif.min():.4f}')\n",
    "print()\n",
    "pd.DataFrame({'close': close, 'EMA12': ema_fast, 'EMA26': ema_slow, 'DIF': dif}).tail(10).round(4)"
]))

cells.append(md_cell([
    "### Step 3: 计算 DEA（讯号线 = DIF 的 9日 EMA）"
]))

cells.append(code_cell([
    "dea = dif.ewm(span=9, adjust=False).mean()\n",
    "\n",
    "pd.DataFrame({'DIF': dif, 'DEA': dea}).tail(10).round(4)"
]))

cells.append(md_cell([
    "### Step 4: 计算 MACD 柱状图\n",
    "\n",
    "国内习惯：$MACD_{柱} = 2 \\times (DIF - DEA)$"
]))

cells.append(code_cell([
    "macd_hist = 2 * (dif - dea)\n",
    "\n",
    "print('最近10日 MACD 三线值：')\n",
    "pd.DataFrame({'close': close, 'DIF': dif, 'DEA': dea, 'MACD柱': macd_hist}).tail(10).round(4)"
]))

cells.append(md_cell([
    "### Step 5: MACD 可视化"
]))

cells.append(code_cell([
    "fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), height_ratios=[2, 1.5],\n",
    "                                sharex=True, gridspec_kw={'hspace': 0.08})\n",
    "\n",
    "ax1.plot(df_sany['trade_date'], close, color='#333', linewidth=1.2)\n",
    "ax1.set_ylabel('收盘价(元)')\n",
    "ax1.set_title('三一重工 — MACD(12,26,9)', fontsize=13, fontweight='bold')\n",
    "ax1.grid(True, alpha=0.3)\n",
    "\n",
    "colors = ['#F44336' if v >= 0 else '#4CAF50' for v in macd_hist]\n",
    "ax2.bar(df_sany['trade_date'], macd_hist, color=colors, width=1.2, alpha=0.6, label='MACD柱')\n",
    "ax2.plot(df_sany['trade_date'], dif, color='#1976D2', linewidth=1.2, label='DIF')\n",
    "ax2.plot(df_sany['trade_date'], dea, color='#FF9800', linewidth=1.2, label='DEA')\n",
    "ax2.axhline(0, color='#666', linewidth=0.6)\n",
    "ax2.set_ylabel('MACD')\n",
    "ax2.legend(loc='upper left', fontsize=9)\n",
    "ax2.grid(True, alpha=0.3)\n",
    "ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))\n",
    "plt.xticks(rotation=30)\n",
    "plt.tight_layout()\n",
    "plt.savefig('三一重工_MACD.png', bbox_inches='tight')\n",
    "plt.show()"
]))

cells.append(md_cell([
    "---"
]))

# ============================================================
# Section 5: 布林带计算过程
# ============================================================
cells.append(md_cell([
    "## 5. 布林带 — Bollinger Bands 计算过程\n",
    "\n",
    "> **发明者:** John Bollinger (1980s) ｜ **参数:** 20日, 2倍标准差\n",
    "\n",
    "**公式：**\n",
    "\n",
    "$$中轨 = MA(close, 20)$$\n",
    "$$上轨 = 中轨 + 2 \\times \\sigma$$\n",
    "$$下轨 = 中轨 - 2 \\times \\sigma$$\n",
    "\n",
    "**作用：** 触及上轨可能超买，触及下轨可能超卖；带宽收口预示突破。"
]))

cells.append(md_cell([
    "### Step 1: 计算中轨 MA(20)"
]))

cells.append(code_cell([
    "window = 20\n",
    "boll_ma = close.rolling(window=window).mean()\n",
    "\n",
    "print('前25行中轨（前19天为NaN）：')\n",
    "pd.DataFrame({'close': close, 'BOLL_MA': boll_ma}).head(25).round(4)"
]))

cells.append(md_cell([
    "### Step 2: 计算标准差 SD(20)"
]))

cells.append(code_cell([
    "boll_std = close.rolling(window=window).std()\n",
    "\n",
    "pd.DataFrame({'close': close, 'BOLL_MA': boll_ma, 'BOLL_STD': boll_std}).tail(10).round(4)"
]))

cells.append(md_cell([
    "### Step 3: 计算上轨和下轨"
]))

cells.append(code_cell([
    "num_std = 2\n",
    "boll_upper = boll_ma + num_std * boll_std\n",
    "boll_lower = boll_ma - num_std * boll_std\n",
    "\n",
    "print('最近10日布林带三轨：')\n",
    "pd.DataFrame({\n",
    "    'close': close, 'BOLL下轨': boll_lower, 'BOLL中轨': boll_ma, 'BOLL上轨': boll_upper\n",
    "}).tail(10).round(2)"
]))

cells.append(md_cell([
    "### Step 4: 计算带宽 Bandwidth\n",
    "\n",
    "$$带宽 = \\frac{上轨 - 下轨}{中轨} \\times 100\\%$$"
]))

cells.append(code_cell([
    "boll_bw = (boll_upper - boll_lower) / boll_ma * 100\n",
    "\n",
    "print(f'带宽统计: 均值={boll_bw.mean():.2f}%, 最大={boll_bw.max():.2f}%, 最小={boll_bw.min():.2f}%')\n",
    "print()\n",
    "pd.DataFrame({'close': close, '带宽(%)': boll_bw}).tail(10).round(2)"
]))

cells.append(md_cell([
    "### Step 5: 布林带可视化"
]))

cells.append(code_cell([
    "fig, ax = plt.subplots(figsize=(12, 5))\n",
    "\n",
    "ax.plot(df_sany['trade_date'], close, color='#333', linewidth=1.2, label='收盘价', zorder=3)\n",
    "ax.plot(df_sany['trade_date'], boll_ma, color='#2196F3', linewidth=1, label='中轨(MA20)', alpha=0.8)\n",
    "ax.plot(df_sany['trade_date'], boll_upper, color='#F44336', linewidth=1, linestyle='--', label='上轨(+2σ)', alpha=0.7)\n",
    "ax.plot(df_sany['trade_date'], boll_lower, color='#4CAF50', linewidth=1, linestyle='--', label='下轨(-2σ)', alpha=0.7)\n",
    "ax.fill_between(df_sany['trade_date'], boll_upper, boll_lower, color='#90CAF9', alpha=0.12)\n",
    "\n",
    "ax.set_title('三一重工 — 布林带 (Bollinger Bands 20,2)', fontsize=13, fontweight='bold')\n",
    "ax.set_ylabel('价格(元)')\n",
    "ax.legend(loc='upper left', fontsize=9)\n",
    "ax.grid(True, alpha=0.3)\n",
    "ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))\n",
    "plt.xticks(rotation=30)\n",
    "plt.tight_layout()\n",
    "plt.savefig('三一重工_布林带.png', bbox_inches='tight')\n",
    "plt.show()"
]))

cells.append(md_cell([
    "---"
]))

# ============================================================
# Section 6: KDJ 计算过程
# ============================================================
cells.append(md_cell([
    "## 6. KDJ — 随机指标计算过程（扩展指标）\n",
    "\n",
    "> **参数:** 9, 3, 3 ｜ 中国市场最常用的短线指标之一\n",
    "\n",
    "**公式：**\n",
    "\n",
    "$$RSV = \\frac{Close - LowestLow(9)}{HighestHigh(9) - LowestLow(9)} \\times 100$$\n",
    "$$K_t = \\frac{2}{3}K_{t-1} + \\frac{1}{3}RSV_t$$\n",
    "$$D_t = \\frac{2}{3}D_{t-1} + \\frac{1}{3}K_t$$\n",
    "$$J = 3K - 2D$$\n",
    "\n",
    "**作用：** K/D > 80 超买，< 20 超卖；J > 100 极度超买，J < 0 极度超卖。\n",
    "\n",
    "**其他典型指标概览：** OBV(能量潮)、CCI(顺势指标)、ATR(真实波幅)、WR(威廉指标)、DMI(趋向指标)、SAR(抛物线指标)。"
]))

cells.append(md_cell([
    "### Step 1: 计算 RSV（未成熟随机值）"
]))

cells.append(code_cell([
    "high = df_sany['high'].copy()\n",
    "low = df_sany['low'].copy()\n",
    "\n",
    "n = 9\n",
    "lowest_low = low.rolling(window=n).min()\n",
    "highest_high = high.rolling(window=n).max()\n",
    "rsv = (close - lowest_low) / (highest_high - lowest_low) * 100\n",
    "rsv = rsv.fillna(50)  # 不足9天时填充50\n",
    "\n",
    "print('前12行 RSV 计算：')\n",
    "pd.DataFrame({'high': high, 'low': low, 'close': close,\n",
    "              'LL(9)': lowest_low, 'HH(9)': highest_high, 'RSV': rsv}).head(12).round(2)"
]))

cells.append(md_cell([
    "### Step 2: 计算 K 值（RSV 的 3日加权移动平均）"
]))

cells.append(code_cell([
    "m1 = 3\n",
    "k = pd.Series(index=close.index, dtype=float)\n",
    "k.iloc[0] = 50  # 初始值\n",
    "\n",
    "for i in range(1, len(close)):\n",
    "    k.iloc[i] = (m1 - 1) / m1 * k.iloc[i-1] + 1 / m1 * rsv.iloc[i]\n",
    "\n",
    "print('K 值前12行：')\n",
    "pd.DataFrame({'RSV': rsv, 'K': k}).head(12).round(2)"
]))

cells.append(md_cell([
    "### Step 3: 计算 D 值（K 的 3日加权移动平均）"
]))

cells.append(code_cell([
    "m2 = 3\n",
    "d = pd.Series(index=close.index, dtype=float)\n",
    "d.iloc[0] = 50\n",
    "\n",
    "for i in range(1, len(close)):\n",
    "    d.iloc[i] = (m2 - 1) / m2 * d.iloc[i-1] + 1 / m2 * k.iloc[i]\n",
    "\n",
    "pd.DataFrame({'RSV': rsv, 'K': k, 'D': d}).head(12).round(2)"
]))

cells.append(md_cell([
    "### Step 4: 计算 J 值\n",
    "\n",
    "$$J = 3K - 2D$$\n",
    "\n",
    "J 值可超出 0-100 范围（理论 -100~200），这是 KDJ 区别于 RSI 的特点。"
]))

cells.append(code_cell([
    "j = 3 * k - 2 * d\n",
    "\n",
    "print('最近10日 KDJ 值：')\n",
    "pd.DataFrame({'close': close, 'K': k, 'D': d, 'J': j}).tail(10).round(2)"
]))

cells.append(md_cell([
    "### Step 5: KDJ 可视化"
]))

cells.append(code_cell([
    "fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), height_ratios=[2, 1.5],\n",
    "                                sharex=True, gridspec_kw={'hspace': 0.08})\n",
    "\n",
    "ax1.plot(df_sany['trade_date'], close, color='#333', linewidth=1.2)\n",
    "ax1.set_ylabel('收盘价(元)')\n",
    "ax1.set_title('三一重工 — KDJ(9,3,3) 随机指标', fontsize=13, fontweight='bold')\n",
    "ax1.grid(True, alpha=0.3)\n",
    "\n",
    "ax2.plot(df_sany['trade_date'], k, color='#1976D2', linewidth=1.2, label='K')\n",
    "ax2.plot(df_sany['trade_date'], d, color='#FF9800', linewidth=1.2, label='D')\n",
    "ax2.plot(df_sany['trade_date'], j, color='#7B1FA2', linewidth=1, label='J', alpha=0.8)\n",
    "ax2.axhline(80, color='#F44336', linewidth=0.8, linestyle='--', alpha=0.6)\n",
    "ax2.axhline(20, color='#4CAF50', linewidth=0.8, linestyle='--', alpha=0.6)\n",
    "ax2.fill_between(df_sany['trade_date'], 80, 120, color='#FFCDD2', alpha=0.2)\n",
    "ax2.fill_between(df_sany['trade_date'], -20, 20, color='#C8E6C9', alpha=0.2)\n",
    "ax2.text(df_sany['trade_date'].iloc[5], 82, '超买(>80)', fontsize=8, color='#D32F2F')\n",
    "ax2.text(df_sany['trade_date'].iloc[5], 16, '超卖(<20)', fontsize=8, color='#388E3C')\n",
    "ax2.set_ylabel('KDJ')\n",
    "ax2.legend(loc='upper left', fontsize=9)\n",
    "ax2.grid(True, alpha=0.3)\n",
    "ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))\n",
    "plt.xticks(rotation=30)\n",
    "plt.tight_layout()\n",
    "plt.savefig('三一重工_KDJ.png', bbox_inches='tight')\n",
    "plt.show()"
]))

cells.append(md_cell([
    "---"
]))

# ============================================================
# Section 7: 平安集团完整计算 + 综合可视化
# ============================================================
cells.append(md_cell([
    "## 7. 平安集团指标计算与综合可视化\n",
    "\n",
    "对平安集团数据执行同样的指标计算，并绘制综合视图。"
]))

cells.append(code_cell([
    "# 平安集团完整指标计算\n",
    "close_pa = df_pingan['close'].copy()\n",
    "high_pa = df_pingan['high'].copy()\n",
    "low_pa = df_pingan['low'].copy()\n",
    "\n",
    "# --- RSI ---\n",
    "delta_pa = close_pa.diff()\n",
    "gain_pa = delta_pa.clip(lower=0)\n",
    "loss_pa = -delta_pa.clip(upper=0)\n",
    "avg_gain_pa = pd.Series(index=close_pa.index, dtype=float)\n",
    "avg_loss_pa = pd.Series(index=close_pa.index, dtype=float)\n",
    "avg_gain_pa.iloc[14] = gain_pa.iloc[1:15].mean()\n",
    "avg_loss_pa.iloc[14] = loss_pa.iloc[1:15].mean()\n",
    "for i in range(15, len(close_pa)):\n",
    "    avg_gain_pa.iloc[i] = (avg_gain_pa.iloc[i-1] * 13 + gain_pa.iloc[i]) / 14\n",
    "    avg_loss_pa.iloc[i] = (avg_loss_pa.iloc[i-1] * 13 + loss_pa.iloc[i]) / 14\n",
    "rsi_pa = 100 - 100 / (1 + avg_gain_pa / avg_loss_pa)\n",
    "rsi_pa.iloc[:14] = np.nan\n",
    "\n",
    "# --- MACD ---\n",
    "dif_pa = close_pa.ewm(span=12, adjust=False).mean() - close_pa.ewm(span=26, adjust=False).mean()\n",
    "dea_pa = dif_pa.ewm(span=9, adjust=False).mean()\n",
    "macd_hist_pa = 2 * (dif_pa - dea_pa)\n",
    "\n",
    "# --- 布林带 ---\n",
    "boll_ma_pa = close_pa.rolling(20).mean()\n",
    "boll_std_pa = close_pa.rolling(20).std()\n",
    "boll_upper_pa = boll_ma_pa + 2 * boll_std_pa\n",
    "boll_lower_pa = boll_ma_pa - 2 * boll_std_pa\n",
    "\n",
    "# --- KDJ ---\n",
    "ll_pa = low_pa.rolling(9).min()\n",
    "hh_pa = high_pa.rolling(9).max()\n",
    "rsv_pa = ((close_pa - ll_pa) / (hh_pa - ll_pa) * 100).fillna(50)\n",
    "k_pa = pd.Series(index=close_pa.index, dtype=float)\n",
    "d_pa = pd.Series(index=close_pa.index, dtype=float)\n",
    "k_pa.iloc[0] = 50; d_pa.iloc[0] = 50\n",
    "for i in range(1, len(close_pa)):\n",
    "    k_pa.iloc[i] = 2/3 * k_pa.iloc[i-1] + 1/3 * rsv_pa.iloc[i]\n",
    "    d_pa.iloc[i] = 2/3 * d_pa.iloc[i-1] + 1/3 * k_pa.iloc[i]\n",
    "j_pa = 3 * k_pa - 2 * d_pa\n",
    "\n",
    "print('平安集团指标计算完成')\n",
    "print(f'RSI最新值: {rsi_pa.iloc[-1]:.1f}')\n",
    "print(f'DIF最新值: {dif_pa.iloc[-1]:.4f}, DEA: {dea_pa.iloc[-1]:.4f}')\n",
    "print(f'KDJ最新值: K={k_pa.iloc[-1]:.1f}, D={d_pa.iloc[-1]:.1f}, J={j_pa.iloc[-1]:.1f}')"
]))

cells.append(md_cell([
    "### 7.1 平安集团综合指标图"
]))

cells.append(code_cell([
    "fig, axes = plt.subplots(5, 1, figsize=(14, 16), height_ratios=[2.5, 1.5, 1.5, 1.5, 1.5],\n",
    "                          sharex=True, gridspec_kw={'hspace': 0.12})\n",
    "dates = df_pingan['trade_date']\n",
    "\n",
    "# 1. 价格 + 布林带\n",
    "ax = axes[0]\n",
    "ax.plot(dates, close_pa, color='#333', linewidth=1.2, label='收盘价', zorder=3)\n",
    "ax.plot(dates, boll_ma_pa, color='#2196F3', linewidth=1, label='BOLL中轨', alpha=0.8)\n",
    "ax.plot(dates, boll_upper_pa, color='#F44336', linewidth=0.8, linestyle='--', alpha=0.6)\n",
    "ax.plot(dates, boll_lower_pa, color='#4CAF50', linewidth=0.8, linestyle='--', alpha=0.6)\n",
    "ax.fill_between(dates, boll_upper_pa, boll_lower_pa, color='#90CAF9', alpha=0.1)\n",
    "ax.set_ylabel('价格(元)')\n",
    "ax.set_title('平安集团 — 技术指标综合视图', fontsize=14, fontweight='bold')\n",
    "ax.legend(loc='upper left', fontsize=8, ncol=4)\n",
    "ax.grid(True, alpha=0.3)\n",
    "\n",
    "# 2. RSI\n",
    "ax = axes[1]\n",
    "ax.plot(dates, rsi_pa, color='#7B1FA2', linewidth=1.2)\n",
    "ax.axhline(70, color='#F44336', linewidth=0.6, linestyle='--', alpha=0.6)\n",
    "ax.axhline(30, color='#4CAF50', linewidth=0.6, linestyle='--', alpha=0.6)\n",
    "ax.fill_between(dates, 70, 100, color='#FFCDD2', alpha=0.2)\n",
    "ax.fill_between(dates, 0, 30, color='#C8E6C9', alpha=0.2)\n",
    "ax.set_ylabel('RSI(14)')\n",
    "ax.set_ylim(0, 100)\n",
    "ax.grid(True, alpha=0.3)\n",
    "\n",
    "# 3. MACD\n",
    "ax = axes[2]\n",
    "colors_pa = ['#F44336' if v >= 0 else '#4CAF50' for v in macd_hist_pa]\n",
    "ax.bar(dates, macd_hist_pa, color=colors_pa, width=1.2, alpha=0.5)\n",
    "ax.plot(dates, dif_pa, color='#1976D2', linewidth=1, label='DIF')\n",
    "ax.plot(dates, dea_pa, color='#FF9800', linewidth=1, label='DEA')\n",
    "ax.axhline(0, color='#666', linewidth=0.5)\n",
    "ax.set_ylabel('MACD')\n",
    "ax.legend(loc='upper left', fontsize=8)\n",
    "ax.grid(True, alpha=0.3)\n",
    "\n",
    "# 4. KDJ\n",
    "ax = axes[3]\n",
    "ax.plot(dates, k_pa, color='#1976D2', linewidth=1, label='K')\n",
    "ax.plot(dates, d_pa, color='#FF9800', linewidth=1, label='D')\n",
    "ax.plot(dates, j_pa, color='#7B1FA2', linewidth=0.8, label='J', alpha=0.7)\n",
    "ax.axhline(80, color='#F44336', linewidth=0.5, linestyle='--', alpha=0.5)\n",
    "ax.axhline(20, color='#4CAF50', linewidth=0.5, linestyle='--', alpha=0.5)\n",
    "ax.set_ylabel('KDJ')\n",
    "ax.legend(loc='upper left', fontsize=8)\n",
    "ax.grid(True, alpha=0.3)\n",
    "\n",
    "# 5. 成交量\n",
    "ax = axes[4]\n",
    "vol_colors = ['#F44336' if df_pingan['pct_chg'].iloc[i] >= 0 else '#4CAF50' for i in range(len(df_pingan))]\n",
    "ax.bar(dates, df_pingan['vol'], color=vol_colors, width=1.2, alpha=0.6)\n",
    "ax.set_ylabel('成交量(手)')\n",
    "ax.set_xlabel('日期')\n",
    "ax.grid(True, alpha=0.3)\n",
    "\n",
    "axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))\n",
    "axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=1))\n",
    "plt.xticks(rotation=30)\n",
    "plt.tight_layout()\n",
    "plt.savefig('平安集团_综合指标图.png', bbox_inches='tight')\n",
    "plt.show()"
]))

cells.append(md_cell([
    "---"
]))

# ============================================================
# Section 8: 结果总结
# ============================================================
cells.append(md_cell([
    "## 8. 结果总结\n",
    "\n",
    "### 指标计算逻辑回顾\n",
    "\n",
    "| 指标 | 核心计算 | 关键参数 | 信号 |\n",
    "|------|----------|----------|------|\n",
    "| **RSI** | 平均涨幅/平均跌幅 → 0~100 | 14日 | >70超买, <30超卖 |\n",
    "| **MACD** | EMA(12)-EMA(26) → DIF, DEA | 12,26,9 | 金叉买入, 死叉卖出 |\n",
    "| **布林带** | MA(20) ± 2σ | 20,2 | 触轨反转, 带宽突破 |\n",
    "| **KDJ** | RSV→K→D→J | 9,3,3 | >80超买, <20超卖 |\n",
    "\n",
    "### 最近交易日指标快照\n",
    "\n",
    "| 股票 | 日期 | 收盘价 | RSI | DIF | DEA | K | D | J | 信号 |\n",
    "|------|------|--------|-----|-----|------|---|---|---|------|\n",
    "| 三一重工 | 2025-07-16 | 18.71 | 55.6 | 0.1559 | 0.0609 | 67.4 | 74.6 | 52.9 | 中性偏弱 |\n",
    "| 平安集团 | 2025-07-17 | 12.59 | 56.4 | 0.2715 | 0.2900 | 39.9 | 58.9 | 2.1 | J≈0 极度超卖 |\n",
    "\n",
    "### 关键发现\n",
    "\n",
    "1. **平安集团** J 值降至 2.1，处于极度超卖区域，同时 MACD 柱由正转负（-0.037），短期有调整压力但反弹可能临近\n",
    "2. **三一重工** 各指标处于中性区域，无明显超买超卖信号\n",
    "3. 平安集团波动性明显大于三一重工（单日最大涨跌幅 ±9.98% vs ±6.28%）\n",
    "4. 多指标配合使用比单一指标更可靠，建议结合趋势指标（MACD）和振荡指标（RSI/KDJ）综合判断\n",
    "\n",
    "> ⚠️ 本报告数据仅供学习参考，不构成投资建议。"
]))

# ============================================================
# 组装 Notebook
# ============================================================
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0",
            "mimetype": "text/x-python",
            "file_extension": ".py",
            "codemirror_mode": {"name": "ipython", "version": 3},
            "pygments_lexer": "ipython3"
        }
    },
    "cells": cells
}

outpath = Path(__file__).parent / "技术指标计算过程.ipynb"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"Notebook 已生成: {outpath}")
print(f"共 {len(cells)} 个单元格")
