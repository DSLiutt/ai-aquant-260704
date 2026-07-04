#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票技术分析：数据诊断 + RSI/MACD/布林带/KDJ 指标计算与可视化
数据：三一重工(600031.SH)、平安集团(000001.SZ)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ---------- 全局设置 ----------
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

BASE_DIR = Path(__file__).parent
FILES = {
    '三一重工': BASE_DIR / '三一重工行情数据.csv',
    '平安集团': BASE_DIR / '平安集团行情数据.csv',
}


# ============================================================
#  1. 数据加载与基础诊断
# ============================================================
def load_data(filepath):
    """加载CSV数据，解析日期，按日期升序排列"""
    df = pd.read_csv(filepath)
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df


def data_diagnostics(df, name):
    """基础诊断：缺失值检查 + 描述性统计"""
    print(f"\n{'='*70}")
    print(f"  【{name}】数据诊断报告")
    print(f"{'='*70}")
    print(f"  数据时间范围: {df['trade_date'].min().strftime('%Y-%m-%d')} ~ "
          f"{df['trade_date'].max().strftime('%Y-%m-%d')}")
    print(f"  总记录数: {len(df)} 条")

    # 缺失值检查
    print(f"\n  --- 缺失值检查 ---")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("  ✓ 所有字段无缺失值，数据完整")
    else:
        for col in df.columns:
            if missing[col] > 0:
                print(f"  ✗ {col}: 缺失 {missing[col]} 条 "
                      f"({missing[col]/len(df)*100:.1f}%)")

    # 描述性统计
    stat_cols = ['open', 'high', 'low', 'close', 'vol', 'amount', 'pct_chg']
    desc = df[stat_cols].describe()
    print(f"\n  --- 描述性统计 ---")
    print(f"  {'指标':<12} {'均值':>12} {'标准差':>12} {'最小值':>12} "
          f"{'最大值':>12} {'中位数':>12}")
    print(f"  {'-'*78}")
    col_names = {
        'open': '开盘价', 'high': '最高价', 'low': '最低价',
        'close': '收盘价', 'vol': '成交量', 'amount': '成交额',
        'pct_chg': '涨跌幅(%)'
    }
    for col in stat_cols:
        row = desc[col]
        print(f"  {col_names[col]:<12} {row['mean']:>12.2f} {row['std']:>12.2f} "
              f"{row['min']:>12.2f} {row['max']:>12.2f} {row['50%']:>12.2f}")

    return desc


# ============================================================
#  2. 技术指标计算
# ============================================================
def calc_rsi(close, period=14):
    """
    RSI（相对强弱指数）
    RS = n日平均涨幅 / n日平均跌幅
    RSI = 100 - 100/(1+RS)
    使用 Wilder 平滑法
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder 平滑法：首值用简单平均，后续用指数平滑
    avg_gain = pd.Series(index=close.index, dtype=float)
    avg_loss = pd.Series(index=close.index, dtype=float)

    avg_gain.iloc[period] = gain.iloc[1:period+1].mean()
    avg_loss.iloc[period] = loss.iloc[1:period+1].mean()

    for i in range(period+1, len(close)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi.iloc[:period] = np.nan
    return rsi


def calc_macd(close, fast=12, slow=26, signal=9):
    """
    MACD（指数平滑异同移动平均线）
    DIF = EMA(fast) - EMA(slow)
    DEA = EMA(DIF, signal)
    MACD柱 = 2 * (DIF - DEA)
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = 2 * (dif - dea)  # 国内常用 2 倍
    return dif, dea, hist


def calc_bollinger(close, window=20, num_std=2):
    """
    布林带（Bollinger Bands）
    中轨 = MA(close, window)
    上轨 = 中轨 + num_std * std
    下轨 = 中轨 - num_std * std
    带宽 = (上轨 - 下轨) / 中轨
    """
    ma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    bandwidth = (upper - lower) / ma * 100
    return ma, upper, lower, bandwidth


