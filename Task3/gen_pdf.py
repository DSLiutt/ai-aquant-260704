"""
生成双均线策略分析报告 PDF
使用 fpdf2 + 已生成的图表
"""
import os
import csv
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = os.path.join(BASE_DIR, "charts")
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

# 读取回测结果
results = []
with open(os.path.join(BASE_DIR, "回测结果汇总.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        results.append(row)

# 按夏普比率排序找出最优
best = max(results, key=lambda x: float(x["sharpe_ratio"]))


class PDF(FPDF):
    """自定义PDF类，支持中文字体"""
    
    def __init__(self):
        super().__init__()
        self.add_font("Unicode", "", FONT_PATH)
        self.add_font("Unicode", "B", FONT_PATH)  # fpdf2 will simulate bold
        self.set_auto_page_break(auto=True, margin=20)
    
    def header(self):
        if self.page_no() > 1:
            self.set_font("Unicode", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, "双均线策略量化分析报告 — BI工作坊 AI量化公益课 Task3", align="R")
            self.ln(5)
            self.set_draw_color(200, 200, 200)
            self.line(10, 18, 200, 18)
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Unicode", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"第 {self.page_no()} 页", align="C")
    
    def section_title(self, title, level=1):
        """添加章节标题"""
        self.set_font("Unicode", "B", 16 if level == 1 else 13)
        self.set_text_color(26, 26, 46)
        if level == 1:
            self.ln(5)
            self.set_fill_color(240, 242, 245)
            self.cell(0, 12, title, fill=True, border=0)
            self.ln(8)
        else:
            self.ln(3)
            self.cell(0, 8, title)
            self.ln(6)
    
    def body_text(self, text, size=10):
        """添加正文"""
        self.set_font("Unicode", "", size)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)
    
    def key_value(self, key, value, color=None):
        """添加键值对"""
        self.set_font("Unicode", "", 10)
        self.set_text_color(51, 51, 51)
        self.cell(60, 6, key)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(26, 26, 46)
        self.set_font("Unicode", "B", 10)
        self.cell(0, 6, value)
        self.ln(7)
    
    def add_image_safe(self, path, w=180):
        """安全添加图片"""
        if os.path.exists(path):
            remaining = self.h - self.get_y() - 25
            if remaining < 60:
                self.add_page()
            img_h = w * 0.6  # 估算高度
            if img_h > remaining:
                w = w * (remaining / img_h) * 0.95
            self.image(path, x=(210-w)/2, w=w)
            self.ln(3)
        else:
            self.body_text(f"[图片缺失: {os.path.basename(path)}]")


pdf = PDF()
pdf.set_title("双均线策略量化分析报告")
pdf.set_author("BI工作坊 AI量化公益课")

# ==================== 封面 ====================
pdf.add_page()
pdf.ln(50)
pdf.set_font("Unicode", "B", 28)
pdf.set_text_color(26, 26, 46)
pdf.cell(0, 15, "双均线交叉策略", align="C")
pdf.ln(18)
pdf.set_font("Unicode", "B", 20)
pdf.set_text_color(15, 52, 96)
pdf.cell(0, 12, "量化分析报告", align="C")
pdf.ln(25)

pdf.set_draw_color(37, 99, 235)
pdf.set_line_width(0.8)
pdf.line(60, pdf.get_y(), 150, pdf.get_y())
pdf.ln(10)

pdf.set_font("Unicode", "", 13)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, "BI工作坊 · AI量化公益课 Task3", align="C")
pdf.ln(8)
pdf.cell(0, 8, "双均线策略概念解析 · 信号生成 · 回测模拟 · 多股票多参数对比", align="C")
pdf.ln(20)

# 关键指标摘要
pdf.set_fill_color(240, 242, 245)
pdf.rect(40, pdf.get_y(), 130, 55, "F")
pdf.ln(5)
pdf.set_font("Unicode", "B", 11)
pdf.set_text_color(26, 26, 46)
pdf.cell(0, 7, "回测核心指标摘要", align="C")
pdf.ln(9)
pdf.set_font("Unicode", "", 10)
pdf.set_text_color(51, 51, 51)

