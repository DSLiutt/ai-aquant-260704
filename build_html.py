import json
import pandas as pd

# 读取CSV数据
csv_path = "/Users/liutt/Documents/AI 2026/Workbuddy/BI工作坊-ai量化公益课/中芯国际_688981_日线数据.csv"
df = pd.read_csv(csv_path)

# 格式化日期 YYYYMMDD -> YYYY-MM-DD
df["trade_date"] = df["trade_date"].astype(str).str.strip()
df["date_fmt"] = df["trade_date"].apply(lambda x: f"{x[:4]}-{x[4:6]}-{x[6:8]}")

# 构建K线数据 [date, open, close, low, high]
kline_data = []
vol_data = []
for _, row in df.iterrows():
    date = row["date_fmt"]
    o = float(row["open"])
    c = float(row["close"])
    low = float(row["low"])
    high = float(row["high"])
    vol = float(row["vol"])
    kline_data.append([date, o, c, low, high])
    # 成交量颜色: 收盘>=开盘为红(涨), 否则绿(跌)
    color = "#ef232a" if c >= o else "#14b143"
    vol_data.append({"value": vol, "itemStyle": {"color": color}})

# 计算统计数据
latest = df.iloc[-1]
first = df.iloc[0]
year_high = df["high"].max()
year_low = df["low"].min()
avg_vol = df["vol"].mean()
total_return = ((float(latest["close"]) - float(first["close"])) / float(first["close"])) * 100

# 生成MA线数据
ma5 = df["close"].rolling(5).mean().tolist()
ma10 = df["close"].rolling(10).mean().tolist()
ma20 = df["close"].rolling(20).mean().tolist()
ma60 = df["close"].rolling(60).mean().tolist()

dates = df["date_fmt"].tolist()

# 转为JSON嵌入HTML
kline_json = json.dumps(kline_data, ensure_ascii=False)
vol_json = json.dumps(vol_data, ensure_ascii=False)
dates_json = json.dumps(dates, ensure_ascii=False)
ma5_json = json.dumps([None if pd.isna(v) else round(v, 2) for v in ma5])
ma10_json = json.dumps([None if pd.isna(v) else round(v, 2) for v in ma10])
ma20_json = json.dumps([None if pd.isna(v) else round(v, 2) for v in ma20])
ma60_json = json.dumps([None if pd.isna(v) else round(v, 2) for v in ma60])