def calc_kdj(high, low, close, n=9, m1=3, m2=3):
    """
    KDJ 随机指标
    RSV = (close - lowest_low(n)) / (highest_high(n) - lowest_low(n)) * 100
    K = SMA(RSV, m1)
    D = SMA(K, m2)
    J = 3*K - 2*D
    """
    lowest_low = low.rolling(window=n).min()
    highest_high = high.rolling(window=n).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    rsv = rsv.fillna(50)

    k = pd.Series(index=close.index, dtype=float)
    d = pd.Series(index=close.index, dtype=float)
    k.iloc[0] = 50
    d.iloc[0] = 50

    for i in range(1, len(close)):
        if np.isnan(rsv.iloc[i]):
            k.iloc[i] = k.iloc[i-1]
            d.iloc[i] = d.iloc[i-1]
        else:
            k.iloc[i] = (m1 - 1) / m1 * k.iloc[i-1] + 1 / m1 * rsv.iloc[i]
            d.iloc[i] = (m2 - 1) / m2 * d.iloc[i-1] + 1 / m2 * k.iloc[i]

    j = 3 * k - 2 * d
    return k, d, j


# ============================================================
#  3. 可视化绘制
# ============================================================
def plot_price_with_boll(df, name, savepath):
    """绘制收盘价 + 布林带"""
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df['trade_date'], df['close'], color='#333333', linewidth=1.2,
            label='收盘价', zorder=3)
    ax.plot(df['trade_date'], df['BOLL_MA'], color='#2196F3', linewidth=1,
            label=f'BOLL中轨(MA{20})', alpha=0.8)
    ax.plot(df['trade_date'], df['BOLL_Upper'], color='#F44336', linewidth=1,
            linestyle='--', label='BOLL上轨(+2σ)', alpha=0.7)
    ax.plot(df['trade_date'], df['BOLL_Lower'], color='#4CAF50', linewidth=1,
            linestyle='--', label='BOLL下轨(-2σ)', alpha=0.7)
    ax.fill_between(df['trade_date'], df['BOLL_Upper'], df['BOLL_Lower'],
                    color='#90CAF9', alpha=0.12)

    ax.set_title(f'{name} — 收盘价与布林带(Bollinger Bands)', fontsize=14, fontweight='bold')
    ax.set_ylabel('价格(元)', fontsize=11)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches='tight')
    plt.close()
    print(f"  ✓ 布林带图已保存: {savepath.name}")


def plot_rsi(df, name, savepath):
    """绘制 RSI 指标"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), height_ratios=[2, 1],
                                    sharex=True,
                                    gridspec_kw={'hspace': 0.08})

    # 上图：收盘价
    ax1.plot(df['trade_date'], df['close'], color='#333333', linewidth=1.2)
    ax1.set_ylabel('收盘价(元)', fontsize=11)
    ax1.set_title(f'{name} — RSI(14) 相对强弱指数', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 下图：RSI
    ax2.plot(df['trade_date'], df['RSI'], color='#7B1FA2', linewidth=1.2, label='RSI(14)')
    ax2.axhline(70, color='#F44336', linewidth=0.8, linestyle='--', alpha=0.7)
    ax2.axhline(30, color='#4CAF50', linewidth=0.8, linestyle='--', alpha=0.7)
    ax2.axhline(50, color='#999999', linewidth=0.5, linestyle=':', alpha=0.5)
    ax2.fill_between(df['trade_date'], 70, 100, color='#FFCDD2', alpha=0.3)
    ax2.fill_between(df['trade_date'], 0, 30, color='#C8E6C9', alpha=0.3)
    ax2.text(df['trade_date'].iloc[5], 72, '超买区(>70)', fontsize=8, color='#D32F2F')
    ax2.text(df['trade_date'].iloc[5], 26, '超卖区(<30)', fontsize=8, color='#388E3C')
    ax2.set_ylabel('RSI', fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches='tight')
    plt.close()
    print(f"  ✓ RSI图已保存: {savepath.name}")


def plot_macd(df, name, savepath):
    """绘制 MACD 指标"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), height_ratios=[2, 1.5],
                                    sharex=True,
                                    gridspec_kw={'hspace': 0.08})

    # 上图：收盘价
    ax1.plot(df['trade_date'], df['close'], color='#333333', linewidth=1.2)
    ax1.set_ylabel('收盘价(元)', fontsize=11)
    ax1.set_title(f'{name} — MACD(12,26,9) 指数平滑异同移动平均线',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 下图：MACD
    # 柱状图
    colors = ['#F44336' if v >= 0 else '#4CAF50' for v in df['MACD_Hist']]
    ax2.bar(df['trade_date'], df['MACD_Hist'], color=colors, width=1.2, alpha=0.6,
            label='MACD柱')
    # DIF 线
    ax2.plot(df['trade_date'], df['MACD_DIF'], color='#1976D2', linewidth=1.2,
             label='DIF')
    # DEA 线
    ax2.plot(df['trade_date'], df['MACD_DEA'], color='#FF9800', linewidth=1.2,
             label='DEA')
    ax2.axhline(0, color='#666666', linewidth=0.6)

    ax2.set_ylabel('MACD', fontsize=11)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches='tight')
    plt.close()
    print(f"  ✓ MACD图已保存: {savepath.name}")


