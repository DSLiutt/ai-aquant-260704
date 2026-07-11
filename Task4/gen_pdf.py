"""
海龟交易策略分析报告 PDF 生成器
================================
使用 matplotlib PdfPages 生成多页PDF报告
包含9只股票（含太空概念股）的完整回测分析
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.dates as mdates

# 中文字体
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "PingFang SC"]
plt.rcParams["axes.unicode_minus"] = False

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(DATA_DIR, "charts")
OUTPUT_PDF = os.path.join(DATA_DIR, "海龟交易策略分析报告.pdf")

# 加载数据
with open(os.path.join(DATA_DIR, "strategy_summary.json"), "r", encoding="utf-8") as f:
    summary = json.load(f)
batch_df = pd.read_csv(os.path.join(DATA_DIR, "海龟策略回测结果.csv"), encoding="utf-8-sig")

# 配色
C_PRIMARY = "#2C3E50"
C_ACCENT = "#8E44AD"
C_UP = "#E74C3C"       # 涨-红
C_DOWN = "#27AE60"     # 跌-绿
C_BLUE = "#3498DB"
C_ORANGE = "#F39C12"
C_GRAY = "#95A5A6"
C_LIGHT = "#ECF0F1"
C_BG = "#FAFBFC"

STOCK_ORDER = [
    "贵州茅台", "比亚迪", "宁德时代", "中芯国际",
    "三一重工", "平安集团", "中国卫星", "航天电子", "航天动力"
]

ALL_STOCKS = [s for s in STOCK_ORDER if s in summary]


def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    return f"{v*100:.2f}%"


def fmt_num(v, d=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    return f"{v:.{d}f}"


def add_text_box(ax, x, y, text, fontsize=9, color="#2C3E50", bg=None, weight="normal", ha="left", va="top"):
    """在指定位置添加文本框"""
    bbox = None
    if bg:
        bbox = dict(boxstyle="round,pad=0.4", facecolor=bg, edgecolor="none", alpha=0.9)
    ax.text(x, y, text, fontsize=fontsize, color=color, fontweight=weight,
            ha=ha, va=va, transform=ax.transAxes, bbox=bbox, wrap=True,
            linespacing=1.6)


def add_section_title(ax, num, title):
    """添加章节标题"""
    ax.axis("off")
    # 左侧数字圆
    circle = plt.Circle((0.04, 0.88), 0.025, color=C_ACCENT, transform=ax.transAxes)
    ax.add_patch(circle)
    ax.text(0.04, 0.88, str(num), fontsize=16, color="white", fontweight="bold",
            ha="center", va="center", transform=ax.transAxes)
    ax.text(0.08, 0.88, title, fontsize=18, color=C_PRIMARY, fontweight="bold",
            ha="left", va="center", transform=ax.transAxes)
    # 下划线
    ax.plot([0.03, 0.97], [0.83, 0.83], color=C_ACCENT, linewidth=2, transform=ax.transAxes)


# ================================================================
# 页面1：封面
# ================================================================
def page_cover(pdf):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(C_PRIMARY)

    # 顶部装饰
    ax.add_patch(plt.Rectangle((0, 0.85), 1, 0.15, color=C_ACCENT, alpha=0.3))
    ax.add_patch(plt.Rectangle((0, 0.83), 1, 0.02, color=C_ACCENT))

    # 标题
    ax.text(0.5, 0.72, "复刻传奇", fontsize=42, color="white", fontweight="bold",
            ha="center", va="center")
    ax.text(0.5, 0.64, "海龟交易法则实战演练", fontsize=28, color="white",
            ha="center", va="center")

    # 分隔线
    ax.plot([0.2, 0.8], [0.56, 0.56], color=C_ACCENT, linewidth=2)

    # 副标题
    ax.text(0.5, 0.50, "BI工作坊 · AI量化交易公益课 · Task4", fontsize=14,
            color="#BDC3C7", ha="center", va="center")
    ax.text(0.5, 0.45, "海龟策略 Python 实现 · 9只股票回测 · 参数敏感性分析", fontsize=12,
            color="#95A5A6", ha="center", va="center")

    # 核心指标摘要
    ax.text(0.5, 0.37, "—— 报告摘要 ——", fontsize=13, color=C_ORANGE,
            ha="center", va="center", fontweight="bold")

    summary_items = [
        "策略引擎: 唐奇安通道 + ATR + 动态止损",
        "回测标的: 9只A股 (含3只太空概念股)",
        "参数组合: 5组参数 × 9只股票 = 45次回测",
        "可视化图表: 48张 (通道/ATR/信号/净值/回撤)",
        "量化指标: MDD / Sharpe / 累计回报 / 胜率",
    ]
    for i, item in enumerate(summary_items):
        ax.text(0.5, 0.32 - i * 0.035, item, fontsize=10, color="#BDC3C7",
                ha="center", va="center")

    # 底部
    ax.add_patch(plt.Rectangle((0, 0), 1, 0.06, color=C_ACCENT, alpha=0.3))
    ax.text(0.5, 0.03, "初始资金 ¥100,000 | 数据区间 2024-2026 | 经典参数 20/10/20/2.0",
            fontsize=9, color="#95A5A6", ha="center", va="center")

    fig.tight_layout(pad=0)
    pdf.savefig(fig, facecolor=fig.get_facecolor())
    plt.close()


# ================================================================
# 页面2：策略概述
# ================================================================
def page_overview(pdf):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_section_title(ax, 1, "海龟交易策略概述")

    # 历史背景
    add_text_box(ax, 0.05, 0.78, "1.1 历史背景", fontsize=13, color=C_ACCENT, weight="bold")
    bg_text = (
        "1983年，美国著名交易员理查德·丹尼斯（Richard Dennis）与威廉·埃克哈特打赌：\n"
        "伟大的交易员是天生还是后天培养的？丹尼斯坚信交易可以被系统化教授，\n"
        "于是招募了一批学员，称之为「海龟」。他用一套完全机械化的交易系统\n"
        "培训这些学员，在随后的4年中，海龟们累计盈利超过1亿美元，\n"
        "创造了华尔街交易史上的传奇。"
    )
    add_text_box(ax, 0.05, 0.75, bg_text, fontsize=9, color=C_PRIMARY, bg=C_LIGHT)

    # 核心思想
    add_text_box(ax, 0.05, 0.62, "1.2 核心思想：趋势跟踪 + 突破入场 + 严格风控", fontsize=13, color=C_ACCENT, weight="bold")

    concepts = [
        ("趋势跟踪", "不预测市场方向，等待价格突破历史高低点后顺势入场。\n大趋势一旦形成，往往持续较长时间。"),
        ("突破入场", "使用唐奇安通道（Donchian Channel）作为入场信号。\n价格突破过去N日最高价时买入。"),
        ("波动率自适应", "通过ATR动态衡量市场波动率，止损距离和仓位大小\n随波动率自动调整。"),
        ("严格风控", "每笔交易风险不超过总资金的2%，止损设在入场价-2×ATR处。\n亏损时果断离场。"),
    ]

    for i, (title, desc) in enumerate(concepts):
        y = 0.58 - i * 0.07
        add_text_box(ax, 0.07, y, f"  {title}", fontsize=10, color=C_ACCENT, weight="bold", bg="#F5EEF8")
        add_text_box(ax, 0.22, y, desc, fontsize=8, color=C_PRIMARY)

    # 关键优势
    add_text_box(ax, 0.05, 0.28, "1.3 关键优势", fontsize=13, color=C_ACCENT, weight="bold")

    advantages = [
        "① 系统化交易，克服人性弱点 — 规则明确，不依赖主观判断",
        "② 趋势捕获能力强 — 突破入场确保大趋势启动时第一时间进场",
        "③ 动态风险控制 — ATR随波动率自动调节止损和仓位",
        "④ 明确的资金管理 — 每笔2%最大风险 + 最多4单位金字塔加仓",
        "⑤ 可量化、可回测 — 适合Python编程实现和历史数据验证",
        "⑥ 跨市场适用性 — 商品期货、股票、外汇、加密货币均可应用",
    ]
    for i, adv in enumerate(advantages):
        add_text_box(ax, 0.07, 0.24 - i * 0.035, adv, fontsize=8.5, color=C_PRIMARY, bg=C_BG)

    fig.tight_layout(pad=1)
    pdf.savefig(fig)
    plt.close()


# ================================================================
# 页面3：核心概念
# ================================================================
def page_concepts(pdf):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_section_title(ax, 2, "核心概念详解")

    # 2.1 唐奇安通道
    add_text_box(ax, 0.05, 0.78, "2.1 高低点通道（唐奇安通道 Donchian Channel）", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.74,
        "由Richard Donchian发明，计算过去N个交易日的最高价和最低价，形成动态价格通道。\n"
        "入场通道（20日）：上轨 = max(high, 过去20日)  下轨 = min(low, 过去20日)\n"
        "离场通道（10日）：下轨 = min(low, 过去10日)\n"
        "核心精髓：慢进快出 — 入场用长周期过滤噪音，离场用短周期快速保住利润。",
        fontsize=8.5, color=C_PRIMARY, bg=C_LIGHT)

    # 2.2 ATR
    add_text_box(ax, 0.05, 0.60, "2.2 平均真实波幅（ATR, Average True Range）", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.56,
        "由Welles Wilder发明，衡量市场波动率。TR取三值最大值：\n"
        "  TR = max(当日最高-最低, |最高-前收|, |最低-前收|)\n"
        "  ATR = TR的N日移动平均（默认N=20）\n\n"
        "ATR在策略中的三大作用：\n"
        "  1. 动态止损：止损价 = 买入价 - 2×ATR（波动大则止损宽）\n"
        "  2. 仓位管理：头寸 = (资金×2%) / (ATR×合约乘数)（波动大则仓位小）\n"
        "  3. 金字塔加仓：每上涨0.5×ATR加仓一个单位，最多加仓4次",
        fontsize=8.5, color=C_PRIMARY, bg=C_LIGHT)

    # 2.3 止损条件
    add_text_box(ax, 0.05, 0.36, "2.3 止损条件", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.32,
        "核心原则：「任何一笔交易的风险绝不超过账户总额的2%」\n\n"
        "止损价计算：止损价 = 买入价 - 2 × ATR\n"
        "  例：买入价100元，ATR=5元 → 止损价 = 100 - 10 = 90元\n\n"
        "仓位大小计算：头寸 = (总资金 × 2%) / (ATR × 合约乘数)\n"
        "  确保从买入到止损的亏损恰好等于总资金的2%\n\n"
        "加仓后止损调整：每加仓一个单位，止损价上移0.5×ATR\n"
        "离场信号：价格跌破10日最低价时平仓（趋势结束的正常退出）",
        fontsize=8.5, color=C_PRIMARY, bg=C_LIGHT)

    # 哲学
    add_text_box(ax, 0.05, 0.08,
        "「有老交易员，也有大胆的交易员，但没有大胆的老交易员。」\n"
        "严格的止损是交易员长期生存的根本。2%风险限制意味着即使连续亏损20次，账户也只损失约33%。",
        fontsize=9, color=C_ORANGE, bg="#FEF9E7", weight="bold")

    fig.tight_layout(pad=1)
    pdf.savefig(fig)
    plt.close()


# ================================================================
# 页面4：Python实现
# ================================================================
def page_python(pdf):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_section_title(ax, 3, "Python 编程实现")

    add_text_box(ax, 0.05, 0.78,
        "完整实现包括6个步骤：数据加载 → 通道计算 → ATR计算 → 信号生成 → 可视化 → 回测评估",
        fontsize=9, color=C_PRIMARY)

    code_blocks = [
        ("① 加载股价数据", '''def load_stock_data(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["trade_date"] = pd.to_datetime(
        df["trade_date"].astype(str).str.replace("-",""),
        format="%Y%m%d")
    df = df.sort_values("trade_date").reset_index(drop=True)
    return df'''),

        ("② 计算唐奇安高低点通道", '''def calc_donchian_channel(df, entry_period=20, exit_period=10):
    df["upper_entry"] = df["high"].rolling(
        entry_period).max().shift(1)  # 20日最高价
    df["lower_entry"] = df["low"].rolling(
        entry_period).min().shift(1)  # 20日最低价
    df["lower_exit"] = df["low"].rolling(
        exit_period).min().shift(1)   # 10日最低价
    return df
# shift(1)排除当日数据，避免未来数据'''),

        ("③ 计算ATR（平均真实波幅）", '''def calc_atr(df, period=20):
    prev_close = df["close"].shift(1)
    tr1 = df["high"] - df["low"]               # 当日振幅
    tr2 = (df["high"] - prev_close).abs()      # 跳空高开
    tr3 = (df["low"] - prev_close).abs()       # 跳空低开
    df["TR"] = pd.concat([tr1, tr2, tr3],
                         axis=1).max(axis=1)
    df["ATR"] = df["TR"].rolling(period).mean()
    return df'''),

        ("④ 生成买卖交易信号", '''def generate_signals(df, stop_atr_mult=2.0):
    # 买入：收盘价突破20日最高价
    # 卖出：跌破10日最低价 或 触及2×ATR止损
    for i in range(len(df)):
        if current_pos == 0:
            if close > upper_entry:  # 突破买入
                signal = 1; stop = close - 2*ATR
        elif current_pos == 1:
            if close < lower_exit:   # 通道离场
                signal = -1
            elif close < stop_price: # 止损离场
                signal = -1'''),

        ("⑤⑥ 回测模拟 & 量化指标", '''def backtest(df, initial_capital=100000):
    # 逐日遍历，根据signal执行买卖
    # 同时计算买入持有基准
    return df, trade_df

def calc_metrics(df, initial_capital=100000):
    # 累计回报 = (最终市值 - 初始资金) / 初始资金
    # 最大回撤 MDD = min((净值-最高净值)/最高净值)
    # 夏普比率 = √252 × (日超额收益均值/标准差)
    # 年化收益 = (1+累计回报)^(252/交易日数) - 1
    return metrics'''),
    ]

    y = 0.74
    for title, code in code_blocks:
        add_text_box(ax, 0.05, y, title, fontsize=9, color=C_ACCENT, weight="bold")
        y -= 0.022
        ax.text(0.05, y, code, fontsize=6.5, color="#ECF0F1",
                fontfamily="Arial Unicode MS",
                ha="left", va="top", transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=C_PRIMARY, edgecolor="none"))
        # 估算代码块高度
        lines = code.count("\n") + 1
        y -= 0.018 * lines + 0.015

    fig.tight_layout(pad=1)
    pdf.savefig(fig)
    plt.close()


# ================================================================
# 页面5：多股票对比
# ================================================================
def page_comparison(pdf):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")

    # 标题
    ax_title = fig.add_axes([0.05, 0.92, 0.9, 0.06])
    ax_title.axis("off")
    add_section_title(ax_title, 4, "策略回测结果 — 多股票对比")

    # 说明文字
    ax_title.text(0.0, 0.0, "经典海龟参数（入场20日 / 离场10日 / ATR20日 / 止损2×ATR），初始资金10万元，9只A股回测",
                  fontsize=9, color=C_PRIMARY, ha="left", va="bottom", transform=ax_title.transAxes)

    # 多股票对比图
    img_path = os.path.join(CHARTS_DIR, "多股票对比.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.42, 0.9, 0.48])
        ax_img.imshow(img)
        ax_img.axis("off")

    # 对比表格
    ax_table = fig.add_axes([0.03, 0.05, 0.94, 0.34])
    ax_table.axis("off")

    classic = batch_df[batch_df["param"] == "入20/出10/ATR20/止2.0"].copy()
    if len(classic) == 0:
        classic = batch_df.head(9)

    # 按STOCK_ORDER排序
    classic["order"] = classic["stock"].map({s: i for i, s in enumerate(STOCK_ORDER)})
    classic = classic.sort_values("order").reset_index(drop=True)

    col_labels = ["股票", "策略\n回报", "买入持有\n回报", "策略\nMDD", "买入持有\nMDD", "策略\nSharpe", "买入持有\nSharpe", "胜率", "交易\n次数"]
    cell_data = []
    cell_colors = []
    for _, r in classic.iterrows():
        row = [
            r["stock"],
            fmt_pct(r["cumulative_return"]),
            fmt_pct(r["bh_cumulative_return"]),
            fmt_pct(r["max_drawdown"]),
            fmt_pct(r["bh_max_drawdown"]),
            fmt_num(r["sharpe_ratio"]),
            fmt_num(r["bh_sharpe_ratio"]),
            fmt_pct(r["win_rate"]),
            f"{int(r['buy_count'])}买{int(r['sell_count'])}卖",
        ]
        cell_data.append(row)

        # 行颜色
        colors = ["#FFFFFF"] * 9
        colors[1] = "#FADBD8" if r["cumulative_return"] >= 0 else "#D5F5E3"
        colors[2] = "#FADBD8" if r["bh_cumulative_return"] >= 0 else "#D5F5E3"
        colors[3] = "#D5F5E3"
        colors[4] = "#D5F5E3"
        colors[5] = "#FADBD8" if r["sharpe_ratio"] >= 0 else "#D5F5E3"
        colors[6] = "#FADBD8" if r["bh_sharpe_ratio"] >= 0 else "#D5F5E3"
        cell_colors.append(colors)

    table = ax_table.table(cellText=cell_data, colLabels=col_labels,
                           cellColours=cell_colors,
                           colColours=[C_PRIMARY]*9,
                           loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.5)

    # 表头样式
    for j in range(9):
        table[0, j].set_text_props(color="white", fontweight="bold", fontsize=7.5)

    # 关键发现
    ax_findings = fig.add_axes([0.05, 0.0, 0.9, 0.04])
    ax_findings.axis("off")
    ax_findings.text(0.0, 0.8, "关键发现：",
                     fontsize=9, color=C_ACCENT, fontweight="bold", ha="left", va="top")
    ax_findings.text(0.12, 0.8,
        "中国卫星+158% | 航天电子+156% | 宁德时代+30% | 比亚迪+4% vs 买入持有-64% | 三一重工Sharpe 1.07",
        fontsize=7.5, color=C_PRIMARY, ha="left", va="top")

    pdf.savefig(fig)
    plt.close()


# ================================================================
# 页面6-14：各股票详情（每只1-2页）
# ================================================================
def page_stock_detail(pdf, stock_name):
    m = summary[stock_name]

    # --- 第一页：指标卡 + 通道图 + ATR图 ---
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")

    # 标题
    ax_title = fig.add_axes([0.03, 0.94, 0.94, 0.05])
    ax_title.axis("off")
    ax_title.text(0.0, 0.5, f"{stock_name} — 海龟策略回测详情",
                  fontsize=16, color=C_PRIMARY, fontweight="bold", ha="left", va="center")
    ax_title.plot([0, 1], [0.1, 0.1], color=C_ACCENT, linewidth=1.5, transform=ax_title.transAxes)

    # 6个指标卡
    metrics_data = [
        ("累计回报", fmt_pct(m["cumulative_return"]), f"买入持有: {fmt_pct(m['bh_cumulative_return'])}"),
        ("最大回撤", fmt_pct(m["max_drawdown"]), f"买入持有: {fmt_pct(m['bh_max_drawdown'])}"),
        ("夏普比率", fmt_num(m["sharpe_ratio"]), f"买入持有: {fmt_num(m['bh_sharpe_ratio'])}"),
        ("年化收益", fmt_pct(m["annual_return"]), f"交易: {m['buy_count']}买/{m['sell_count']}卖"),
        ("胜率", fmt_pct(m["win_rate"]), "初始资金: ¥100,000"),
        ("最终市值", fmt_num(m.get("final_value", 0), 0), f"买入持有: ¥{fmt_num(m.get('bh_final_value', 0), 0)}"),
    ]

    card_w = 0.30
    card_h = 0.06
    start_x = 0.03
    start_y = 0.89
    gap_x = 0.015
    gap_y = 0.015

    for i, (label, value, sub) in enumerate(metrics_data):
        col = i % 3
        row = i // 3
        x = start_x + col * (card_w + gap_x)
        y = start_y - row * (card_h + gap_y)

        ax_card = fig.add_axes([x, y, card_w, card_h])
        ax_card.axis("off")
        ax_card.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                          boxstyle="round,pad=0.02",
                                          facecolor=C_BG, edgecolor="#E0E6ED", linewidth=0.5))

        color = C_PRIMARY
        if "回报" in label or "收益" in label:
            color = C_DOWN if m.get("cumulative_return", 0) >= 0 else C_UP
        elif "回撤" in label:
            color = C_UP
        elif "夏普" in label:
            color = C_DOWN if m.get("sharpe_ratio", 0) >= 0 else C_UP

        ax_card.text(0.5, 0.72, label, fontsize=7, color="#7F8C8D", ha="center", va="center")
        ax_card.text(0.5, 0.42, value, fontsize=14, color=color, fontweight="bold", ha="center", va="center")
        ax_card.text(0.5, 0.15, sub, fontsize=6, color="#95A5A6", ha="center", va="center")

    # 通道图
    img_path = os.path.join(CHARTS_DIR, f"{stock_name}_通道图.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.52, 0.9, 0.32])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("股价与唐奇安高低点通道", fontsize=10, color=C_PRIMARY, pad=4)

    # ATR图
    img_path = os.path.join(CHARTS_DIR, f"{stock_name}_ATR.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.18, 0.9, 0.32])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("ATR 波动率", fontsize=10, color=C_PRIMARY, pad=4)

    pdf.savefig(fig)
    plt.close()

    # --- 第二页：信号图 + 净值图 + 回撤图 + 交易记录 ---
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")

    # 信号图
    img_path = os.path.join(CHARTS_DIR, f"{stock_name}_交易信号.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.68, 0.9, 0.28])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("交易信号标记（买入▲ / 卖出▼ / 止损线）", fontsize=10, color=C_PRIMARY, pad=4)

    # 净值对比
    img_path = os.path.join(CHARTS_DIR, f"{stock_name}_净值对比.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.38, 0.9, 0.28])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("策略净值 vs 买入持有", fontsize=10, color=C_PRIMARY, pad=4)

    # 回撤曲线
    img_path = os.path.join(CHARTS_DIR, f"{stock_name}_回撤.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.10, 0.9, 0.26])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("回撤曲线对比", fontsize=10, color=C_PRIMARY, pad=4)

    pdf.savefig(fig)
    plt.close()

    # --- 第三页：交易记录表 ---
    trades = m.get("trades", [])
    if trades and len(trades) > 0:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")

        ax_title = fig.add_axes([0.03, 0.94, 0.94, 0.05])
        ax_title.axis("off")
        ax_title.text(0.0, 0.5, f"{stock_name} — 交易记录", fontsize=14,
                      color=C_PRIMARY, fontweight="bold", ha="left", va="center")

        ax_table = fig.add_axes([0.03, 0.08, 0.94, 0.84])
        ax_table.axis("off")

        col_labels = ["#", "日期", "方向", "价格(元)", "股数", "金额(元)", "ATR", "止损价"]
        cell_data = []
        cell_colors = []

        for i, t in enumerate(trades, 1):
            action = t.get("action", "")
            row = [
                str(i),
                str(t.get("date", ""))[:10],
                action,
                fmt_num(t.get("price", 0)),
                str(t.get("shares", 0)),
                fmt_num(t.get("value", 0)),
                fmt_num(t.get("atr")) if t.get("atr") else "-",
                fmt_num(t.get("stop_loss")) if t.get("stop_loss") else "-",
            ]
            cell_data.append(row)
            colors = ["#FFFFFF"] * 8
            if action == "BUY":
                colors[2] = "#FADBD8"
            else:
                colors[2] = "#D5F5E3"
            cell_colors.append(colors)

        table = ax_table.table(cellText=cell_data, colLabels=col_labels,
                               cellColours=cell_colors,
                               colColours=[C_PRIMARY]*8,
                               loc="upper center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.4)

        for j in range(8):
            table[0, j].set_text_props(color="white", fontweight="bold")

        pdf.savefig(fig)
        plt.close()


# ================================================================
# 页面：参数分析
# ================================================================
def page_params(pdf):
    # 茅台参数分析
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")

    ax_title = fig.add_axes([0.05, 0.92, 0.9, 0.06])
    ax_title.axis("off")
    add_section_title(ax_title, 5, "参数调节与场景分析")

    ax_title.text(0.0, 0.0, "通过5组参数组合，观察不同配置下的收益与风险变化",
                  fontsize=9, color=C_PRIMARY, ha="left", va="bottom")

    # 参数表
    ax_table = fig.add_axes([0.03, 0.74, 0.94, 0.16])
    ax_table.axis("off")

    param_labels = ["经典海龟\n20/10/2.0", "更紧止损\n20/10/1.5", "更宽止损\n20/10/3.0", "长周期\n55/20/2.0", "短周期\n10/5/2.0"]
    param_desc = ["标准参数，平衡趋势与风险", "止损更敏感，减少单笔亏损", "给趋势更多空间，减少假止损", "信号更少更可靠，适合大趋势", "信号更频繁，适合震荡市"]

    table_data = [[l, d] for l, d in zip(param_labels, param_desc)]
    table = ax_table.table(cellText=table_data,
                           colLabels=["参数组合", "策略特点"],
                           colColours=[C_PRIMARY, C_PRIMARY],
                           loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.8)
    for j in range(2):
        table[0, j].set_text_props(color="white", fontweight="bold")

    # 茅台参数图
    img_path = os.path.join(CHARTS_DIR, "茅台_参数敏感性.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.40, 0.9, 0.32])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("贵州茅台 - 参数敏感性分析", fontsize=11, color=C_PRIMARY, pad=4)

    # 比亚迪参数图
    img_path = os.path.join(CHARTS_DIR, "比亚迪_参数敏感性.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.06, 0.9, 0.32])
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_title("比亚迪 - 参数敏感性分析", fontsize=11, color=C_PRIMARY, pad=4)

    pdf.savefig(fig)
    plt.close()

    # 参数分析结论页
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_section_title(ax, 5, "参数分析结论")

    # 止损倍数影响
    add_text_box(ax, 0.05, 0.78, "① 止损倍数的影响", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.74,
        "止损1.5×ATR（更紧）：茅台累计回报从-8.70%改善至-0.47%，比亚迪从+4.28%提升至+10.00%\n"
        "  → 更紧止损在下跌行情中减少了回撤幅度\n"
        "止损3.0×ATR（更宽）：给趋势更多呼吸空间，但在震荡市中可能导致单笔亏损扩大\n"
        "结论：在A股高波动环境下，适当收紧止损（1.5-2.0倍ATR）效果更好",
        fontsize=8.5, color=C_PRIMARY, bg=C_LIGHT)

    # 通道周期影响
    add_text_box(ax, 0.05, 0.60, "② 通道周期的影响", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.56,
        "10日短周期：交易信号最多（茅台11次、比亚迪12次），在宁德时代上获得+46.93%高收益\n"
        "  → 适合高波动成长股，但也可能频繁假突破\n"
        "55日长周期：信号最少，茅台仅4次交易且全部亏损\n"
        "  → 长周期在震荡市中表现较差，但在大趋势中可能更可靠\n"
        "结论：短周期适合高波动成长股，长周期适合趋势明确的品种",
        fontsize=8.5, color=C_PRIMARY, bg=C_LIGHT)

    # 股票类型影响
    add_text_box(ax, 0.05, 0.42, "③ 股票类型的影响", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.38,
        "高波动成长股（宁德时代、中芯国际）：海龟策略表现最好，趋势跟踪能捕获大幅上涨\n"
        "太空概念股（中国卫星、航天电子）：强趋势行情下策略回报超100%，Sharpe>1.3\n"
        "防御性蓝筹（茅台、平安）：策略表现一般，震荡行情中假突破频繁\n"
        "周期股（三一重工）：策略Sharpe最高(1.07)，MDD仅-11.14%，风控效果最佳\n"
        "暴跌股（比亚迪）：策略+4.28% vs 买入持有-64.41%，防御力极强",
        fontsize=8.5, color=C_PRIMARY, bg=C_LIGHT)

    # 新增：太空概念股专项分析
    add_text_box(ax, 0.05, 0.22, "④ 太空概念股专项分析（新增）", fontsize=12, color=C_ACCENT, weight="bold")
    add_text_box(ax, 0.05, 0.18,
        "中国卫星：策略+158.10%，买入持有+344.08%，Sharpe 1.36，胜率62.5%\n"
        "航天电子：策略+156.47%，买入持有+214.72%，Sharpe 1.39，胜率57.1%\n"
        "航天动力：策略+109.13%，买入持有+265.69%，Sharpe 1.06，胜率25.0%\n"
        "分析：航天概念股在过去两年是强趋势行情，海龟策略捕获了大部分趋势。\n"
        "      虽然买入持有收益更高，但策略的Sharpe比率表现优秀（1.06~1.39），\n"
        "      说明风险调整后的收益较好。航天动力胜率仅25%但依然盈利超100%，\n"
        "      体现了海龟策略「少数大赢覆盖多数小亏」的典型特征。",
        fontsize=8.5, color=C_PRIMARY, bg="#FEF9E7")

    fig.tight_layout(pad=1)
    pdf.savefig(fig)
    plt.close()


# ================================================================
# 页面：总结心得
# ================================================================
def page_summary_final(pdf):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_section_title(ax, 6, "海龟法则适应场景与使用心得")

    # 适应场景
    add_text_box(ax, 0.05, 0.78, "6.1 适应场景", fontsize=12, color=C_ACCENT, weight="bold")

    add_text_box(ax, 0.05, 0.74, "  适合的场景", fontsize=10, color=C_DOWN, weight="bold", bg="#EAFAF1")
    add_text_box(ax, 0.05, 0.70,
        "  ✓ 强趋势市场 — 单边上涨或下跌行情中，突破信号可靠性高\n"
        "  ✓ 高波动品种 — 成长股、科技股、周期股、太空概念股等波动大的标的\n"
        "  ✓ 中长期投资 — 持仓周期通常数周到数月，不适合日内交易\n"
        "  ✓ 商品期货市场 — 海龟策略的原始战场，趋势性强且可双向交易",
        fontsize=8.5, color=C_PRIMARY)

    add_text_box(ax, 0.05, 0.58, "  不适合的场景", fontsize=10, color=C_UP, weight="bold", bg="#FDEDEC")
    add_text_box(ax, 0.05, 0.54,
        "  ✗ 震荡市场 — 价格在区间内反复波动时，突破信号频繁失效\n"
        "  ✗ 低流动性品种 — 成交量小、滑点大，突破时可能无法以理想价格成交\n"
        "  ✗ 短线交易 — 信号产生频率低，不适合追求高频交易的投资者\n"
        "  ✗ 基本面突变 — 如突发利空导致跳空暴跌，止损可能远低于设定价位",
        fontsize=8.5, color=C_PRIMARY)

    # 使用心得
    add_text_box(ax, 0.05, 0.42, "6.2 使用心得", fontsize=12, color=C_ACCENT, weight="bold")

    insights = [
        ("纪律性是灵魂",
         "策略本身不复杂，真正难点在于严格执行。连续止损3-5次后，人性本能倾向于\n"
         "跳过下一个信号，而这往往正是大趋势启动的信号。程序化交易的价值在于不犹豫。"),
        ("截断亏损，让利润奔跑",
         "回测数据显示海龟策略胜率通常30%-50%，但盈利交易平均收益远大于亏损平均损失，\n"
         "少数大趋势的利润覆盖了大量小亏损。航天动力胜率仅25%却盈利109%即是明证。"),
        ("参数不是越复杂越好",
         "经典20/10/2.0参数在大多数股票上表现已经不错。过度优化参数容易导致过拟合\n"
         "——在历史数据上完美但在未来失效。建议测试参数稳定性而非追求历史最优。"),
        ("ATR是最被低估的指标",
         "大多数人关注唐奇安通道的突破信号，但ATR才是海龟策略的真正秘密武器。\n"
         "它让策略自动适应不同波动率环境，这是固定百分比止损做不到的。"),
        ("不要期待跑赢牛市的买入持有",
         "单边大牛市中（如中国卫星+344%），策略收益(+158%)通常低于满仓持有。\n"
         "但海龟的价值在于风险调整后的收益——在熊市中大幅跑赢买入持有\n"
         "（比亚迪+4.28% vs -64.41%）。"),
        ("结合多品种分散风险",
         "海龟策略最初在24个商品期货品种上同时运行。股票市场同样应构建多股票组合，\n"
         "避免重仓单一标的。本次9只股票的组合验证了分散化的价值。"),
        ("A股需要适配",
         "A股T+1交易、涨跌停限制、做空受限等特性会影响执行效果。A股只能做多，\n"
         "无法在下跌趋势中做空获利，策略在熊市中只能空仓等待，收益来源受限。"),
    ]

    y = 0.38
    for title, desc in insights:
        add_text_box(ax, 0.07, y, f"  {title}", fontsize=9, color=C_ACCENT, weight="bold", bg="#F5EEF8")
        add_text_box(ax, 0.22, y, desc, fontsize=7.5, color=C_PRIMARY)
        y -= 0.045

    # 最终总结
    add_text_box(ax, 0.05, 0.04,
        "海龟交易法则之所以成为传奇，不在于神秘的技术指标，而在于它把趋势跟踪 + 风险管理 + 资金管理\n"
        "三者完美结合成了一套可执行的系统。交易不是预测，而是应对——你不需要知道市场往哪走，\n"
        "你只需要知道：如果市场往涨你该怎么做，如果往跌你该怎么做。然后，严格执行。",
        fontsize=9, color=C_PRIMARY, bg="#FEF9E7", weight="bold")

    fig.tight_layout(pad=1)
    pdf.savefig(fig)
    plt.close()


# ================================================================
# 主函数
# ================================================================
def main():
    print("=" * 60)
    print("  生成海龟交易策略分析报告 PDF")
    print("=" * 60)

    with PdfPages(OUTPUT_PDF) as pdf:
        # 封面
        print("  [1/N] 封面...")
        page_cover(pdf)

        # 策略概述
        print("  [2/N] 策略概述...")
        page_overview(pdf)

        # 核心概念
        print("  [3/N] 核心概念...")
        page_concepts(pdf)

        # Python实现
        print("  [4/N] Python实现...")
        page_python(pdf)

        # 多股票对比
        print("  [5/N] 多股票对比...")
        page_comparison(pdf)

        # 各股票详情
        for i, stock in enumerate(ALL_STOCKS):
            print(f"  [{6+i}/N] {stock} 详情...")
            page_stock_detail(pdf, stock)

        # 参数分析
        next_page = 6 + len(ALL_STOCKS)
        print(f"  [{next_page}/N] 参数分析...")
        page_params(pdf)

        # 总结
        print(f"  [{next_page+1}/N] 总结心得...")
        page_summary_final(pdf)

        # PDF元信息
        d = pdf.infodict()
        d["Title"] = "海龟交易策略分析报告"
        d["Author"] = "BI工作坊 AI量化公益课"
        d["Subject"] = "Task4 海龟交易法则实战演练"
        d["Keywords"] = "海龟策略,唐奇安通道,ATR,趋势跟踪,量化交易"

    file_size = os.path.getsize(OUTPUT_PDF) / 1024 / 1024
    print(f"\n{'=' * 60}")
    print(f"  PDF生成完毕!")
    print(f"  路径: {OUTPUT_PDF}")
    print(f"  大小: {file_size:.1f} MB")
    print(f"  总页数: 封面+概述+概念+代码+对比+{len(ALL_STOCKS)}只股票详情+参数+总结")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
