import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 中芯国际 (688981.SH) 行情数据获取与可视化\n",
    "\n",
    "本 Notebook 演示从 Tushare 获取中芯国际近一年日线行情数据，并进行 K线图和成交量可视化分析。\n",
    "\n",
    "**流程**：数据获取 → 数据清洗 → 统计概览 → K线图 → 交互式图表 → 成交量分析"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. 导入依赖库"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import requests\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import mplfinance as mpf\n",
    "import plotly.graph_objects as go\n",
    "from plotly.subplots import make_subplots\n",
    "from datetime import datetime, timedelta\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "# 中文显示\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib as mpl\n",
    "mpl.rcParams['font.family'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti TC', 'sans-serif']\n",
    "mpl.rcParams['axes.unicode_minus'] = False\n",
    "\n",
    "print('依赖库加载完成')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. 从 Tushare 获取数据\n",
    "\n",
    "通过 Tushare Pro HTTP API 直接获取中芯国际 (688981.SH) 近一年日线行情。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Tushare API 配置\n",
    "API_URL = 'https://api.tushare.pro'\n",
    "TOKEN = 'e3a2cfe468c90953359a183127273ad04175da9de57308f61a1ca703'\n",
    "\n",
    "# 中芯国际 A股代码\n",
    "ts_code = '688981.SH'\n",
    "end_date = datetime.now().strftime('%Y%m%d')\n",
    "start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')\n",
    "\n",
    "print(f'股票代码: {ts_code}')\n",
    "print(f'数据区间: {start_date} ~ {end_date}')\n",
    "\n",
    "# 调用 Tushare daily 接口\n",
    "payload = {\n",
    "    'api_name': 'daily',\n",
    "    'token': TOKEN,\n",
    "    'params': {\n",
    "        'ts_code': ts_code,\n",
    "        'start_date': start_date,\n",
    "        'end_date': end_date\n",
    "    },\n",
    "    'fields': 'ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'\n",
    "}\n",
    "\n",
    "resp = requests.post(API_URL, json=payload, timeout=30)\n",
    "result = resp.json()\n",
    "\n",
    "if result.get('code') != 0:\n",
    "    raise Exception(f\"API错误: {result}\")\n",
    "\n",
    "data = result['data']\n",
    "df = pd.DataFrame(data['items'], columns=data['fields'])\n",
    "print(f'\\n成功获取 {len(df)} 条日线数据')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. 数据清洗与预处理"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 数值类型转换\n",
    "num_cols = ['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']\n",
    "for col in num_cols:\n",
    "    df[col] = pd.to_numeric(df[col], errors='coerce')\n",
    "\n",
    "# 日期格式转换 YYYYMMDD -> datetime\n",
    "df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')\n",
    "\n",
    "# 按日期升序排列\n",
    "df = df.sort_values('trade_date').reset_index(drop=True)\n",
    "\n",
    "# 设为索引（mplfinance 要求 DatetimeIndex）\n",
    "df.set_index('trade_date', inplace=True)\n",
    "\n",
    "print(f'数据范围: {df.index[0].strftime(\"%Y-%m-%d\")} 至 {df.index[-1].strftime(\"%Y-%m-%d\")}')\n",
    "print(f'交易日数: {len(df)} 天')\n",
    "print(f'\\n字段列表: {list(df.columns)}')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 查看前10行\n",
    "df.head(10)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 查看后10行\n",
    "df.tail(10)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. 数据统计概览"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 基本统计信息\n",
    "df[['open', 'high', 'low', 'close', 'vol', 'amount']].describe().round(2)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 关键指标\n",
    "latest = df.iloc[-1]\n",
    "first = df.iloc[0]\n",
    "year_high = df['high'].max()\n",
    "year_low = df['low'].min()\n",
    "total_return = ((latest['close'] - first['close']) / first['close']) * 100\n",
    "avg_vol = df['vol'].mean()\n",
    "\n",
    "print('='*50)\n",
    "print(f'  中芯国际 ({ts_code}) 行情概览')\n",
    "print('='*50)\n",
    "print(f'  最新收盘价: ¥{latest[\"close\"]:.2f}')\n",
    "print(f'  当日涨跌幅: {latest[\"pct_chg\"]:+.2f}%')\n",
    "print(f'  近一年涨跌: {total_return:+.2f}%')\n",
    "print(f'  起始价 → 终价: ¥{first[\"close\"]:.2f} → ¥{latest[\"close\"]:.2f}')\n",
    "print(f'  一年最高价: ¥{year_high:.2f}')\n",
    "print(f'  一年最低价: ¥{year_low:.2f}')\n",
    "print(f'  日均成交量: {avg_vol/10000:.1f} 万手')\n",
    "print(f'  最新成交额: ¥{latest[\"amount\"]/100000:.2f} 亿元')\n",
    "print('='*50)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 5. K线图（mplfinance 静态版）\n",
    "\n",
    "使用 mplfinance 绘制蜡烛图，**涨红跌绿**（中国股市配色），叠加 MA5/MA10/MA20 均线。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# mplfinance 要求列名为 Open/High/Low/Close/Volume\n",
    "df_mpf = df[['open', 'high', 'low', 'close', 'vol']].copy()\n",
    "df_mpf.columns = ['Open', 'High', 'Low', 'Close', 'Volume']\n",
    "\n",
    "# 自定义配色：涨红跌绿\n",
    "mc = mpf.make_marketcolors(\n",
    "    up='#ef232a', down='#14b143',\n",
    "    edge={'up': '#ef232a', 'down': '#14b143'},\n",
    "    wick={'up': '#ef232a', 'down': '#14b143'},\n",
    "    volume={'up': '#ef232a', 'down': '#14b143'}\n",
    ")\n",
    "s = mpf.make_mpf_style(\n",
    "    marketcolors=mc,\n",
    "    gridstyle='--',\n",
    "    gridcolor='#e0e0e0',\n",
    "    figcolor='white',\n",
    "    facecolor='white'\n",
    ")\n",
    "\n",
    "# 绘制K线图 + 成交量\n",
    "fig, axes = mpf.plot(\n",
    "    df_mpf,\n",
    "    type='candle',\n",
    "    style=s,\n",
    "    title='\\u4e2d\\u82af\\u56fd\\u9645 (688981.SH) \\u65e5K\\u7ebf\\u56fe',\n",
    "    ylabel='\\u4ef7\\u683c (\\u5143)',\n",
    "    ylabel_lower='\\u6210\\u4ea4\\u91cf (\\u624b)',\n",
    "    volume=True,\n",
    "    mav=(5, 10, 20),\n",
    "    figsize=(16, 10),\n",
    "    returnfig=True\n",
    ")\n",
    "\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 6. 交互式 K线图（Plotly 版）\n",
    "\n",
    "使用 Plotly 生成交互式 K线图，支持缩放、悬停查看详情。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 计算均线\n",
    "df['MA5'] = df['close'].rolling(5).mean()\n",
    "df['MA10'] = df['close'].rolling(10).mean()\n",
    "df['MA20'] = df['close'].rolling(20).mean()\n",
    "df['MA60'] = df['close'].rolling(60).mean()\n",
    "\n",
    "# 判断涨跌颜色\n",
    "colors = ['#ef232a' if c >= o else '#14b143' for o, c in zip(df['open'], df['close'])]\n",
    "\n",
    "fig = make_subplots(\n",
    "    rows=2, cols=1, shared_xaxes=True,\n",
    "    vertical_spacing=0.03,\n",
    "    row_width=[0.3, 0.7],\n",
    "    subplot_titles=('K\\u7ebf\\u56fe', '\\u6210\\u4ea4\\u91cf')\n",
    ")\n",
    "\n",
    "# K线\n",
    "fig.add_trace(go.Candlestick(\n",
    "    x=df.index,\n",
    "    open=df['open'], high=df['high'],\n",
    "    low=df['low'], close=df['close'],\n",
    "    increasing_line_color='#ef232a',\n",
    "    decreasing_line_color='#14b143',\n",
    "    name='K线'\n",
    "), row=1, col=1)\n",
    "\n",
    "# 均线\n",
    "for ma_name, ma_color in [('MA5', '#f5a623'), ('MA10', '#0984e3'), ('MA20', '#a55eea'), ('MA60', '#26de81')]:\n",
    "    fig.add_trace(go.Scatter(\n",
    "        x=df.index, y=df[ma_name],\n",
    "        mode='lines', name=ma_name,\n",
    "        line=dict(color=ma_color, width=1.5)\n",
    "    ), row=1, col=1)\n",
    "\n",
    "# 成交量\n",
    "fig.add_trace(go.Bar(\n",
    "    x=df.index, y=df['vol'],\n",
    "    marker_color=colors,\n",
    "    name='成交量',\n",
    "    showlegend=False\n",
    "), row=2, col=1)\n",
    "\n",
    "fig.update_layout(\n",
    "    title='中芯国际 (688981.SH) 交互式K线图',\n",
    "    xaxis_rangeslider_visible=False,\n",
    "    template='plotly_white',\n",
    "    height=700,\n",
    "    font=dict(family='Arial Unicode MS', size=12),\n",
    "    yaxis=dict(title='价格 (元)'),\n",
    "    yaxis2=dict(title='成交量 (手)'),\n",
    "    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)\n",
    ")\n",
    "\n",
    "fig.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 7. 成交量分析"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))\n",
    "\n",
    "# 成交量柱状图\n",
    "colors_vol = ['#ef232a' if c >= o else '#14b143' for o, c in zip(df['open'], df['close'])]\n",
    "ax1.bar(df.index, df['vol']/10000, color=colors_vol, width=0.8, alpha=0.8)\n",
    "ax1.axhline(y=df['vol'].mean()/10000, color='#0984e3', linestyle='--', linewidth=1, label=f'日均成交量: {df[\"vol\"].mean()/10000:.0f}万手')\n",
    "ax1.set_title('中芯国际 近一年日成交量', fontsize=14, fontweight='bold')\n",
    "ax1.set_ylabel('成交量 (万手)', fontsize=12)\n",
    "ax1.legend(fontsize=11)\n",
    "ax1.grid(True, alpha=0.3)\n",
    "\n",
    "# 成交额柱状图\n",
    "colors_amt = ['#ef232a' if c >= o else '#14b143' for o, c in zip(df['open'], df['close'])]\n",
    "ax2.bar(df.index, df['amount']/100000, color=colors_amt, width=0.8, alpha=0.8)\n",
    "ax2.axhline(y=df['amount'].mean()/100000, color='#0984e3', linestyle='--', linewidth=1, label=f'日均成交额: {df[\"amount\"].mean()/100000:.2f}亿元')\n",
    "ax2.set_title('中芯国际 近一年日成交额', fontsize=14, fontweight='bold')\n",
    "ax2.set_ylabel('成交额 (亿元)', fontsize=12)\n",
    "ax2.set_xlabel('日期', fontsize=12)\n",
    "ax2.legend(fontsize=11)\n",
    "ax2.grid(True, alpha=0.3)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 8. 涨跌幅分布分析"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))\n",
    "\n",
    "# 涨跌幅直方图\n",
    "ax1.hist(df['pct_chg'], bins=40, color='#0984e3', edgecolor='white', alpha=0.7)\n",
    "ax1.axvline(x=0, color='#2d3436', linestyle='-', linewidth=1)\n",
    "ax1.axvline(x=df['pct_chg'].mean(), color='#ef232a', linestyle='--', linewidth=1.5, label=f'均值: {df[\"pct_chg\"].mean():.2f}%')\n",
    "ax1.set_title('日涨跌幅分布', fontsize=14, fontweight='bold')\n",
    "ax1.set_xlabel('涨跌幅 (%)', fontsize=12)\n",
    "ax1.set_ylabel('频次', fontsize=12)\n",
    "ax1.legend(fontsize=11)\n",
    "ax1.grid(True, alpha=0.3)\n",
    "\n",
    "# 累计涨跌幅\n",
    "cum_return = ((1 + df['pct_chg']/100).cumprod() - 1) * 100\n",
    "ax2.fill_between(df.index, 0, cum_return, where=cum_return>=0, color='#ef232a', alpha=0.3, label='正收益')\n",
    "ax2.fill_between(df.index, 0, cum_return, where=cum_return<0, color='#14b143', alpha=0.3, label='负收益')\n",
    "ax2.plot(df.index, cum_return, color='#2d3436', linewidth=1.5)\n",
    "ax2.axhline(y=0, color='#2d3436', linestyle='-', linewidth=0.8)\n",
    "ax2.set_title('累计涨跌幅走势', fontsize=14, fontweight='bold')\n",
    "ax2.set_ylabel('累计涨跌幅 (%)', fontsize=12)\n",
    "ax2.legend(fontsize=11)\n",
    "ax2.grid(True, alpha=0.3)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f'累计涨跌幅: {cum_return.iloc[-1]:+.2f}%')\n",
    "print(f'最大日涨幅: {df[\"pct_chg\"].max():+.2f}% ({df[\"pct_chg\"].idxmax().strftime(\"%Y-%m-%d\")})')\n",
    "print(f'最大日跌幅: {df[\"pct_chg\"].min():+.2f}% ({df[\"pct_chg\"].idxmin().strftime(\"%Y-%m-%d\")})')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 9. 保存数据到本地"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 重置索引便于保存\n",
    "df_save = df.reset_index()\n",
    "df_save['trade_date'] = df_save['trade_date'].dt.strftime('%Y%m%d')\n",
    "\n",
    "# 保存 CSV\n",
    "csv_path = '中芯国际_688981_日线数据.csv'\n",
    "df_save.to_csv(csv_path, index=False, encoding='utf-8-sig')\n",
    "print(f'CSV 已保存: {csv_path}')\n",
    "\n",
    "# 保存 JSON\n",
    "json_path = '中芯国际_688981_日线数据.json'\n",
    "df_save.to_json(json_path, orient='records', force_ascii=False, indent=2)\n",
    "print(f'JSON 已保存: {json_path}')\n",
    "\n",
    "print(f'\\n共 {len(df_save)} 条记录, 字段: {list(df_save.columns)}')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "---\n",
    "\n",
    "### 说明\n",
    "\n",
    "- **数据来源**: Tushare Pro (https://tushare.pro)\n",
    "- **配色规则**: 涨红跌绿（中国股市惯例）\n",
    "- **均线**: MA5(橙) / MA10(蓝) / MA20(紫) / MA60(绿)\n",
    "- 本 Notebook 仅供学习参考，不构成投资建议"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

output_path = "/Users/liutt/Documents/AI 2026/Workbuddy/BI工作坊-ai量化公益课/中芯国际_行情分析.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"Notebook 已生成: {output_path}")