summary_items = [
    ("测试股票数量", "6 只"),
    ("参数组合数量", "5 种"),
    ("总回测次数", "30 次"),
    ("最优组合", f"{best['stock']} {best['param']}"),
    ("最优夏普比率", f"{float(best['sharpe_ratio']):.2f}"),
    ("最优累计回报", f"{float(best['cumulative_return'])*100:+.2f}%"),
]
for k, v in summary_items:
    pdf.set_x(55)
    pdf.set_font("Unicode", "", 10)
    pdf.cell(50, 6, k)
    pdf.set_font("Unicode", "B", 10)
    pdf.set_text_color(224, 54, 77)
    pdf.cell(50, 6, v)
    pdf.ln(6)
    pdf.set_text_color(51, 51, 51)

pdf.ln(10)
pdf.set_font("Unicode", "", 9)
pdf.set_text_color(150, 150, 150)
pdf.cell(0, 5, "数据来源: Tushare API | 回测区间: 2024-2026 | 初始资金: ¥100,000", align="C")
pdf.ln(5)
pdf.cell(0, 5, "本报告仅供学习参考，不构成投资建议", align="C")

# ==================== 目录 ====================
pdf.add_page()
pdf.section_title("目录", 1)
pdf.ln(5)
toc_items = [
    "一、策略概念解析",
    "    1.1 双均线策略概述",
    "    1.2 金叉与死叉",
    "    1.3 常用均线周期组合",
    "二、量化指标说明",
    "    2.1 累计回报 (Cumulative Return)",
    "    2.2 最大回撤 (MDD)",
    "    2.3 夏普比率 (Sharpe Ratio)",
    "三、策略实现与回测",
    "    3.1 数据加载",
    "    3.2 均线计算与信号生成",
    "    3.3 策略可视化",
    "    3.4 回测模拟与量化指标",
    "四、多股票多参数对比分析",
    "五、策略适用场景与应用心得",
]
for item in toc_items:
    if item.startswith("    "):
        pdf.set_font("Unicode", "", 10)
        pdf.set_text_color(80, 80, 80)
    else:
        pdf.set_font("Unicode", "B", 11)
        pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 7, item)
    pdf.ln(7)

# ==================== 第一章 ====================
pdf.add_page()
pdf.section_title("一、策略概念解析")

pdf.section_title("1.1 双均线策略概述", 2)
pdf.body_text(
    "双均线策略（Dual Moving Average Strategy）是最经典的趋势跟踪型量化策略之一。"
    "它利用短期移动平均线和长期移动平均线的交叉关系来判断市场趋势的方向，并据此产生买卖信号。"
)
pdf.body_text(
    "核心逻辑：当短均线从下方穿越长均线向上时，意味着近期价格走势强于长期趋势，"
    "市场可能进入上升通道，产生买入信号；当短均线从上方穿越长均线向下时，"
    "意味着近期价格走势弱于长期趋势，市场可能进入下降通道，产生卖出信号。"
)

pdf.section_title("1.2 金叉与死叉", 2)
pdf.body_text(
    "金叉（Golden Cross）：短周期均线从下方穿越长周期均线向上。"
    "表示短期价格上涨动能增强，突破长期均价，通常被视为看涨买入信号。"
    "金叉出现意味着市场多头力量开始占主导地位。"
)
pdf.body_text(
    "死叉（Death Cross）：短周期均线从上方穿越长周期均线向下。"
    "表示短期价格下跌动能增强，跌破长期均价，通常被视为看跌卖出信号。"
    "死叉出现意味着市场空头力量开始占主导地位。"
)

pdf.section_title("1.3 常用均线周期组合", 2)
combos = [
    ["组合", "短均线", "长均线", "特点"],
    ["5/15", "5日", "15日", "灵敏度高，信号频繁，适合短线"],
    ["5/20", "5日", "20日", "平衡型，适中灵敏度"],
    ["10/20", "10日", "20日", "中线常用，信号较稳定"],
    ["10/30", "10日", "30日", "滞后性较强，适合中长线"],
    ["5/30", "5日", "30日", "大跨度，信号少但趋势性强"],
]
pdf.set_font("Unicode", "", 9)
pdf.set_fill_color(240, 242, 245)
for i, row in enumerate(combos):
    if i == 0:
        pdf.set_font("Unicode", "B", 9)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
    else:
        pdf.set_font("Unicode", "", 9)
        pdf.set_text_color(51, 51, 51)
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
    col_widths = [25, 25, 25, 115]
    for j, (cell_text, w) in enumerate(zip(row, col_widths)):
        pdf.cell(w, 7, cell_text, border=1, fill=True)
    pdf.ln(7)