html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中芯国际 (688981.SH) K线行情面板</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: #f5f6fa;
            color: #2d3436;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 20px;
            color: #fff;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .header .subtitle {{
            font-size: 14px;
            color: #a0a3bd;
        }}
        .header .code {{
            display: inline-block;
            background: rgba(255,255,255,0.12);
            padding: 3px 12px;
            border-radius: 6px;
            font-size: 13px;
            margin-left: 10px;
            font-family: "SF Mono", "Fira Code", monospace;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #fff;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
        .stat-card .label {{
            font-size: 12px;
            color: #9c9c9c;
            margin-bottom: 6px;
            font-weight: 500;
        }}
        .stat-card .value {{
            font-size: 22px;
            font-weight: 700;
            font-family: "SF Mono", "Fira Code", monospace;
        }}
        .stat-card .change {{
            font-size: 13px;
            margin-top: 4px;
        }}
        .up {{ color: #ef232a; }}
        .down {{ color: #14b143; }}
        .chart-container {{
            background: #fff;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            margin-bottom: 20px;
        }}
        .chart-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .chart-title::before {{
            content: '';
            display: inline-block;
            width: 4px;
            height: 16px;
            background: #0984e3;
            border-radius: 2px;
        }}
        #klineChart {{ width: 100%; height: 520px; }}
        #volChart {{ width: 100%; height: 200px; }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #b2bec3;
            padding: 16px 0;
        }}
        .legend-info {{
            display: flex;
            gap: 20px;
            margin-top: 8px;
            font-size: 12px;
            color: #636e72;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>中芯国际 K线行情面板<span class="code">688981.SH</span></h1>
        <p class="subtitle">数据周期: {dates[0]} 至 {dates[-1]} · 数据来源: Tushare · 共 {len(df)} 个交易日</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">最新收盘价</div>
            <div class="value">¥{float(latest["close"]):.2f}</div>
            <div class="change {'up' if float(latest['pct_chg']) >= 0 else 'down'}">
                {float(latest["pct_chg"]):+.2f}% ({'↑' if float(latest['change']) >= 0 else '↓'}{abs(float(latest['change'])):.2f})
            </div>
        </div>
        <div class="stat-card">
            <div class="label">近一年涨跌幅</div>
            <div class="value {'up' if total_return >= 0 else 'down'}">{total_return:+.2f}%</div>
            <div class="change" style="color:#9c9c9c;">起价 ¥{float(first["close"]):.2f} → 终价 ¥{float(latest["close"]):.2f}</div>
        </div>
        <div class="stat-card">
            <div class="label">一年最高价</div>
            <div class="value up">¥{year_high:.2f}</div>
            <div class="change" style="color:#9c9c9c;">区间高点</div>
        </div>
        <div class="stat-card">
            <div class="label">一年最低价</div>
            <div class="value down">¥{year_low:.2f}</div>
            <div class="change" style="color:#9c9c9c;">区间低点</div>
        </div>
        <div class="stat-card">
            <div class="label">日均成交量</div>
            <div class="value">{avg_vol/10000:.1f}<span style="font-size:13px;color:#9c9c9c;">万手</span></div>
            <div class="change" style="color:#9c9c9c;">最新: {float(latest['vol'])/10000:.1f}万手</div>
        </div>
        <div class="stat-card">
            <div class="label">最新成交额</div>
            <div class="value">{float(latest["amount"])/100000:.2f}<span style="font-size:13px;color:#9c9c9c;">亿元</span></div>
            <div class="change" style="color:#9c9c9c;">换手活跃</div>
        </div>
    </div>

    <div class="chart-container">
        <div class="chart-title">日K线走势</div>
        <div class="legend-info">
            <div class="legend-item"><span class="legend-dot" style="background:#ef232a;"></span>阳线(收涨)</div>
            <div class="legend-item"><span class="legend-dot" style="background:#14b143;"></span>阴线(收跌)</div>
            <div class="legend-item"><span class="legend-dot" style="background:#f5a623;"></span>MA5</div>
            <div class="legend-item"><span class="legend-dot" style="background:#0984e3;"></span>MA10</div>
            <div class="legend-item"><span class="legend-dot" style="background:#a55eea;"></span>MA20</div>
            <div class="legend-item"><span class="legend-dot" style="background:#26de81;"></span>MA60</div>
        </div>
        <div id="klineChart"></div>
    </div>

    <div class="chart-container">
        <div class="chart-title">成交量</div>
        <div id="volChart"></div>
    </div>

    <div class="footer">数据来源: Tushare Pro · 仅供学习参考，不构成投资建议 · 生成时间: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}</div>

    <script>
        var dates = {dates_json};
        var klineData = {kline_json};
        var volData = {vol_json};
        var ma5 = {ma5_json};
        var ma10 = {ma10_json};
        var ma20 = {ma20_json};
        var ma60 = {ma60_json};

        // K线图
        var klineChart = echarts.init(document.getElementById('klineChart'));
        var klineOption = {{
            backgroundColor: 'transparent',
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'cross' }},
                backgroundColor: 'rgba(26,26,46,0.9)',
                borderColor: '#333',
                textStyle: {{ color: '#fff', fontSize: 12 }},
                formatter: function(params) {{
                    var d = params[0].axisValue;
                    var html = '<div style="font-weight:600;margin-bottom:4px;">' + d + '</div>';
                    var k;
                    params.forEach(function(p) {{
                        if (p.seriesName === '日K') {{
                            k = p.data.slice(1);
                            var color = k[1] >= k[0] ? '#ef232a' : '#14b143';
                            html += '<div style="color:' + color + '">开 ' + k[0].toFixed(2) + '</div>';
                            html += '<div style="color:' + color + '">收 ' + k[1].toFixed(2) + '</div>';
                            html += '<div style="color:#aaa">低 ' + k[2].toFixed(2) + '</div>';
                            html += '<div style="color:#aaa">高 ' + k[3].toFixed(2) + '</div>';
                        }} else if (p.value !== null && p.value !== undefined) {{
                            html += '<div><span style="color:' + p.color + '">●</span> ' + p.seriesName + ': ' + p.value.toFixed(2) + '</div>';
                        }}
                    }});
                    return html;
                }}
            }},
            grid: [{{ left: '6%', right: '3%', top: '4%', height: '88%' }}],
            xAxis: {{
                type: 'category',
                data: dates,
                boundaryGap: true,
                axisLine: {{ lineStyle: {{ color: '#dfe4ea' }} }},
                axisLabel: {{ color: '#9c9c9c', fontSize: 11 }},
                splitLine: {{ show: false }}
            }},
            yAxis: {{
                type: 'value',
                scale: true,
                axisLine: {{ show: false }},
                axisLabel: {{ color: '#9c9c9c', fontSize: 11, formatter: function(v) {{ return '¥' + v.toFixed(0); }} }},
                splitLine: {{ lineStyle: {{ color: '#f0f0f0' }} }}
            }},
            dataZoom: [
                {{ type: 'inside', start: 0, end: 100 }},
                {{ type: 'slider', start: 0, end: 100, height: 20, bottom: 5, borderColor: '#e0e0e0', fillerColor: 'rgba(9,132,227,0.1)', handleStyle: {{ color: '#0984e3' }} }}
            ],
            series: [
                {{
                    name: '日K',
                    type: 'candlestick',
                    data: klineData,
                    itemStyle: {{
                        color: '#ef232a',
                        color0: '#14b143',
                        borderColor: '#ef232a',
                        borderColor0: '#14b143'
                    }}
                }},
                {{ name: 'MA5', type: 'line', data: ma5, smooth: true, symbol: 'none', lineStyle: {{ color: '#f5a623', width: 1.5 }} }},
                {{ name: 'MA10', type: 'line', data: ma10, smooth: true, symbol: 'none', lineStyle: {{ color: '#0984e3', width: 1.5 }} }},
                {{ name: 'MA20', type: 'line', data: ma20, smooth: true, symbol: 'none', lineStyle: {{ color: '#a55eea', width: 1.5 }} }},
                {{ name: 'MA60', type: 'line', data: ma60, smooth: true, symbol: 'none', lineStyle: {{ color: '#26de81', width: 1.5 }} }}
            ]
        }};
        klineChart.setOption(klineOption);

        // 成交量图
        var volChart = echarts.init(document.getElementById('volChart'));
        var volOption = {{
            backgroundColor: 'transparent',
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }},
                backgroundColor: 'rgba(26,26,46,0.9)',
                borderColor: '#333',
                textStyle: {{ color: '#fff', fontSize: 12 }},
                formatter: function(params) {{
                    var d = params[0].axisValue;
                    var v = params[0].data.value;
                    return '<div style="font-weight:600;">' + d + '</div><div>成交量: ' + (v / 10000).toFixed(1) + ' 万手</div>';
                }}
            }},
            grid: [{{ left: '6%', right: '3%', top: '8%', height: '70%' }}],
            xAxis: {{
                type: 'category',
                data: dates,
                boundaryGap: true,
                axisLine: {{ lineStyle: {{ color: '#dfe4ea' }} }},
                axisLabel: {{ color: '#9c9c9c', fontSize: 11 }},
                splitLine: {{ show: false }}
            }},
            yAxis: {{
                type: 'value',
                axisLine: {{ show: false }},
                axisLabel: {{
                    color: '#9c9c9c', fontSize: 11,
                    formatter: function(v) {{ return (v / 10000).toFixed(0) + '万'; }}
                }},
                splitLine: {{ lineStyle: {{ color: '#f0f0f0' }} }}
            }},
            dataZoom: [
                {{ type: 'inside', start: 0, end: 100 }},
                {{ type: 'slider', start: 0, end: 100, height: 20, bottom: 5, borderColor: '#e0e0e0', fillerColor: 'rgba(9,132,227,0.1)', handleStyle: {{ color: '#0984e3' }} }}
            ],
            series: [{{
                name: '成交量',
                type: 'bar',
                data: volData,
                barWidth: '60%'
            }}]
        }};
        volChart.setOption(volOption);

        // 联动
        echarts.connect([klineChart, volChart]);

        // 响应式
        window.addEventListener('resize', function() {{
            klineChart.resize();
            volChart.resize();
        }});
    </script>
</body>
</html>'''

output_html = "/Users/liutt/Documents/AI 2026/Workbuddy/BI工作坊-ai量化公益课/中芯国际_K线面板.html"
with open(output_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML面板已生成: {output_html}")
print(f"数据范围: {dates[0]} 至 {dates[-1]}")
print(f"K线数据点: {len(kline_data)}")
print(f"近一年涨跌幅: {total_return:+.2f}%")
