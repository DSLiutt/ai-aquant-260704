"""
生成双均线策略交互式可视化HTML页面
Vue 3 + ECharts
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 读取回测数据
with open(os.path.join(BASE_DIR, "backtest_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

json_str = json.dumps(data, ensure_ascii=False)

# 使用普通字符串模板 + replace 避免f-string花括号冲突
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>双均线策略量化分析 — BI工作坊 AI量化公益课</title>
<script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f0f2f5; color: #1a1a2e; }
#app { max-width: 1400px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white;
  border-radius: 16px; padding: 32px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
.header h1 { font-size: 28px; margin-bottom: 8px; }
.header .subtitle { font-size: 14px; opacity: 0.8; }
.header .tags { margin-top: 12px; }
.header .tag { display: inline-block; background: rgba(255,255,255,0.15); padding: 4px 12px;
  border-radius: 20px; font-size: 12px; margin-right: 8px; }
.controls { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px;
  display: flex; gap: 24px; align-items: center; flex-wrap: wrap; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.control-group { display: flex; align-items: center; gap: 8px; }
.control-group label { font-size: 14px; font-weight: 600; color: #555; white-space: nowrap; }
select { padding: 8px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px;
  cursor: pointer; transition: border-color 0.2s; outline: none; }
select:focus, select:hover { border-color: #2563eb; }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px; margin-bottom: 20px; }
.metric-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  position: relative; overflow: hidden; transition: transform 0.2s; }
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.metric-card .label { font-size: 12px; color: #888; margin-bottom: 6px; }
.metric-card .value { font-size: 28px; font-weight: 700; }
.metric-card .sub { font-size: 12px; margin-top: 4px; }
.metric-card .icon { position: absolute; top: 16px; right: 16px; font-size: 24px; opacity: 0.15; }
.positive { color: #e0364d; }
.negative { color: #16a34a; }
.neutral { color: #2563eb; }
.chart-card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #1a1a2e;
  display: flex; align-items: center; gap: 8px; }
.chart-card h3::before { content: ""; width: 4px; height: 20px; background: #2563eb; border-radius: 2px; }
.chart-container { width: 100%; }
.table-card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow-x: auto; }
.table-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #1a1a2e;
  display: flex; align-items: center; gap: 8px; }
.table-card h3::before { content: ""; width: 4px; height: 20px; background: #7c3aed; border-radius: 2px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #f8f9fa; padding: 10px 12px; text-align: left; font-weight: 600;
  color: #555; border-bottom: 2px solid #e0e0e0; white-space: nowrap; }
td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
tr:hover { background: #f8f9fa; }
.best-row { background: #fff3cd !important; }
.best-badge { display: inline-block; background: #f59e0b; color: white; padding: 2px 8px;
  border-radius: 4px; font-size: 11px; margin-left: 4px; }
.concept-card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.concept-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #1a1a2e;
  display: flex; align-items: center; gap: 8px; }
.concept-card h3::before { content: ""; width: 4px; height: 20px; background: #16a34a; border-radius: 2px; }
.concept-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.concept-item { padding: 16px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #2563eb; }
.concept-item h4 { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #1a1a2e; }
.concept-item p { font-size: 13px; line-height: 1.6; color: #555; }
.concept-item .formula { background: #1a1a2e; color: #4ade80; padding: 8px 12px; border-radius: 6px;
  font-family: "Courier New", monospace; font-size: 12px; margin: 8px 0; }
.footer { text-align: center; padding: 24px; color: #888; font-size: 13px; }
@media (max-width: 768px) {
  .controls { flex-direction: column; align-items: stretch; }
  .metric-card .value { font-size: 22px; }
}
</style>
</head>
<body>
<div id="app">
  <div class="header">
    <h1>双均线交叉策略 — 量化分析看板</h1>
    <div class="subtitle">BI工作坊 · AI量化公益课 Task3 | 双均线策略回测与多股票多参数对比分析</div>
    <div class="tags">
      <span class="tag">Vue 3</span>
      <span class="tag">ECharts 5</span>
      <span class="tag">{{ stockCount }} 只股票</span>
      <span class="tag">{{ paramCount }} 种参数组合</span>
      <span class="tag">{{ totalBacktests }} 次回测</span>
    </div>
  </div>

  <div class="controls">
    <div class="control-group">
      <label>选择股票:</label>
      <select v-model="selectedStock" @change="updateCharts">
        <option v-for="s in stockNames" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    <div class="control-group">
      <label>均线参数:</label>
      <select v-model="selectedParam" @change="updateCharts">
        <option v-for="p in paramCombos" :key="p" :value="p">{{ p }}</option>
      </select>
    </div>
    <div class="control-group" v-if="bestParam">
      <label>最优组合:</label>
      <span style="font-size:14px;color:#f59e0b;font-weight:600;">{{ bestParam.stock }} - {{ bestParam.param }} (Sharpe={{ bestParam.sharpe_ratio }})</span>
    </div>
  </div>

  <div class="metrics-grid">
    <div class="metric-card">
      <div class="label">累计回报</div>
      <div class="value" :class="currentMetrics.cumulative_return >= 0 ? 'positive' : 'negative'">
        {{ currentMetrics.cumulative_return >= 0 ? '+' : '' }}{{ currentMetrics.cumulative_return }}%
      </div>
      <div class="sub" style="color:#888;">买入持有: {{ currentMetrics.bh_cumulative_return >= 0 ? '+' : '' }}{{ currentMetrics.bh_cumulative_return }}%</div>
      <div class="icon">📈</div>
    </div>
    <div class="metric-card">
      <div class="label">最大回撤 (MDD)</div>
      <div class="value negative">{{ currentMetrics.max_drawdown }}%</div>
      <div class="sub" style="color:#888;">买入持有: {{ currentMetrics.bh_max_drawdown }}%</div>
      <div class="icon">📉</div>
    </div>
    <div class="metric-card">
      <div class="label">夏普比率</div>
      <div class="value" :class="currentMetrics.sharpe_ratio >= 1 ? 'positive' : (currentMetrics.sharpe_ratio >= 0 ? 'neutral' : 'negative')">
        {{ currentMetrics.sharpe_ratio }}
      </div>
      <div class="sub" style="color:#888;">买入持有: {{ currentMetrics.bh_sharpe_ratio }}</div>
      <div class="icon">⚡</div>
    </div>
    <div class="metric-card">
      <div class="label">期末市值</div>
      <div class="value neutral">¥{{ formatNum(currentMetrics.final_value) }}</div>
      <div class="sub" style="color:#888;">初始资金: ¥100,000</div>
      <div class="icon">💰</div>
    </div>
    <div class="metric-card">
      <div class="label">交易次数</div>
      <div class="value neutral">{{ currentMetrics.buy_count }}</div>
      <div class="sub" style="color:#888;">买入信号次数</div>
      <div class="icon">🔄</div>
    </div>
    <div class="metric-card">
      <div class="label">年化收益率</div>
      <div class="value" :class="currentMetrics.annual_return >= 0 ? 'positive' : 'negative'">
        {{ currentMetrics.annual_return >= 0 ? '+' : '' }}{{ currentMetrics.annual_return }}%
      </div>
      <div class="sub" style="color:#888;">折算年度收益</div>
      <div class="icon">📅</div>
    </div>
  </div>

  <div class="chart-card">
    <h3>股价走势与均线信号</h3>
    <div ref="chartPrice" class="chart-container" style="height: 450px;"></div>
  </div>

  <div class="chart-card">
    <h3>策略收益 vs 买入持有 — 市值曲线对比</h3>
    <div ref="chartReturns" class="chart-container" style="height: 400px;"></div>
  </div>

  <div class="chart-card">
    <h3>最大回撤对比</h3>
    <div ref="chartDrawdown" class="chart-container" style="height: 350px;"></div>
  </div>

  <div class="chart-card">
    <h3>多股票多参数 — 累计回报对比</h3>
    <div ref="chartCompare" class="chart-container" style="height: 450px;"></div>
  </div>

  <div class="table-card">
    <h3>完整回测结果汇总表</h3>
    <table>
      <thead>
        <tr>
          <th>股票</th>
          <th>参数</th>
          <th>累计回报</th>
          <th>年化收益</th>
          <th>最大回撤</th>
          <th>夏普比率</th>
          <th>买入持有回报</th>
          <th>持有MDD</th>
          <th>持有Sharpe</th>
          <th>交易次数</th>
          <th>评价</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in allResults" :key="idx" :class="{'best-row': isBest(row)}">
          <td>{{ row.stock }}</td>
          <td>{{ row.param }}</td>
          <td :class="row.cumulative_return >= 0 ? 'positive' : 'negative'" style="font-weight:600;">
            {{ (row.cumulative_return * 100).toFixed(2) }}%
          </td>
          <td :class="row.annual_return >= 0 ? 'positive' : 'negative'">
            {{ (row.annual_return * 100).toFixed(2) }}%
          </td>
          <td class="negative">{{ (row.max_drawdown * 100).toFixed(2) }}%</td>
          <td :class="row.sharpe_ratio >= 1 ? 'positive' : (row.sharpe_ratio >= 0 ? 'neutral' : 'negative')" style="font-weight:600;">
            {{ row.sharpe_ratio.toFixed(2) }}
          </td>
          <td :class="row.bh_cumulative_return >= 0 ? 'positive' : 'negative'">
            {{ (row.bh_cumulative_return * 100).toFixed(2) }}%
          </td>
          <td class="negative">{{ (row.bh_max_drawdown * 100).toFixed(2) }}%</td>
          <td>{{ row.bh_sharpe_ratio.toFixed(2) }}</td>
          <td>{{ row.buy_count }}</td>
          <td>
            <span v-if="row.sharpe_ratio >= 1" style="color:#e0364d;font-weight:600;">优秀</span>
            <span v-else-if="row.sharpe_ratio >= 0.5" style="color:#f59e0b;">良好</span>
            <span v-else-if="row.sharpe_ratio >= 0" style="color:#2563eb;">一般</span>
            <span v-else style="color:#16a34a;">较差</span>
            <span v-if="isBest(row)" class="best-badge">最优</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="concept-card">
    <h3>核心概念解析</h3>
    <div class="concept-grid">
      <div class="concept-item" style="border-left-color: #e0364d;">
        <h4>金叉（Golden Cross）</h4>
        <p>短周期均线从下方穿越长周期均线向上。表示短期价格上涨动能增强，突破长期均价，通常被视为<strong>看涨买入信号</strong>。</p>
      </div>
      <div class="concept-item" style="border-left-color: #16a34a;">
        <h4>死叉（Death Cross）</h4>
        <p>短周期均线从上方穿越长周期均线向下。表示短期价格下跌动能增强，跌破长期均价，通常被视为<strong>看跌卖出信号</strong>。</p>
      </div>
      <div class="concept-item">
        <h4>累计回报（Cumulative Return）</h4>
        <div class="formula">CR = (V_final - V_initial) / V_initial</div>
        <p>策略从开始到结束的总收益率，是最直观的收益衡量指标。CR > 0 盈利，CR < 0 亏损。</p>
      </div>
      <div class="concept-item">
        <h4>最大回撤（MDD）</h4>
        <div class="formula">MDD = min((V_t - max(V_s)) / max(V_s))</div>
        <p>从历史最高点到后续最低点的最大跌幅。MDD越小越好。跌20%需涨25%回本，跌50%需涨100%回本。</p>
      </div>
      <div class="concept-item">
        <h4>夏普比率（Sharpe Ratio）</h4>
        <div class="formula">Sharpe = √252 × (R̄ - Rf) / σ</div>
        <p>单位风险下的超额回报。<1.0较差，1.0~2.0良好，>2.0优秀。衡量风险调整后的收益质量。</p>
      </div>
      <div class="concept-item" style="border-left-color: #7c3aed;">
        <h4>策略适用场景</h4>
        <p><strong>适合：</strong>趋势行情、中长线、高波动股<br>
        <strong>不适合：</strong>横盘震荡、V型反转、高频交易<br>
        核心价值在于用纪律化规则替代情绪化决策。</p>
      </div>
    </div>
  </div>

  <div class="footer">
    <p>BI工作坊 · AI量化公益课 Task3 — 双均线策略量化分析</p>
    <p style="margin-top:4px;">数据来源: Tushare API | 回测区间: 2024-2026 | 初始资金: ¥100,000 | 本报告仅供学习参考，不构成投资建议</p>
  </div>
</div>

<script>
const { createApp, ref, computed, onMounted, nextTick, watch } = Vue;

const app = createApp({
  setup() {
    const rawData = __JSON_PLACEHOLDER__;

    const stockNames = ref(rawData.summary.stock_names);
    const paramCombos = ref(rawData.summary.param_combos);
    const allResults = ref(rawData.summary.all_results);
    const bestParam = ref(rawData.best_params);

    const selectedStock = ref(stockNames.value[0]);
    const selectedParam = ref(paramCombos.value[0]);

    const chartPrice = ref(null);
    const chartReturns = ref(null);
    const chartDrawdown = ref(null);
    const chartCompare = ref(null);

    let echartPrice = null, echartReturns = null, echartDrawdown = null, echartCompare = null;

    const stockCount = stockNames.value.length;
    const paramCount = paramCombos.value.length;
    const totalBacktests = stockCount * paramCount;

    const currentData = computed(() => {
      const stock = rawData.stocks[selectedStock.value];
      if (!stock || !stock.params[selectedParam.value]) return null;
      return stock.params[selectedParam.value];
    });

    const currentMetrics = computed(() => {
      if (!currentData.value) return {
        cumulative_return: 0, max_drawdown: 0, sharpe_ratio: 0,
        final_value: 0, buy_count: 0, bh_cumulative_return: 0,
        bh_max_drawdown: 0, bh_sharpe_ratio: 0, annual_return: 0
      };
      return currentData.value.metrics;
    });

    const formatNum = (n) => {
      return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    };

    const isBest = (row) => {
      return bestParam.value && row.stock === bestParam.value.stock && row.param === bestParam.value.param;
    };

    const renderPriceChart = () => {
      if (!echartPrice || !currentData.value) return;
      const d = currentData.value;
      const paramParts = selectedParam.value.split('/');
      const maShortName = paramParts[0];
      const maLongName = paramParts[1];

      const buySignals = d.signals.filter(s => s.type === 'buy');
      const sellSignals = d.signals.filter(s => s.type === 'sell');

      const option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { data: ['收盘价', maShortName, maLongName, '买入信号', '卖出信号'], top: 0 },
        grid: { left: '6%', right: '4%', bottom: '12%', top: '12%' },
        xAxis: { type: 'category', data: d.dates, axisLabel: { rotate: 30, fontSize: 10 } },
        yAxis: { type: 'value', name: '股价(元)', scale: true },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { type: 'slider', start: 0, end: 100, height: 20, bottom: 5 }
        ],
        series: [
          { name: '收盘价', type: 'line', data: d.close, lineStyle: { width: 1.2, color: '#6B7280' }, itemStyle: { color: '#6B7280' }, symbol: 'none', z: 2 },
          { name: maShortName, type: 'line', data: d.ma_short, lineStyle: { width: 1.5, color: '#2563EB' }, itemStyle: { color: '#2563EB' }, symbol: 'none', z: 3 },
          { name: maLongName, type: 'line', data: d.ma_long, lineStyle: { width: 1.5, color: '#F59E0B' }, itemStyle: { color: '#F59E0B' }, symbol: 'none', z: 3 },
          { name: '买入信号', type: 'scatter', data: buySignals.map(s => [s.date, s.price]), symbol: 'triangle', symbolSize: 12, itemStyle: { color: '#E0364D', borderColor: '#fff', borderWidth: 1 }, z: 5 },
          { name: '卖出信号', type: 'scatter', data: sellSignals.map(s => [s.date, s.price]), symbol: 'pin', symbolSize: 14, symbolRotate: 180, itemStyle: { color: '#16A34A', borderColor: '#fff', borderWidth: 1 }, z: 5 }
        ]
      };
      echartPrice.setOption(option, true);
    };

    const renderReturnsChart = () => {
      if (!echartReturns || !currentData.value) return;
      const d = currentData.value;
      const option = {
        tooltip: { trigger: 'axis', formatter: function(params) {
          let html = params[0].axisValue + '<br/>';
          params.forEach(p => { html += p.marker + p.seriesName + ': ¥' + Number(p.value).toLocaleString() + '<br/>'; });
          return html;
        }},
        legend: { data: ['双均线策略', '买入持有'], top: 0 },
        grid: { left: '10%', right: '4%', bottom: '12%', top: '12%' },
        xAxis: { type: 'category', data: d.dates, axisLabel: { rotate: 30, fontSize: 10 } },
        yAxis: { type: 'value', name: '市值(¥)', axisLabel: { formatter: function(v) { return '¥' + (v/10000).toFixed(1) + '万'; } } },
        dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', start: 0, end: 100, height: 20, bottom: 5 }],
        series: [
          { name: '双均线策略', type: 'line', data: d.strategy_value, lineStyle: { width: 2, color: '#E0364D' }, areaStyle: { color: 'rgba(224,54,77,0.08)' }, itemStyle: { color: '#E0364D' }, symbol: 'none' },
          { name: '买入持有', type: 'line', data: d.buy_hold_value, lineStyle: { width: 2, color: '#2563EB', type: 'dashed' }, itemStyle: { color: '#2563EB' }, symbol: 'none' }
        ]
      };
      echartReturns.setOption(option, true);
    };

    const renderDrawdownChart = () => {
      if (!echartDrawdown || !currentData.value) return;
      const d = currentData.value;
      const strategyDD = [];
      let maxS = d.strategy_value[0];
      d.strategy_value.forEach(v => { if (v > maxS) maxS = v; strategyDD.push(((v - maxS) / maxS * 100).toFixed(2)); });
      const bhDD = [];
      let maxBH = d.buy_hold_value[0];
      d.buy_hold_value.forEach(v => { if (v > maxBH) maxBH = v; bhDD.push(((v - maxBH) / maxBH * 100).toFixed(2)); });
      const option = {
        tooltip: { trigger: 'axis', formatter: function(params) {
          let html = params[0].axisValue + '<br/>';
          params.forEach(p => { html += p.marker + p.seriesName + ': ' + p.value + '%<br/>'; });
          return html;
        }},
        legend: { data: ['策略回撤', '买入持有回撤'], top: 0 },
        grid: { left: '6%', right: '4%', bottom: '12%', top: '12%' },
        xAxis: { type: 'category', data: d.dates, axisLabel: { rotate: 30, fontSize: 10 } },
        yAxis: { type: 'value', name: '回撤(%)', max: 0 },
        dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', start: 0, end: 100, height: 20, bottom: 5 }],
        series: [
          { name: '策略回撤', type: 'line', data: strategyDD, lineStyle: { width: 1.5, color: '#E0364D' }, areaStyle: { color: 'rgba(224,54,77,0.2)' }, itemStyle: { color: '#E0364D' }, symbol: 'none' },
          { name: '买入持有回撤', type: 'line', data: bhDD, lineStyle: { width: 1.5, color: '#2563EB', type: 'dashed' }, itemStyle: { color: '#2563EB' }, symbol: 'none' }
        ]
      };
      echartDrawdown.setOption(option, true);
    };

    const renderCompareChart = () => {
      if (!echartCompare) return;
      const stocks = stockNames.value;
      const params = paramCombos.value;
      const colors = ['#2563EB', '#F59E0B', '#7C3AED', '#16A34A', '#E0364D'];
      const series = params.map((p, i) => ({
        name: p, type: 'bar',
        data: stocks.map(s => {
          const item = allResults.value.find(r => r.stock === s && r.param === p);
          return item ? +(item.cumulative_return * 100).toFixed(2) : 0;
        }),
        itemStyle: { color: colors[i % colors.length], borderRadius: [4, 4, 0, 0] }
      }));
      const option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: params, top: 0, type: 'scroll' },
        grid: { left: '5%', right: '4%', bottom: '10%', top: '12%' },
        xAxis: { type: 'category', data: stocks },
        yAxis: { type: 'value', name: '累计回报(%)' },
        series: series
      };
      echartCompare.setOption(option, true);
    };

    const updateCharts = () => {
      nextTick(() => {
        renderPriceChart();
        renderReturnsChart();
        renderDrawdownChart();
        renderCompareChart();
      });
    };

    const handleResize = () => {
      echartPrice && echartPrice.resize();
      echartReturns && echartReturns.resize();
      echartDrawdown && echartDrawdown.resize();
      echartCompare && echartCompare.resize();
    };

    onMounted(() => {
      nextTick(() => {
        echartPrice = echarts.init(chartPrice.value);
        echartReturns = echarts.init(chartReturns.value);
        echartDrawdown = echarts.init(chartDrawdown.value);
        echartCompare = echarts.init(chartCompare.value);
        updateCharts();
        window.addEventListener('resize', handleResize);
      });
    });

    return {
      stockNames, paramCombos, allResults, bestParam,
      selectedStock, selectedParam,
      chartPrice, chartReturns, chartDrawdown, chartCompare,
      currentData, currentMetrics,
      stockCount, paramCount, totalBacktests,
      formatNum, isBest, updateCharts
    };
  }
});

app.mount('#app');
</script>
</body>
</html>
"""

# 使用占位符替换JSON数据
html = HTML_TEMPLATE.replace("__JSON_PLACEHOLDER__", json_str)

output_path = os.path.join(BASE_DIR, "双均线策略可视化看板.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"HTML页面已生成: {output_path}")
file_size = os.path.getsize(output_path) / 1024
print(f"文件大小: {file_size:.0f} KB")