# ==================== 第二章 ====================
pdf.add_page()
pdf.section_title("二、量化指标说明")

pdf.section_title("2.1 累计回报 (Cumulative Return)", 2)
pdf.body_text("公式: CR = (V_final - V_initial) / V_initial")
pdf.body_text(
    "累计回报是策略从开始到结束的总收益率，是最直观的收益衡量指标。"
    "V_final为期末总资产价值，V_initial为期初投入资金。"
    "CR > 0表示盈利，CR < 0表示亏损。但仅看累计回报无法衡量风险。"
)

pdf.section_title("2.2 最大回撤 (Maximum Drawdown, MDD)", 2)
pdf.body_text("公式: MDD = min((V_t - max(V_s<=t)) / max(V_s<=t))")
pdf.body_text(
    "最大回撤是从历史最高点到后续最低点的最大跌幅，衡量策略可能面临的最严重亏损。"
    "MDD越小（绝对值越小）越好。"
    "关键认识：跌20%需要涨25%才能回本，跌50%需要涨100%才能回本。"
    "最大回撤是评估策略风险承受能力的重要指标。"
)

pdf.section_title("2.3 夏普比率 (Sharpe Ratio)", 2)
pdf.body_text("公式: Sharpe = sqrt(252) * (R_daily_mean - Rf_daily) / R_daily_std")
pdf.body_text(
    "夏普比率衡量单位风险下的超额回报，是风险调整后的收益指标。"
    "R_daily_mean为日收益率均值，Rf_daily为日无风险利率（年化2%/252天），"
    "R_daily_std为日收益率标准差，sqrt(252)为年化因子。"
)
pdf.body_text("解读标准：")
sharpe_table = [
    ["Sharpe", "评级", "说明"],
    ["< 0", "亏损", "策略不可行，收益低于无风险利率"],
    ["0 ~ 0.5", "较差", "风险补偿不足"],
    ["0.5 ~ 1.0", "一般", "可接受，但不够理想"],
    ["1.0 ~ 2.0", "良好", "风险调整后收益不错"],
    ["> 2.0", "优秀", "极具吸引力"],
]
pdf.set_font("Unicode", "", 9)
for i, row in enumerate(sharpe_table):
    if i == 0:
        pdf.set_font("Unicode", "B", 9)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
    else:
        pdf.set_font("Unicode", "", 9)
        pdf.set_text_color(51, 51, 51)
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
    col_widths = [30, 30, 130]
    for cell_text, w in zip(row, col_widths):
        pdf.cell(w, 7, cell_text, border=1, fill=True)
    pdf.ln(7)

# ==================== 第三章 ====================
pdf.add_page()
pdf.section_title("三、策略实现与回测")

pdf.section_title("3.1 数据加载", 2)
pdf.body_text(
    "本次回测使用6只不同行业、不同特性的A股股票数据，"
    "涵盖半导体、工程机械、金融保险、白酒、新能源等板块。"
    "数据通过Tushare API获取，包含日线OHLCV（开盘价、最高价、最低价、收盘价、成交量）信息。"
)
stocks_info = [
    ["股票", "代码", "行业", "数据特征"],
    ["中芯国际", "688981.SH", "半导体", "高波动，趋势性强"],
    ["三一重工", "600031.SH", "工程机械", "低波动，震荡为主"],
    ["平安集团", "000001.SZ", "保险银行", "大盘蓝筹，温和波动"],
    ["贵州茅台", "600519.SH", "白酒", "高价股，近年回调"],
    ["宁德时代", "300750.SZ", "新能源", "高成长，大幅波动"],
    ["比亚迪", "002594.SZ", "新能源汽车", "高波动，趋势反转"],
]
pdf.set_font("Unicode", "", 9)
for i, row in enumerate(stocks_info):
    if i == 0:
        pdf.set_font("Unicode", "B", 9)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
    else:
        pdf.set_font("Unicode", "", 9)
        pdf.set_text_color(51, 51, 51)
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
    col_widths = [30, 35, 35, 90]
    for cell_text, w in zip(row, col_widths):
        pdf.cell(w, 7, cell_text, border=1, fill=True)
    pdf.ln(7)