def plot_kdj(df, name, savepath):
    """绘制 KDJ 指标（扩展指标）"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), height_ratios=[2, 1.5],
                                    sharex=True,
                                    gridspec_kw={'hspace': 0.08})

    # 上图：收盘价
    ax1.plot(df['trade_date'], df['close'], color='#333333', linewidth=1.2)
    ax1.set_ylabel('收盘价(元)', fontsize=11)
    ax1.set_title(f'{name} — KDJ(9,3,3) 随机指标', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 下图：KDJ
    ax2.plot(df['trade_date'], df['K'], color='#1976D2', linewidth=1.2, label='K')
    ax2.plot(df['trade_date'], df['D'], color='#FF9800', linewidth=1.2, label='D')
    ax2.plot(df['trade_date'], df['J'], color='#7B1FA2', linewidth=1, label='J', alpha=0.8)
    ax2.axhline(80, color='#F44336', linewidth=0.8, linestyle='--', alpha=0.6)
    ax2.axhline(20, color='#4CAF50', linewidth=0.8, linestyle='--', alpha=0.6)
    ax2.fill_between(df['trade_date'], 80, 120, color='#FFCDD2', alpha=0.2)
    ax2.fill_between(df['trade_date'], -20, 20, color='#C8E6C9', alpha=0.2)
    ax2.text(df['trade_date'].iloc[5], 82, '超买(>80)', fontsize=8, color='#D32F2F')
    ax2.text(df['trade_date'].iloc[5], 16, '超卖(<20)', fontsize=8, color='#388E3C')
    ax2.set_ylabel('KDJ', fontsize=11)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches='tight')
    plt.close()
    print(f"  ✓ KDJ图已保存: {savepath.name}")


def plot_all_indicators(df, name, savepath):
    """将所有指标汇总在一张综合图中"""
    fig, axes = plt.subplots(5, 1, figsize=(14, 16),
                              height_ratios=[2.5, 1.5, 1.5, 1.5, 1.5],
                              sharex=True,
                              gridspec_kw={'hspace': 0.12})

    dates = df['trade_date']

    # 1. 价格 + 布林带
    ax = axes[0]
    ax.plot(dates, df['close'], color='#333333', linewidth=1.2, label='收盘价', zorder=3)
    ax.plot(dates, df['BOLL_MA'], color='#2196F3', linewidth=1, label='BOLL中轨', alpha=0.8)
    ax.plot(dates, df['BOLL_Upper'], color='#F44336', linewidth=0.8, linestyle='--', alpha=0.6)
    ax.plot(dates, df['BOLL_Lower'], color='#4CAF50', linewidth=0.8, linestyle='--', alpha=0.6)
    ax.fill_between(dates, df['BOLL_Upper'], df['BOLL_Lower'], color='#90CAF9', alpha=0.1)
    ax.set_ylabel('价格(元)', fontsize=10)
    ax.set_title(f'{name} — 技术指标综合视图', fontsize=15, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8, ncol=4)
    ax.grid(True, alpha=0.3)

    # 2. RSI
    ax = axes[1]
    ax.plot(dates, df['RSI'], color='#7B1FA2', linewidth=1.2)
    ax.axhline(70, color='#F44336', linewidth=0.6, linestyle='--', alpha=0.6)
    ax.axhline(30, color='#4CAF50', linewidth=0.6, linestyle='--', alpha=0.6)
    ax.fill_between(dates, 70, 100, color='#FFCDD2', alpha=0.2)
    ax.fill_between(dates, 0, 30, color='#C8E6C9', alpha=0.2)
    ax.set_ylabel('RSI(14)', fontsize=10)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)

    # 3. MACD
    ax = axes[2]
    colors = ['#F44336' if v >= 0 else '#4CAF50' for v in df['MACD_Hist']]
    ax.bar(dates, df['MACD_Hist'], color=colors, width=1.2, alpha=0.5)
    ax.plot(dates, df['MACD_DIF'], color='#1976D2', linewidth=1, label='DIF')
    ax.plot(dates, df['MACD_DEA'], color='#FF9800', linewidth=1, label='DEA')
    ax.axhline(0, color='#666666', linewidth=0.5)
    ax.set_ylabel('MACD', fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 4. KDJ
    ax = axes[3]
    ax.plot(dates, df['K'], color='#1976D2', linewidth=1, label='K')
    ax.plot(dates, df['D'], color='#FF9800', linewidth=1, label='D')
    ax.plot(dates, df['J'], color='#7B1FA2', linewidth=0.8, label='J', alpha=0.7)
    ax.axhline(80, color='#F44336', linewidth=0.5, linestyle='--', alpha=0.5)
    ax.axhline(20, color='#4CAF50', linewidth=0.5, linestyle='--', alpha=0.5)
    ax.set_ylabel('KDJ', fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 5. 成交量
    ax = axes[4]
    vol_colors = ['#F44336' if df['pct_chg'].iloc[i] >= 0 else '#4CAF50'
                  for i in range(len(df))]
    ax.bar(dates, df['vol'], color=vol_colors, width=1.2, alpha=0.6)
    ax.set_ylabel('成交量(手)', fontsize=10)
    ax.set_xlabel('日期', fontsize=11)
    ax.grid(True, alpha=0.3)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(savepath, bbox_inches='tight')
    plt.close()
    print(f"  ✓ 综合指标图已保存: {savepath.name}")


# ============================================================
#  主程序
# ============================================================
def main():
    all_results = {}

    for name, filepath in FILES.items():
        print(f"\n{'#'*70}")
        print(f"#  正在处理: {name} ({filepath.name})")
        print(f"{'#'*70}")

        # 1. 加载数据
        df = load_data(filepath)
        print(f"  数据加载完成: {len(df)} 条记录")

        # 2. 数据诊断
        desc = data_diagnostics(df, name)

        # 3. 计算技术指标
        print(f"\n  --- 技术指标计算 ---")
        df['RSI'] = calc_rsi(df['close'], period=14)
        df['MACD_DIF'], df['MACD_DEA'], df['MACD_Hist'] = calc_macd(df['close'])
        df['BOLL_MA'], df['BOLL_Upper'], df['BOLL_Lower'], df['BOLL_BW'] = \
            calc_bollinger(df['close'], window=20, num_std=2)
        df['K'], df['D'], df['J'] = calc_kdj(df['high'], df['low'], df['close'])
        print("  ✓ RSI(14)、MACD(12,26,9)、BOLL(20,2)、KDJ(9,3,3) 计算完成")

        # 输出最新5日指标值
        print(f"\n  --- 最近5个交易日指标值 ---")
        latest = df[['trade_date', 'close', 'RSI', 'MACD_DIF',
                     'MACD_DEA', 'MACD_Hist', 'BOLL_Upper', 'BOLL_Lower',
                     'K', 'D', 'J']].tail(5)
        for _, row in latest.iterrows():
            print(f"  {row['trade_date'].strftime('%Y-%m-%d')} | "
                  f"收盘:{row['close']:.2f} | RSI:{row['RSI']:.1f} | "
                  f"DIF:{row['MACD_DIF']:.4f} DEA:{row['MACD_DEA']:.4f} | "
                  f"BOLL:[{row['BOLL_Lower']:.2f}, {row['BOLL_Upper']:.2f}] | "
                  f"K:{row['K']:.1f} D:{row['D']:.1f} J:{row['J']:.1f}")

        # 4. 可视化
        print(f"\n  --- 可视化绘图 ---")
        plot_price_with_boll(df, name, BASE_DIR / f'{name}_布林带.png')
        plot_rsi(df, name, BASE_DIR / f'{name}_RSI.png')
        plot_macd(df, name, BASE_DIR / f'{name}_MACD.png')
        plot_kdj(df, name, BASE_DIR / f'{name}_KDJ.png')
        plot_all_indicators(df, name, BASE_DIR / f'{name}_综合指标图.png')

        all_results[name] = df

    # 保存带指标的完整数据
    for name, df in all_results.items():
        outpath = BASE_DIR / f'{name}_含技术指标.csv'
        df.to_csv(outpath, index=False, encoding='utf-8-sig')
        print(f"\n  ✓ {name} 带指标数据已保存: {outpath.name}")

    print(f"\n{'='*70}")
    print("  全部分析完成！")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
