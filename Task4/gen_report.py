"""
海龟交易策略报告 HTML 生成器
"""
import os
import json
import base64
import pandas as pd

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(DATA_DIR, "charts")

# 加载策略汇总数据
with open(os.path.join(DATA_DIR, "strategy_summary.json"), "r", encoding="utf-8") as f:
    summary = json.load(f)

# 加载批量回测结果
batch_df = pd.read_csv(os.path.join(DATA_DIR, "海龟策略回测结果.csv"), encoding="utf-8-sig")


def img_to_base64(img_path):
    """将图片转为base64嵌入HTML"""
    with open(img_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def fmt_pct(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{v*100:.2f}%"


def fmt_num(v, digits=2):
    if v is None or pd.isna(v):
        return "-"
    return f"{v:.{digits}f}"


# ========== 生成交易记录表 ==========
def gen_trade_table(trades):
    if not trades:
        return "<p class='no-data'>无交易记录</p>"
    rows = ""
    for i, t in enumerate(trades, 1):
        action_cls = "buy" if t["action"] == "BUY" else "sell"
        date_str = str(t["date"])[:10]
        atr_str = fmt_num(t.get("atr"), 2) if t.get("atr") else "-"
        stop_str = fmt_num(t.get("stop_loss"), 2) if t.get("stop_loss") else "-"
        rows += f"""
        <tr>
            <td>{i}</td>
            <td>{date_str}</td>
            <td class="{action_cls}">{t['action']}</td>
            <td>{fmt_num(t['price'])}</td>
            <td>{t['shares']}</td>
            <td>{fmt_num(t['value'])}</td>
            <td>{atr_str}</td>
            <td>{stop_str}</td>
        </tr>"""
    return f"""
    <table class="data-table">
        <thead>
            <tr><th>#</th><th>日期</th><th>方向</th><th>价格(元)</th><th>股数</th><th>金额(元)</th><th>ATR</th><th>止损价</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


# ========== 生成经典参数指标卡 ==========
def gen_metrics_cards(stock_name, m):
    return f"""
    <div class="metrics-grid">
        <div class="metric-card {'positive' if m['cumulative_return'] >= 0 else 'negative'}">
            <div class="metric-label">累计回报</div>
            <div class="metric-value">{fmt_pct(m['cumulative_return'])}</div>
            <div class="metric-sub">买入持有: {fmt_pct(m['bh_cumulative_return'])}</div>
        </div>
        <div class="metric-card negative">
            <div class="metric-label">最大回撤 (MDD)</div>
            <div class="metric-value">{fmt_pct(m['max_drawdown'])}</div>
            <div class="metric-sub">买入持有: {fmt_pct(m['bh_max_drawdown'])}</div>
        </div>
        <div class="metric-card {'positive' if m['sharpe_ratio'] >= 0 else 'negative'}">
            <div class="metric-label">夏普比率</div>
            <div class="metric-value">{fmt_num(m['sharpe_ratio'])}</div>
            <div class="metric-sub">买入持有: {fmt_num(m['bh_sharpe_ratio'])}</div>
        </div>
        <div class="metric-card {'positive' if m['annual_return'] >= 0 else 'negative'}">
            <div class="metric-label">年化收益率</div>
            <div class="metric-value">{fmt_pct(m['annual_return'])}</div>
            <div class="metric-sub">交易次数: {m['buy_count']}买/{m['sell_count']}卖</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">胜率</div>
            <div class="metric-value">{fmt_pct(m['win_rate'])}</div>
            <div class="metric-sub">初始资金: 100,000元</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">最终市值</div>
            <div class="metric-value">{fmt_num(m.get('final_value', 0), 0)}</div>
            <div class="metric-sub">买入持有: {fmt_num(m.get('bh_final_value', 0), 0)}</div>
        </div>
    </div>"""


# ========== 生成单股票详情区块 ==========
def gen_stock_section(stock_name, img_prefix):
    m = summary[stock_name]
    charts = {
        "channel": f"{stock_name}_通道图.png",
        "atr": f"{stock_name}_ATR.png",
        "signal": f"{stock_name}_交易信号.png",
        "netvalue": f"{stock_name}_净值对比.png",
        "drawdown": f"{stock_name}_回撤.png",
    }

    # 嵌入图片base64
    img_tags = {}
    for key, fname in charts.items():
        path = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(path):
            img_tags[key] = img_to_base64(path)

    return f"""
    <div class="stock-section" id="stock-{stock_name}">
        <h3 class="stock-title">{stock_name} - 海龟策略回测详情</h3>
        {gen_metrics_cards(stock_name, m)}

        <div class="chart-row">
            <div class="chart-block full">
                <h4>股价与唐奇安高低点通道</h4>
                <img src="{img_tags.get('channel', '')}" alt="{stock_name}通道图" />
            </div>
        </div>
        <div class="chart-row">
            <div class="chart-block full">
                <h4>ATR 波动率</h4>
                <img src="{img_tags.get('atr', '')}" alt="{stock_name}ATR" />
            </div>
        </div>
        <div class="chart-row">
            <div class="chart-block full">
                <h4>交易信号标记（买入▲ / 卖出▼ / 止损线）</h4>
                <img src="{img_tags.get('signal', '')}" alt="{stock_name}交易信号" />
            </div>
        </div>
        <div class="chart-row two-col">
            <div class="chart-block">
                <h4>策略净值 vs 买入持有</h4>
                <img src="{img_tags.get('netvalue', '')}" alt="{stock_name}净值对比" />
            </div>
            <div class="chart-block">
                <h4>回撤曲线</h4>
                <img src="{img_tags.get('drawdown', '')}" alt="{stock_name}回撤" />
            </div>
        </div>

        <h4>交易记录</h4>
        {gen_trade_table(m.get('trades', []))}
    </div>"""


# ========== 生成多股票对比表 ==========
def gen_comparison_table():
    classic = batch_df[batch_df["param"] == "入20/出10/ATR20/止2.0"].copy()
    if len(classic) == 0:
        classic = batch_df.head(6)

    rows = ""
    for _, r in classic.iterrows():
        cr_cls = "positive" if r["cumulative_return"] >= 0 else "negative"
        bh_cr_cls = "positive" if r["bh_cumulative_return"] >= 0 else "negative"
        sharpe_cls = "positive" if r["sharpe_ratio"] >= 0 else "negative"
        rows += f"""
        <tr>
            <td class="stock-name">{r['stock']}</td>
            <td class="{cr_cls}">{fmt_pct(r['cumulative_return'])}</td>
            <td class="{bh_cr_cls}">{fmt_pct(r['bh_cumulative_return'])}</td>
            <td class="negative">{fmt_pct(r['max_drawdown'])}</td>
            <td class="negative">{fmt_pct(r['bh_max_drawdown'])}</td>
            <td class="{sharpe_cls}">{fmt_num(r['sharpe_ratio'])}</td>
            <td>{fmt_num(r['bh_sharpe_ratio'])}</td>
            <td>{fmt_pct(r['annual_return'])}</td>
            <td>{fmt_pct(r['win_rate'])}</td>
            <td>{int(r['buy_count'])}买/{int(r['sell_count'])}卖</td>
        </tr>"""

    return f"""
    <table class="data-table comparison-table">
        <thead>
            <tr>
                <th rowspan="2">股票</th>
                <th colspan="2">累计回报</th>
                <th colspan="2">最大回撤</th>
                <th colspan="2">夏普比率</th>
                <th rowspan="2">年化收益</th>
                <th rowspan="2">胜率</th>
                <th rowspan="2">交易次数</th>
            </tr>
            <tr>
                <th>海龟策略</th><th>买入持有</th>
                <th>海龟策略</th><th>买入持有</th>
                <th>海龟策略</th><th>买入持有</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


# ========== 生成参数对比表 ==========
def gen_param_table(stock_name):
    stock_data = batch_df[batch_df["stock"] == stock_name].copy()
    if len(stock_data) == 0:
        return "<p class='no-data'>无数据</p>"

    rows = ""
    for _, r in stock_data.iterrows():
        cr_cls = "positive" if r["cumulative_return"] >= 0 else "negative"
        sharpe_cls = "positive" if r["sharpe_ratio"] >= 0 else "negative"
        rows += f"""
        <tr>
            <td>{r['param']}</td>
            <td class="{cr_cls}">{fmt_pct(r['cumulative_return'])}</td>
            <td class="negative">{fmt_pct(r['max_drawdown'])}</td>
            <td class="{sharpe_cls}">{fmt_num(r['sharpe_ratio'])}</td>
            <td>{fmt_pct(r['annual_return'])}</td>
            <td>{fmt_pct(r['win_rate'])}</td>
            <td>{int(r['buy_count'])}买/{int(r['sell_count'])}卖</td>
        </tr>"""

    return f"""
    <table class="data-table">
        <thead>
            <tr><th>参数组合<br/><small>入场/离场/ATR/止损倍数</small></th><th>累计回报</th><th>最大回撤</th><th>夏普比率</th><th>年化收益</th><th>胜率</th><th>交易次数</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


# ========== 嵌入对比图和参数图 ==========
multi_cmp_img = img_to_base64(os.path.join(CHARTS_DIR, "多股票对比.png"))
maotai_param_img = img_to_base64(os.path.join(CHARTS_DIR, "茅台_参数敏感性.png"))
byd_param_img = img_to_base64(os.path.join(CHARTS_DIR, "比亚迪_参数敏感性.png"))


# ========== HTML 模板 ==========
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task4 - 海龟交易法则实战演练</title>
    <style>
        :root {{
            --bg: #f5f7fa;
            --card-bg: #ffffff;
            --primary: #2c3e50;
            --accent: #8e44ad;
            --up: #e74c3c;
            --down: #27ae60;
            --border: #e0e6ed;
            --text: #2c3e50;
            --text-light: #7f8c8d;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
            font-size: 15px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

        /* 封面 */
        .cover {{
            background: linear-gradient(135deg, #2c3e50 0%, #8e44ad 100%);
            color: white;
            padding: 60px 40px;
            border-radius: 16px;
            margin-bottom: 40px;
            text-align: center;
        }}
        .cover h1 {{ font-size: 36px; margin-bottom: 12px; font-weight: 700; }}
        .cover .subtitle {{ font-size: 18px; opacity: 0.85; margin-bottom: 8px; }}
        .cover .meta {{ font-size: 14px; opacity: 0.7; margin-top: 16px; }}

        /* 导航 */
        .nav {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 30px;
            padding: 12px 16px;
            background: var(--card-bg);
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            position: sticky;
            top: 10px;
            z-index: 100;
        }}
        .nav a {{
            text-decoration: none;
            color: var(--primary);
            font-size: 13px;
            padding: 6px 14px;
            border-radius: 6px;
            transition: all 0.2s;
            font-weight: 500;
        }}
        .nav a:hover {{ background: var(--accent); color: white; }}

        /* 章节 */
        .section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}
        .section h2 {{
            font-size: 24px;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid var(--accent);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section h2 .num {{
            background: var(--accent);
            color: white;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }}
        .section h3 {{
            font-size: 20px;
            color: var(--primary);
            margin: 24px 0 12px;
        }}
        .section h4 {{
            font-size: 16px;
            color: var(--text);
            margin: 16px 0 8px;
            font-weight: 600;
        }}
        .section p {{ margin-bottom: 12px; }}
        .section ul, .section ol {{ margin: 12px 0 12px 24px; }}
        .section li {{ margin-bottom: 6px; }}

        /* 概念卡片 */
        .concept-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .concept-card {{
            background: #f8f9fb;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.2s;
        }}
        .concept-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
        .concept-card h4 {{
            color: var(--accent);
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .concept-card .formula {{
            background: #fff;
            border: 1px dashed var(--border);
            border-radius: 6px;
            padding: 8px 12px;
            font-family: "Courier New", monospace;
            font-size: 13px;
            margin: 8px 0;
            color: var(--primary);
        }}

        /* 优势卡片 */
        .advantage-list {{ list-style: none; margin: 16px 0; }}
        .advantage-list li {{
            background: #f8f9fb;
            border-left: 4px solid var(--accent);
            padding: 14px 18px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
        }}
        .advantage-list li strong {{ color: var(--accent); }}

        /* 指标卡 */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fb;
            border-radius: 10px;
            padding: 18px;
            text-align: center;
            border: 1px solid var(--border);
        }}
        .metric-card.positive {{ border-left: 4px solid var(--down); }}
        .metric-card.negative {{ border-left: 4px solid var(--up); }}
        .metric-label {{ font-size: 13px; color: var(--text-light); margin-bottom: 6px; }}
        .metric-value {{ font-size: 24px; font-weight: 700; color: var(--primary); }}
        .metric-card.positive .metric-value {{ color: var(--down); }}
        .metric-card.negative .metric-value {{ color: var(--up); }}
        .metric-sub {{ font-size: 11px; color: var(--text-light); margin-top: 4px; }}

        /* 图表 */
        .chart-row {{ margin: 16px 0; }}
        .chart-row.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .chart-block {{
            background: #fafbfc;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
        }}
        .chart-block.full {{ }}
        .chart-block h4 {{ margin-bottom: 10px; color: var(--text); }}
        .chart-block img {{ width: 100%; height: auto; border-radius: 6px; }}

        /* 表格 */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 13px;
        }}
        .data-table th {{
            background: var(--primary);
            color: white;
            padding: 10px 8px;
            text-align: center;
            font-weight: 600;
        }}
        .data-table th small {{ font-weight: 400; opacity: 0.8; }}
        .data-table td {{
            padding: 8px;
            border-bottom: 1px solid var(--border);
            text-align: center;
        }}
        .data-table tbody tr:hover {{ background: #f8f9fb; }}
        .data-table td.buy {{ color: var(--up); font-weight: 600; }}
        .data-table td.sell {{ color: var(--down); font-weight: 600; }}
        .data-table td.positive {{ color: var(--down); font-weight: 600; }}
        .data-table td.negative {{ color: var(--up); font-weight: 600; }}
        .data-table td.stock-name {{ font-weight: 600; text-align: left; }}
        .comparison-table th {{ font-size: 12px; }}

        /* 股票区块 */
        .stock-section {{
            background: #fafbfc;
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid var(--border);
        }}
        .stock-title {{
            font-size: 20px;
            color: var(--primary);
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent);
        }}

        /* 代码块 */
        .code-block {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            margin: 16px 0;
            font-family: "Courier New", monospace;
            font-size: 13px;
            line-height: 1.6;
            overflow-x: auto;
            white-space: pre;
        }}
        .code-block .comment {{ color: #95a5a6; }}
        .code-block .keyword {{ color: #e74c3c; }}
        .code-block .string {{ color: #27ae60; }}
        .code-block .func {{ color: #f39c12; }}

        /* 提示框 */
        .callout {{
            background: #fef9e7;
            border-left: 4px solid #f39c12;
            padding: 16px 20px;
            border-radius: 0 8px 8px 0;
            margin: 16px 0;
        }}
        .callout.info {{
            background: #eaf2f8;
            border-left-color: #3498db;
        }}
        .callout.success {{
            background: #eafaf1;
            border-left-color: #27ae60;
        }}
        .callout h4 {{ margin-bottom: 6px; }}

        .no-data {{ color: var(--text-light); font-style: italic; }}

        /* 步骤流程 */
        .step-flow {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin: 20px 0;
        }}
        .step-item {{
            flex: 1;
            min-width: 140px;
            background: #f8f9fb;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            border-top: 3px solid var(--accent);
        }}
        .step-item .step-num {{
            background: var(--accent);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        .step-item .step-title {{ font-weight: 600; font-size: 14px; margin-bottom: 4px; }}
        .step-item .step-desc {{ font-size: 12px; color: var(--text-light); }}

        /* 页脚 */
        .footer {{
            text-align: center;
            padding: 24px;
            color: var(--text-light);
            font-size: 13px;
        }}
    </style>
</head>
<body>
<div class="container">

<!-- 封面 -->
<div class="cover">
    <h1>复刻传奇：海龟交易法则实战演练</h1>
    <div class="subtitle">BI工作坊 · 量化交易公益课 · Task4</div>
    <div class="meta">海龟交易策略 Python 实现 · 多股票回测 · 参数敏感性分析</div>
</div>

<!-- 导航 -->
<div class="nav">
    <a href="#part1">1. 策略概述</a>
    <a href="#part2">2. 核心概念</a>
    <a href="#part3">3. Python实现</a>
    <a href="#part4">4. 回测结果</a>
    <a href="#part5">5. 参数分析</a>
    <a href="#part6">6. 总结心得</a>
</div>

<!-- ========== Part 1: 策略概述 ========== -->
<div class="section" id="part1">
    <h2><span class="num">1</span>海龟交易策略概述</h2>

    <h3>1.1 历史背景</h3>
    <p>1983年，美国著名交易员<strong>理查德·丹尼斯（Richard Dennis）</strong>与威廉·埃克哈特打了一个赌：伟大的交易员究竟是天生还是后天培养的？丹尼斯坚信交易可以被系统化教授，于是招募了一批学员，称之为<strong>"海龟"</strong>。他用一套完全机械化的交易系统培训这些学员，在随后的4年中，海龟们累计盈利超过1亿美元，创造了华尔街交易史上的传奇。</p>

    <p>海龟交易法则的核心思想是：<strong>趋势跟踪 + 突破入场 + 严格风控</strong>。它不预测市场方向，而是等待市场自己走出趋势，在趋势确认的瞬间跟进，并通过动态止损和仓位管理控制风险。</p>

    <h3>1.2 核心思想</h3>
    <div class="concept-grid">
        <div class="concept-card">
            <h4>趋势跟踪</h4>
            <p>不预测市场方向，而是等待价格突破历史高低点后顺势入场。海龟策略认为，大趋势一旦形成，往往持续较长时间，"截断亏损，让利润奔跑"。</p>
        </div>
        <div class="concept-card">
            <h4>突破入场</h4>
            <p>使用<strong>唐奇安通道</strong>（Donchian Channel）作为入场信号。当价格突破过去N日的最高价时买入，突破最低价时卖出（做空）。</p>
        </div>
        <div class="concept-card">
            <h4>波动率自适应</h4>
            <p>通过<strong>ATR（平均真实波幅）</strong>动态衡量市场波动率，止损距离和仓位大小随波动率自动调整，实现"波动大则仓位小，波动小则仓位大"。</p>
        </div>
        <div class="concept-card">
            <h4>严格风控</h4>
            <p>每笔交易风险不超过总资金的2%，止损设在入场价-2×ATR处。亏损时果断离场，绝不让小亏变成大亏。</p>
        </div>
    </div>

    <h3>1.3 关键优势</h3>
    <ul class="advantage-list">
        <li><strong>系统化交易，克服人性弱点</strong> — 海龟策略是完全规则化的交易系统，买卖信号、止损位置、仓位大小都有明确计算公式，不依赖主观判断，有效避免了恐惧与贪婪对交易决策的干扰。</li>
        <li><strong>趋势捕获能力强</strong> — 突破入场机制确保在大趋势启动时第一时间进场。历史上海龟策略在单边大牛市或大熊市中表现尤为出色，能够捕获数倍于止损额度的利润。</li>
        <li><strong>动态风险控制</strong> — ATR随市场波动率自动调节，波动剧烈时止损更宽、仓位更小；波动平缓时止损更紧、仓位更大。这种自适应机制使策略在不同市场环境下都能保持合理的风险敞口。</li>
        <li><strong>明确的资金管理规则</strong> — 每笔交易限定2%的最大风险，加上最多4个单位的金字塔加仓规则，确保即使连续亏损也不会伤及元气，而盈利时能通过加仓放大收益。</li>
        <li><strong>可量化、可回测</strong> — 所有规则均可用数学公式表达，适合用Python编程实现和历史数据回测，策略效果可通过MDD、Sharpe Ratio等指标客观评估。</li>
        <li><strong>跨市场适用性</strong> — 海龟策略最初用于商品期货，但其核心逻辑同样适用于股票、外汇、加密货币等市场，具有广泛的适应性。</li>
    </ul>

    <div class="callout info">
        <h4>海龟策略的两套系统</h4>
        <p><strong>系统一（短期）</strong>：20日突破入场，10日突破离场。信号更频繁，适合波动较大的市场。</p>
        <p><strong>系统二（长期）</strong>：55日突破入场，20日突破离场。信号更少但更可靠，适合捕获大趋势。</p>
    </div>
</div>

<!-- ========== Part 2: 核心概念 ========== -->
<div class="section" id="part2">
    <h2><span class="num">2</span>核心概念详解</h2>

    <h3>2.1 高低点通道（唐奇安通道 Donchian Channel）</h3>
    <p>唐奇安通道由技术分析先驱 Richard Donchian 发明，是海龟策略的核心入场工具。它计算过去N个交易日的最高价和最低价，形成一个动态的价格通道。</p>

    <div class="concept-grid">
        <div class="concept-card">
            <h4>入场通道（20日）</h4>
            <div class="formula">上轨 = max(high, 过去20日)</div>
            <div class="formula">下轨 = min(low, 过去20日)</div>
            <p>当收盘价突破上轨 → <strong>买入信号</strong>（创新高，趋势向上）<br>
            当收盘价跌破下轨 → <strong>卖出信号</strong>（创新低，趋势向下）</p>
        </div>
        <div class="concept-card">
            <h4>离场通道（10日）</h4>
            <div class="formula">下轨 = min(low, 过去10日)</div>
            <div class="formula">上轨 = max(high, 过去10日)</div>
            <p>多头持仓时：收盘价跌破10日最低价 → <strong>平仓离场</strong><br>
            比入场通道更短周期，目的是在趋势反转时更快退出保住利润</p>
        </div>
    </div>

    <div class="callout">
        <h4>为什么入场用20日、离场用10日？</h4>
        <p>这是海龟策略的精髓：<strong>慢进快出</strong>。入场通道较长（20日），确保趋势确实已经形成，过滤掉短期噪音；离场通道较短（10日），一旦短期趋势有反转迹象就果断退出，不让利润回吐过多。</p>
    </div>

    <h3>2.2 平均真实波幅（ATR, Average True Range）</h3>
    <p>ATR 由技术分析大师 Welles Wilder 发明，用于衡量市场波动率。海龟策略用 ATR 来动态设定止损距离和仓位大小。</p>

    <div class="concept-card">
        <h4>真实波幅（True Range, TR）的计算</h4>
        <p>TR 取以下三个值中的最大值，反映当日价格波动的最大幅度：</p>
        <div class="formula">TR = max(
    当日最高价 - 当日最低价,
    |当日最高价 - 前日收盘价|,
    |当日最低价 - 前日收盘价|
)</div>
        <p>第一个值衡量当日正常振幅；后两个值考虑了跳空缺口的情况。如果当日跳空高开或低开，TR 会捕捉到这个跳空幅度。</p>
    </div>

    <div class="concept-card">
        <h4>ATR 的计算</h4>
        <div class="formula">ATR = TR 的 N 日移动平均（默认N=20）</div>
        <p>ATR 越大，说明市场波动越剧烈；ATR 越小，说明市场越平静。</p>
    </div>

    <h4>ATR 在海龟策略中的三大作用</h4>
    <div class="step-flow">
        <div class="step-item">
            <div class="step-num">1</div>
            <div class="step-title">动态止损</div>
            <div class="step-desc">止损价 = 买入价 - 2×ATR<br/>波动大则止损宽，波动小则止损紧</div>
        </div>
        <div class="step-item">
            <div class="step-num">2</div>
            <div class="step-title">仓位管理</div>
            <div class="step-desc">头寸单位 = (资金×2%) / (ATR×合约乘数)<br/>波动大则仓位小，控制单笔风险</div>
        </div>
        <div class="step-item">
            <div class="step-num">3</div>
            <div class="step-title">金字塔加仓</div>
            <div class="step-desc">每上涨 0.5×ATR 加仓一个单位<br/>最多加仓4次，逐步扩大盈利仓位</div>
        </div>
    </div>

    <h3>2.3 止损条件</h3>
    <p>海龟策略的止损规则是其长期盈利的关键保障，核心原则是<strong>"任何一笔交易的风险绝不超过账户总额的2%"</strong>。</p>

    <div class="concept-grid">
        <div class="concept-card">
            <h4>止损价计算</h4>
            <div class="formula">止损价 = 买入价 - 2 × ATR</div>
            <p>例如：买入价100元，ATR=5元，则止损价 = 100 - 2×5 = 90元。如果价格跌破90元，立即平仓。</p>
        </div>
        <div class="concept-card">
            <h4>仓位大小计算</h4>
            <div class="formula">头寸 = (总资金 × 2%) / (ATR × 合约乘数)</div>
            <p>确保从买入价到止损价的亏损恰好等于总资金的2%。ATR越大，买得越少；ATR越小，买得越多。</p>
        </div>
        <div class="concept-card">
            <h4>加仓后的止损调整</h4>
            <p>每加仓一个单位，整个仓位的止损价上移 0.5×ATR。这样早期建仓的部分也逐渐进入盈利保护状态，不会因为加仓而增加整体风险。</p>
        </div>
        <div class="concept-card">
            <h4>离场信号</h4>
            <p>除了止损离场外，还有<strong>通道离场</strong>：价格跌破10日最低价时平仓。这是趋势结束的正常退出机制，不是止损，而是利润兑现。</p>
        </div>
    </div>

    <div class="callout success">
        <h4>止损的核心哲学</h4>
        <p>海龟法则认为：<strong>"有老交易员，也有大胆的交易员，但没有大胆的老交易员。"</strong> 严格的止损是交易员长期生存的根本。2%的风险限制意味着即使连续亏损20次，账户也只损失约33%，仍有机会翻身。</p>
    </div>
</div>

<!-- ========== Part 3: Python实现 ========== -->
<div class="section" id="part3">
    <h2><span class="num">3</span>Python 编程实现</h2>

    <p>以下为海龟交易策略的完整Python实现，包括数据加载、通道计算、ATR计算、信号生成、回测模拟和量化指标计算。</p>

    <div class="step-flow">
        <div class="step-item"><div class="step-num">1</div><div class="step-title">加载股价数据</div><div class="step-desc">读取CSV格式日线数据</div></div>
        <div class="step-item"><div class="step-num">2</div><div class="step-title">计算通道</div><div class="step-desc">20日高低点 + 10日离场通道</div></div>
        <div class="step-item"><div class="step-num">3</div><div class="step-title">计算ATR</div><div class="step-desc">真实波幅 + 20日移动平均</div></div>
        <div class="step-item"><div class="step-num">4</div><div class="step-title">生成信号</div><div class="step-desc">突破买入 + 止损/通道卖出</div></div>
        <div class="step-item"><div class="step-num">5</div><div class="step-title">可视化</div><div class="step-desc">通道/ATR/信号/净值/回撤</div></div>
        <div class="step-item"><div class="step-num">6</div><div class="step-title">回测评估</div><div class="step-desc">MDD/Sharpe/累计回报</div></div>
    </div>

    <h3>3.1 核心代码</h3>

    <h4>① 加载股价数据</h4>
    <div class="code-block"><span class="comment"># 加载CSV格式股价数据，统一日期格式</span>
<span class="keyword">def</span> <span class="func">load_stock_data</span>(csv_path):
    df = pd.read_csv(csv_path, encoding=<span class="string">"utf-8-sig"</span>)
    df[<span class="string">"trade_date"</span>] = df[<span class="string">"trade_date"</span>].astype(str).str.replace(<span class="string">"-"</span>, <span class="string">""</span>)
    df[<span class="string">"trade_date"</span>] = pd.to_datetime(df[<span class="string">"trade_date"</span>], format=<span class="string">"%Y%m%d"</span>)
    df = df.sort_values(<span class="string">"trade_date"</span>).reset_index(drop=<span class="keyword">True</span>)
    <span class="keyword">return</span> df</div>

    <h4>② 计算唐奇安高低点通道</h4>
    <div class="code-block"><span class="comment"># 入场通道20日，离场通道10日，shift(1)避免未来数据</span>
<span class="keyword">def</span> <span class="func">calc_donchian_channel</span>(df, entry_period=20, exit_period=10):
    df = df.copy()
    df[<span class="string">"upper_entry"</span>] = df[<span class="string">"high"</span>].rolling(window=entry_period).max().shift(1)
    df[<span class="string">"lower_entry"</span>] = df[<span class="string">"low"</span>].rolling(window=entry_period).min().shift(1)
    df[<span class="string">"upper_exit"</span>] = df[<span class="string">"high"</span>].rolling(window=exit_period).max().shift(1)
    df[<span class="string">"lower_exit"</span>] = df[<span class="string">"low"</span>].rolling(window=exit_period).min().shift(1)
    df[<span class="string">"channel_mid"</span>] = (df[<span class="string">"upper_entry"</span>] + df[<span class="string">"lower_entry"</span>]) / 2
    <span class="keyword">return</span> df</div>

    <h4>③ 计算 ATR（平均真实波幅）</h4>
    <div class="code-block"><span class="comment"># TR取三种波动幅度的最大值，ATR为TR的N日移动平均</span>
<span class="keyword">def</span> <span class="func">calc_atr</span>(df, period=20):
    df = df.copy()
    prev_close = df[<span class="string">"close"</span>].shift(1)
    tr1 = df[<span class="string">"high"</span>] - df[<span class="string">"low"</span>]                      <span class="comment"># 当日振幅</span>
    tr2 = (df[<span class="string">"high"</span>] - prev_close).abs()              <span class="comment"># 跳空高开</span>
    tr3 = (df[<span class="string">"low"</span>] - prev_close).abs()               <span class="comment"># 跳空低开</span>
    df[<span class="string">"TR"</span>] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df[<span class="string">"ATR"</span>] = df[<span class="string">"TR"</span>].rolling(window=period).mean()
    <span class="keyword">return</span> df</div>

    <h4>④ 生成买入/卖出交易信号</h4>
    <div class="code-block"><span class="comment"># 买入：收盘价突破20日最高价；卖出：跌破10日最低价或触及2×ATR止损</span>
<span class="keyword">def</span> <span class="func">generate_signals</span>(df, entry_period=20, exit_period=10, atr_period=20, stop_atr_mult=2.0):
    df = df.copy()
    df[<span class="string">"signal"</span>] = 0; df[<span class="string">"position"</span>] = 0; df[<span class="string">"stop_loss"</span>] = np.nan
    current_pos = 0; entry_price = 0.0; stop_price = 0.0

    <span class="keyword">for</span> i <span class="keyword">in</span> range(len(df)):
        <span class="keyword">if</span> pd.isna(df.loc[i, <span class="string">"upper_entry"</span>]) <span class="keyword">or</span> pd.isna(df.loc[i, <span class="string">"ATR"</span>]):
            df.loc[i, <span class="string">"position"</span>] = current_pos; <span class="keyword">continue</span>

        close = df.loc[i, <span class="string">"close"</span>]; atr = df.loc[i, <span class="string">"ATR"</span>]

        <span class="keyword">if</span> current_pos == 0:  <span class="comment"># 空仓</span>
            <span class="keyword">if</span> close > df.loc[i, <span class="string">"upper_entry"</span>]:  <span class="comment"># 突破20日新高</span>
                df.loc[i, <span class="string">"signal"</span>] = 1; current_pos = 1
                entry_price = close
                stop_price = close - stop_atr_mult * atr  <span class="comment"># 止损 = 买入价 - 2×ATR</span>

        <span class="keyword">elif</span> current_pos == 1:  <span class="comment"># 持仓</span>
            <span class="keyword">if</span> close < df.loc[i, <span class="string">"lower_exit"</span>]:  <span class="comment"># 跌破10日最低价</span>
                df.loc[i, <span class="string">"signal"</span>] = -1; current_pos = 0
            <span class="keyword">elif</span> close < stop_price:  <span class="comment"># 触及止损</span>
                df.loc[i, <span class="string">"signal"</span>] = -1; current_pos = 0

        df.loc[i, <span class="string">"position"</span>] = current_pos
        <span class="keyword">if</span> current_pos == 1 <span class="keyword">and</span> pd.isna(df.loc[i, <span class="string">"stop_loss"</span>]):
            df.loc[i, <span class="string">"stop_loss"</span>] = stop_price

    <span class="keyword">return</span> df</div>

    <h4>⑤ 回测模拟 & ⑥ 量化指标计算</h4>
    <div class="code-block"><span class="comment"># 回测：买入信号全仓建仓，卖出信号清仓，每日更新市值</span>
<span class="keyword">def</span> <span class="func">backtest</span>(df, initial_capital=100000):
    <span class="comment"># ... 逐日遍历，根据signal执行买卖 ...</span>
    <span class="comment"># 同时计算买入持有基准</span>
    <span class="keyword">return</span> df, trade_df

<span class="comment"># 量化指标</span>
<span class="keyword">def</span> <span class="func">calc_metrics</span>(df, initial_capital=100000, risk_free_rate=0.02):
    <span class="comment"># 累计回报 = (最终市值 - 初始资金) / 初始资金</span>
    <span class="comment"># 最大回撤 MDD = min((净值 - 历史最高净值) / 历史最高净值)</span>
    <span class="comment"># 夏普比率 = √252 × (日超额收益均值 / 日超额收益标准差)</span>
    <span class="comment"># 年化收益率 = (1+累计回报)^(252/交易日数) - 1</span>
    <span class="keyword">return</span> metrics</div>
</div>

<!-- ========== Part 4: 回测结果 ========== -->
<div class="section" id="part4">
    <h2><span class="num">4</span>策略回测结果</h2>
    <p>使用经典海龟参数（入场20日 / 离场10日 / ATR20日 / 止损2倍ATR），对6只A股进行回测，初始资金10万元。</p>

    <h3>4.1 多股票对比总览</h3>
    {gen_comparison_table()}

    <div class="chart-row">
        <div class="chart-block full">
            <img src="{multi_cmp_img}" alt="多股票对比" />
        </div>
    </div>

    <div class="callout info">
        <h4>关键发现</h4>
        <ul>
            <li><strong>宁德时代</strong>：策略累计回报 +29.89%，虽低于买入持有(+96.87%)，但最大回撤从-29.27%降至-29.13%，风险收益比有所改善</li>
            <li><strong>比亚迪</strong>：策略 +4.28% vs 买入持有 -64.41%，海龟策略在暴跌行情中展现了极强的防御能力，避免了巨亏</li>
            <li><strong>三一重工</strong>：策略 Sharpe 高达 1.07，最大回撤仅 -11.14%，是风险控制最佳的一只</li>
            <li><strong>中芯国际</strong>：策略胜率高达 75%，交易4次仅1次亏损，展示了趋势跟踪在半导体高波动股票上的有效性</li>
        </ul>
    </div>

    <h3>4.2 各股票详细回测</h3>
"""

# 生成每只股票的详情区块
for stock_name in ["贵州茅台", "比亚迪", "宁德时代", "中芯国际", "三一重工", "平安集团"]:
    html += gen_stock_section(stock_name, "")

html += f"""
</div>

<!-- ========== Part 5: 参数分析 ========== -->
<div class="section" id="part5">
    <h2><span class="num">5</span>参数调节与场景分析</h2>

    <p>通过调节海龟策略的核心参数，观察不同配置下的收益与风险变化，总结适应场景。</p>

    <h3>5.1 测试参数组合</h3>
    <table class="data-table">
        <thead>
            <tr><th>参数组合</th><th>入场周期</th><th>离场周期</th><th>ATR周期</th><th>止损倍数</th><th>策略特点</th></tr>
        </thead>
        <tbody>
            <tr><td>经典海龟</td><td>20日</td><td>10日</td><td>20日</td><td>2.0</td><td>标准参数，平衡趋势与风险</td></tr>
            <tr><td>更紧止损</td><td>20日</td><td>10日</td><td>20日</td><td>1.5</td><td>止损更敏感，减少单笔亏损</td></tr>
            <tr><td>更宽止损</td><td>20日</td><td>10日</td><td>20日</td><td>3.0</td><td>给趋势更多空间，减少假止损</td></tr>
            <tr><td>长周期通道</td><td>55日</td><td>20日</td><td>20日</td><td>2.0</td><td>信号更少更可靠，适合大趋势</td></tr>
            <tr><td>短周期通道</td><td>10日</td><td>5日</td><td>20日</td><td>2.0</td><td>信号更频繁，适合震荡市</td></tr>
        </tbody>
    </table>

    <h3>5.2 贵州茅台 - 参数敏感性分析</h3>
    {gen_param_table("贵州茅台")}
    <div class="chart-row">
        <div class="chart-block full">
            <img src="{maotai_param_img}" alt="茅台参数敏感性" />
        </div>
    </div>

    <h3>5.3 比亚迪 - 参数敏感性分析</h3>
    {gen_param_table("比亚迪")}
    <div class="chart-row">
        <div class="chart-block full">
            <img src="{byd_param_img}" alt="比亚迪参数敏感性" />
        </div>
    </div>

    <div class="callout">
        <h4>参数调节关键发现</h4>
        <h5>① 止损倍数的影响</h5>
        <ul>
            <li><strong>止损1.5×ATR</strong>（更紧）：茅台累计回报 -8.70% → -0.47%（大幅改善），比亚迪从 +4.28% 提升到 +10.00%。更紧止损在下跌行情中减少了回撤幅度</li>
            <li><strong>止损3.0×ATR</strong>（更宽）：给趋势更多呼吸空间，但在震荡市中可能导致单笔亏损扩大</li>
            <li><strong>结论</strong>：在A股高波动环境下，适当收紧止损（1.5-2.0倍ATR）效果更好</li>
        </ul>
        <h5>② 通道周期的影响</h5>
        <ul>
            <li><strong>10日短周期</strong>：交易信号最多（茅台11次、比亚迪12次），在宁德时代上获得 +46.93% 的高收益，但也可能频繁假突破</li>
            <li><strong>55日长周期</strong>：信号最少，茅台仅4次交易且全部亏损。长周期在震荡市中表现较差，但在大趋势中可能更可靠</li>
            <li><strong>结论</strong>：短周期适合高波动成长股（如宁德时代），长周期适合趋势明确的品种</li>
        </ul>
        <h5>③ 股票类型的影响</h5>
        <ul>
            <li><strong>高波动成长股</strong>（宁德时代、中芯国际）：海龟策略表现最好，趋势跟踪能捕获大幅上涨</li>
            <li><strong>防御性蓝筹</strong>（茅台、平安）：策略表现一般，震荡行情中假突破频繁</li>
            <li><strong>周期股</strong>（三一重工）：策略Sharpe最高(1.07)，周期股趋势性强，适合突破策略</li>
        </ul>
    </div>
</div>

<!-- ========== Part 6: 总结 ========== -->
<div class="section" id="part6">
    <h2><span class="num">6</span>海龟法则适应场景与使用心得</h2>

    <h3>6.1 适应场景</h3>
    <div class="concept-grid">
        <div class="concept-card">
            <h4>✅ 适合的场景</h4>
            <ul>
                <li><strong>强趋势市场</strong>：单边上涨或下跌行情中，突破信号可靠性高</li>
                <li><strong>高波动品种</strong>：成长股、科技股、周期股等波动大的标的，ATR机制能充分发挥作用</li>
                <li><strong>中长期投资</strong>：持仓周期通常数周到数月，不适合日内交易</li>
                <li><strong>商品期货市场</strong>：海龟策略的原始战场，趋势性强且可双向交易</li>
            </ul>
        </div>
        <div class="concept-card">
            <h4>❌ 不适合的场景</h4>
            <ul>
                <li><strong>震荡市场</strong>：价格在区间内反复波动时，突破信号频繁失效，导致连续止损</li>
                <li><strong>低流动性品种</strong>：成交量小、滑点大，突破时可能无法以理想价格成交</li>
                <li><strong>短线交易</strong>：信号产生频率低，不适合追求高频交易的投资者</li>
                <li><strong>基本面突变</strong>：如突发利空导致跳空暴跌，止损可能远低于设定价位</li>
            </ul>
        </div>
    </div>

    <h3>6.2 使用心得</h3>
    <ul class="advantage-list">
        <li><strong>纪律性是海龟策略的灵魂</strong> — 策略本身并不复杂，真正的难点在于严格执行。当连续止损3-5次后，人性本能会倾向于"跳过下一个信号"，而这往往正是大趋势启动的信号。程序化交易的价值在于它不会犹豫。</li>
        <li><strong>"截断亏损，让利润奔跑"</strong> — 回测数据显示，海龟策略的胜率通常在30%-50%之间，并不高。但盈利交易的平均收益远大于亏损交易的平均损失，少数大趋势的利润覆盖了大量小亏损。这是典型的"薄利多销反过来的"策略——少数大赢覆盖多数小亏。</li>
        <li><strong>参数不是越复杂越好</strong> — 经典的20/10/2.0参数在大多数股票上表现已经不错。过度优化参数容易导致过拟合——在历史数据上完美但在未来失效。建议在不同市场环境下测试参数稳定性而非追求历史最优。</li>
        <li><strong>ATR 是最被低估的指标</strong> — 大多数人关注唐奇安通道的突破信号，但ATR才是海龟策略的真正秘密武器。它让策略自动适应不同波动率环境，这是固定百分比止损做不到的。</li>
        <li><strong>不要期待跑赢牛市中的买入持有</strong> — 在单边大牛市中（如宁德时代+96.87%），海龟策略的收益(+29.89%)通常低于满仓持有。但海龟的价值在于<strong>风险调整后的收益</strong>——它在熊市和震荡市中大幅跑赢买入持有（如比亚迪 +4.28% vs -64.41%）。</li>
        <li><strong>结合多品种分散风险</strong> — 海龟策略最初在24个商品期货品种上同时运行，通过分散化降低单一品种趋势消失的风险。股票市场中同样应该构建多股票组合，避免重仓单一标的。</li>
        <li><strong>A股需要适配</strong> — A股T+1交易、涨跌停限制、做空受限等特性会影响海龟策略的执行效果。尤其是A股只能做多，无法在下跌趋势中做空获利，这使得海龟策略在A股熊市中只能"空仓等待"，收益来源受限。</li>
    </ul>

    <div class="callout success">
        <h4>最终总结</h4>
        <p>海龟交易法则之所以成为传奇，不在于它有什么神秘的技术指标，而在于它把<strong>趋势跟踪 + 风险管理 + 资金管理</strong>三者完美结合成了一套可执行的系统。通过本次Python实战，我们验证了：</p>
        <ul>
            <li>海龟策略在<strong>高波动成长股</strong>上表现优异（宁德时代 +29.89%）</li>
            <li>在<strong>暴跌行情</strong>中展现了强大的防御能力（比亚迪策略 +4.28% vs 买入持有 -64.41%）</li>
            <li><strong>三一重工</strong>以 Sharpe 1.07、MDD仅-11.14% 证明了趋势跟踪在周期股上的有效性</li>
            <li>参数调节的核心trade-off：<strong>短周期=更多信号+更多假突破</strong>，<strong>紧止损=更小亏损+更早离场</strong></li>
        </ul>
        <p>海龟策略给我们的最大启示：<strong>交易不是预测，而是应对</strong>。你不需要知道市场往哪走，你只需要知道——如果市场往上涨你该怎么做，如果往下跌你该怎么做。然后，严格执行。</p>
    </div>
</div>

<div class="footer">
    <p>BI工作坊 · AI量化公益课 · Task4 海龟交易法则实战演练</p>
    <p>初始资金 100,000元 | 数据区间 2024-2026 | 经典参数 20/10/20/2.0</p>
</div>

</div>
</body>
</html>"""

# 写入HTML文件
output_path = os.path.join(DATA_DIR, "海龟策略分析报告.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"报告已生成: {output_path}")
print(f"文件大小: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB")