pdf.section_title("3.2 均线计算与信号生成", 2)
pdf.body_text(
    "使用pandas的rolling().mean()计算简单移动平均线（SMA）。"
    "信号生成逻辑：金叉（买入信号）为前一日短均线低于长均线且今日短均线高于长均线；"
    "死叉（卖出信号）为前一日短均线高于长均线且今日短均线低于长均线。"
)

pdf.section_title("3.3 策略可视化", 2)
pdf.body_text(
    "以中芯国际MA5/MA15为例，下图展示了股价走势、短长均线及买卖信号标记。"
    "红色三角形标记金叉买入点，绿色倒三角标记死叉卖出点，浅红色背景表示持仓区间。"
)
pdf.add_image_safe(os.path.join(CHART_DIR, "中芯国际_MA5_15_策略总览.png"), w=180)

pdf.add_page()
pdf.body_text("六只股票双均线策略信号对比（MA5/MA15）：")
# 显示各股票策略图（选3只代表性的）
for stock in ["中芯国际", "宁德时代", "三一重工"]:
    img_path = os.path.join(CHART_DIR, f"{stock}_MA5_15_策略总览.png")
    if os.path.exists(img_path):
        pdf.add_image_safe(img_path, w=170)

pdf.section_title("3.4 回测模拟与量化指标", 2)
pdf.body_text(
    "回测设定：初始资金¥100,000，金叉日以收盘价全仓买入，死叉日以收盘价全仓卖出。"
    "同时计算「买入持有」策略作为基准对比。"
)
pdf.body_text(
    "以中芯国际MA5/MA15为例，策略收益与买入持有的对比如下图所示。"
    "红色实线为双均线策略市值，蓝色虚线为买入持有市值。"
)
pdf.add_image_safe(os.path.join(CHART_DIR, "中芯国际_MA5_15_收益对比.png"), w=180)

pdf.add_page()
pdf.body_text("最大回撤对比如下图，红色区域为策略回撤，蓝色虚线为买入持有回撤：")
pdf.add_image_safe(os.path.join(CHART_DIR, "中芯国际_MA5_15_回撤.png"), w=180)

# 中芯国际MA5/15指标
pdf.ln(5)
pdf.section_title("中芯国际 MA5/MA15 回测结果", 2)
cr = float(best["cumulative_return"]) if best["stock"] == "中芯国际" else None
# 找到中芯国际MA5/MA15的结果
for r in results:
    if r["stock"] == "中芯国际" and r["param"] == "MA5/MA15":
        cr = float(r["cumulative_return"])
        mdd = float(r["max_drawdown"])
        sharpe = float(r["sharpe_ratio"])
        ar = float(r["annual_return"])
        bh_cr = float(r["bh_cumulative_return"])
        bh_mdd = float(r["bh_max_drawdown"])
        bh_sharpe = float(r["bh_sharpe_ratio"])
        buy_cnt = int(r["buy_count"])
        break

pdf.set_font("Unicode", "", 10)
pdf.set_text_color(51, 51, 51)
metrics_display = [
    ("初始资金", "¥100,000.00", (51, 51, 51)),
    ("期末市值", f"¥{100000*(1+cr):,.2f}", (26, 26, 46)),
    ("累计回报", f"{cr:+.2%}", (224, 54, 77) if cr >= 0 else (22, 163, 74)),
    ("年化收益率", f"{ar:+.2%}", (224, 54, 77) if ar >= 0 else (22, 163, 74)),
    ("最大回撤 (MDD)", f"{mdd:.2%}", (22, 163, 74)),
    ("夏普比率", f"{sharpe:.2f}", (37, 99, 235)),
    ("买入信号次数", f"{buy_cnt} 次", (51, 51, 51)),
    ("── 买入持有基准 ──", "", (150, 150, 150)),
    ("买入持有回报", f"{bh_cr:+.2%}", (224, 54, 77) if bh_cr >= 0 else (22, 163, 74)),
    ("买入持有MDD", f"{bh_mdd:.2%}", (22, 163, 74)),
    ("买入持有Sharpe", f"{bh_sharpe:.2f}", (37, 99, 235)),
]
for k, v, color in metrics_display:
    pdf.set_font("Unicode", "", 10)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(70, 7, k)
    if v:
        pdf.set_font("Unicode", "B", 10)
        pdf.set_text_color(*color)
        pdf.cell(0, 7, v)
    pdf.ln(7)

