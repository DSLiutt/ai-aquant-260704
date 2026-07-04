# 技术指标计算 Notebook 规格说明书 (SPEC)

> 文件: `技术指标计算过程.ipynb`
> 目标: 以 Jupyter Notebook 形式，**分步骤、可交互**地展示 RSI、MACD、布林带、KDJ 四大技术指标的完整计算过程与可视化结果。

---

## 1. 背景与目标

| 项目 | 说明 |
|------|------|
| 数据来源 | 三一重工(600031.SH)、平安集团(000001.SZ) 日线行情 CSV |
| 核心任务 | 加载数据 → 数据诊断 → 逐指标计算 → 可视化 → 综合分析 |
| 交付物 | 一个 `.ipynb` 文件，包含代码、输出图表、Markdown 说明 |
| 受众 | 量化学习入门者，需理解每个指标的计算逻辑和代码实现 |

## 2. 技术栈

```
Python 3.11+
pandas       — 数据加载与处理
numpy        — 数值计算
matplotlib   — 可视化绘图
```

## 3. Notebook 单元格规划

共 **8 个 Section**，每个 Section 包含 Markdown 说明 + Code 单元格 + 输出。

### Section 0: 标题与概述
- **类型**: Markdown
- **内容**: Notebook 标题、数据说明、指标清单、运行环境说明

### Section 1: 环境准备与数据加载
- **类型**: Markdown + Code
- **Code**:
  - 导入 pandas / numpy / matplotlib
  - 设置中文字体、绘图风格
  - 定义 `load_data()` 函数，加载两只股票 CSV
  - 日期解析、升序排列
- **输出**: 打印前 5 行数据预览

### Section 2: 数据基础诊断
- **类型**: Markdown + Code
- **Code**:
  - 缺失值检查 (`df.isnull().sum()`)
  - 描述性统计 (`df.describe()`)
  - 数据时间范围、记录数
- **输出**: 诊断报告文本 + 统计表格

### Section 3: RSI 计算过程
- **类型**: Markdown + Code (分 5 个步骤)
- **Markdown**: 介绍 RSI 公式与作用
- **Code 步骤拆解**:
  - Step 1: 计算价格变动 `delta = close.diff()`
  - Step 2: 分离涨跌 `gain / loss`
  - Step 3: Wilder 平滑法计算平均涨跌幅
  - Step 4: 计算 RS 和 RSI
  - Step 5: 绘制 RSI 图（含 70/30 超买超卖线）
- **输出**: 每步中间结果 DataFrame 预览 + RSI 图表

### Section 4: MACD 计算过程
- **类型**: Markdown + Code (分 4 个步骤)
- **Markdown**: 介绍 MACD 公式与作用
- **Code 步骤拆解**:
  - Step 1: 计算 EMA(12) 和 EMA(26)
  - Step 2: 计算 DIF = EMA(12) - EMA(26)
  - Step 3: 计算 DEA = EMA(DIF, 9)
  - Step 4: 计算 MACD 柱 = 2 × (DIF - DEA)
  - Step 5: 绘制 MACD 图（DIF 线 + DEA 线 + 柱状图）
- **输出**: 中间结果预览 + MACD 图表

### Section 5: 布林带计算过程
- **类型**: Markdown + Code (分 4 个步骤)
- **Markdown**: 介绍布林带公式与作用
- **Code 步骤拆解**:
  - Step 1: 计算中轨 MA(20)
  - Step 2: 计算标准差 SD(20)
  - Step 3: 计算上轨/下轨
  - Step 4: 计算带宽 Bandwidth
  - Step 5: 绘制布林带图（价格 + 三轨 + 填充带）
- **输出**: 中间结果预览 + 布林带图表

### Section 6: KDJ 计算过程（扩展指标）
- **类型**: Markdown + Code (分 4 个步骤)
- **Markdown**: 介绍 KDJ 公式与作用，列出其他典型指标
- **Code 步骤拆解**:
  - Step 1: 计算 RSV
  - Step 2: 计算 K 值（SMA 平滑）
  - Step 3: 计算 D 值（SMA 平滑）
  - Step 4: 计算 J = 3K - 2D
  - Step 5: 绘制 KDJ 图
- **输出**: 中间结果预览 + KDJ 图表

### Section 7: 综合可视化与指标对照
- **类型**: Markdown + Code
- **Code**: 绘制 5 行子图（价格+布林带 / RSI / MACD / KDJ / 成交量）
- **输出**: 综合指标图

### Section 8: 结果总结
- **类型**: Markdown
- **内容**: 各指标计算逻辑总结、最近交易日指标值、分析结论

## 4. 设计原则

1. **可读性优先**: 每个 Code 单元格前都有 Markdown 说明计算逻辑
2. **分步展示**: 关键指标拆成多个小单元格，展示中间计算结果（而非一个黑盒函数）
3. **双股票对比**: 每个指标同时计算三一重工和平安集团，便于对比
4. **可视化贯穿**: 每个指标计算完成后立即绘制对应图表
5. **中国股市配色**: 红涨绿跌，¥ 符号

## 5. 输出文件清单

| 文件 | 说明 |
|------|------|
| `技术指标计算过程.ipynb` | 主交付 Notebook |
| `NOTEBOOK_SPEC.md` | 本规格说明书 |