# ==================== 第四章 ====================
pdf.add_page()
pdf.section_title("四、多股票多参数对比分析")

pdf.body_text(
    "对6只股票分别使用5种均线参数组合进行回测，共30次回测。"
    "下图展示了各股票在不同参数下的累计回报和夏普比率对比。"
)
pdf.add_image_safe(os.path.join(CHART_DIR, "多股票参数对比.png"), w=185)

pdf.add_page()
pdf.body_text("策略收益 vs 买入持有散点对比图：")
pdf.add_image_safe(os.path.join(CHART_DIR, "策略vs买入持有散点.png"), w=160)

pdf.add_page()
pdf.body_text("各股票最大回撤（MDD）对比：")
pdf.add_image_safe(os.path.join(CHART_DIR, "MDD对比.png"), w=185)

# 完整结果表
pdf.add_page()
pdf.section_title("完整回测结果汇总表", 2)
pdf.set_font("Unicode", "", 7.5)
pdf.set_fill_color(37, 99, 235)
pdf.set_text_color(255, 255, 255)
headers = ["股票", "参数", "累计回报", "年化收益", "MDD", "Sharpe", "买入持有", "持有MDD", "持有Sharpe", "交易次数"]
col_w = [22, 22, 22, 20, 20, 18, 22, 20, 20, 14]
for h, w in zip(headers, col_w):
    pdf.cell(w, 6, h, border=1, fill=True, align="C")
pdf.ln(6)

for i, r in enumerate(results):
    if pdf.get_y() > 270:
        pdf.add_page()
        pdf.set_font("Unicode", "", 7.5)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        for h, w in zip(headers, col_w):
            pdf.cell(w, 6, h, border=1, fill=True, align="C")
        pdf.ln(6)
    
    pdf.set_font("Unicode", "", 7.5)
    pdf.set_text_color(51, 51, 51)
    if i % 2 == 0:
        pdf.set_fill_color(248, 249, 250)
    else:
        pdf.set_fill_color(255, 255, 255)
    
    cr_val = float(r["cumulative_return"]) * 100
    ar_val = float(r["annual_return"]) * 100
    mdd_val = float(r["max_drawdown"]) * 100
    sharpe_val = float(r["sharpe_ratio"])
    bh_cr_val = float(r["bh_cumulative_return"]) * 100
    bh_mdd_val = float(r["bh_max_drawdown"]) * 100
    bh_sharpe_val = float(r["bh_sharpe_ratio"])
    
    row_data = [
        r["stock"],
        r["param"],
        f"{cr_val:+.1f}%",
        f"{ar_val:+.1f}%",
        f"{mdd_val:.1f}%",
        f"{sharpe_val:.2f}",
        f"{bh_cr_val:+.1f}%",
        f"{bh_mdd_val:.1f}%",
        f"{bh_sharpe_val:.2f}",
        str(r["buy_count"]),
    ]
    for val, w in zip(row_data, col_w):
        pdf.cell(w, 5.5, val, border=1, fill=True, align="C")
    pdf.ln(5.5)

# ==================== 第五章 ====================
pdf.add_page()
pdf.section_title("五、策略适用场景与应用心得")

pdf.section_title("5.1 回测核心发现", 2)
findings = [
    ["发现", "说明"],
    ["趋势行情中表现优异", "中芯国际、宁德时代等强趋势股，策略收益可观(50%+)"],
    ["震荡行情中频繁假信号", "三一重工等横盘股，金叉死叉反复出现，导致亏损"],
    ["有效降低最大回撤", "多数情况下策略MDD优于买入持有，体现止损效果"],
    ["难以跑赢强牛市", "单边大涨行情中，频繁卖出导致错过涨幅"],
    ["长周期参数更稳健", "MA5/30等大跨度参数信号少但质量高"],
    ["短周期参数更灵敏", "MA5/15信号频繁，适合短线但需配合过滤"],
]
pdf.set_font("Unicode", "", 9)
for i, row in enumerate(findings):
    if i == 0:
        pdf.set_font("Unicode", "B", 9)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
    else:
        pdf.set_font("Unicode", "", 9)
        pdf.set_text_color(51, 51, 51)
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
    col_widths = [55, 125]
    for cell_text, w in zip(row, col_widths):
        pdf.cell(w, 7, cell_text, border=1, fill=True)
    pdf.ln(7)

pdf.section_title("5.2 适用场景", 2)
pdf.body_text("适合使用的场景：")
pdf.body_text(
    "1. 明显的趋势行情：股价持续上涨或下跌，均线能清晰反映趋势方向\n"
    "2. 中长线投资：持仓周期以周/月为单位，避免日内噪音干扰\n"
    "3. 高波动股票：波动越大，趋势越明显，策略捕捉能力越强\n"
    "4. 组合管理：作为多策略组合中的趋势跟踪组件"
)
pdf.body_text("不适合使用的场景：")
pdf.body_text(
    "1. 横盘震荡市场：价格在区间内反复波动，金叉死叉频繁但无趋势\n"
    "2. V型反转行情：均线滞后性大，反转信号来得太晚\n"
    "3. 高频交易：日内波动噪音大，均线信号不可靠\n"
    "4. 小盘低流动性股票：容易被均线信号误导"
)

pdf.section_title("5.3 参数选择心得", 2)
param_table = [
    ["参数特点", "适用场景", "优缺点"],
    ["短周期(5/15)", "短线交易、高波动股", "灵敏度高 / 假信号多"],
    ["中周期(10/20)", "中线、温和波动", "平衡稳健 / 两头不靠"],
    ["长周期(5/30,10/30)", "中长线、趋势确认", "信号可靠 / 滞后性大"],
]
pdf.set_font("Unicode", "", 9)
for i, row in enumerate(param_table):
    if i == 0:
        pdf.set_font("Unicode", "B", 9)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
    else:
        pdf.set_font("Unicode", "", 9)
        pdf.set_text_color(51, 51, 51)
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
    col_widths = [50, 55, 75]
    for cell_text, w in zip(row, col_widths):
        pdf.cell(w, 7, cell_text, border=1, fill=True)
    pdf.ln(7)

pdf.section_title("5.4 改进方向", 2)
pdf.body_text(
    "1. 多指标过滤：结合MACD、RSI、成交量等指标过滤假信号\n"
    "2. 动态止损：设置移动止损线，控制单笔亏损\n"
    "3. 仓位管理：根据信号强度调整仓位，而非全仓进出\n"
    "4. 市场状态识别：判断当前是趋势市还是震荡市，动态切换策略\n"
    "5. 多时间框架：结合日线和周线信号，提高判断准确性"
)

pdf.section_title("5.5 核心结论", 2)
pdf.set_fill_color(240, 248, 255)
pdf.set_draw_color(37, 99, 235)
pdf.set_font("Unicode", "B", 10)
pdf.set_text_color(26, 26, 46)
pdf.multi_cell(0, 7, 
    "双均线策略是一个简单但有效的趋势跟踪工具。它的价值不在于「万能盈利」，"
    "而在于用纪律化的规则替代情绪化决策——在趋势来临时果断入场，"
    "在趋势结束时及时止损。理解其「趋势市赚钱、震荡市亏钱」的本质特征，"
    "并在合适的场景中使用，才是量化策略的正确打开方式。",
    border=1, fill=True)

# ==================== 保存 ====================
output_path = os.path.join(BASE_DIR, "双均线策略分析报告.pdf")
pdf.output(output_path)
print(f"PDF报告已生成: {output_path}")
file_size = os.path.getsize(output_path) / 1024
print(f"文件大小: {file_size:.0f} KB")
print(f"总页数: {pdf.page_no()}")
