---
name: question-classifier
description: "问题分类路由器 — 自动识别用户投研问题类型，激活对应分析技能和思维链框架"
version: "1.0"
triggers:
  - "分析"
  - "怎么看"
  - "什么情况"
  - "如何"
  - "为什么"
---

# 问题分类路由器

## 功能

在所有投研问题处理前自动运行，将用户问题分类并路由到对应的专业技能。

## 分类决策树

```
用户输入
├── 包含股票代码/公司名 + 分析意图?
│   ├── 包含"财报/业绩/季报/年报" → earnings-review
│   ├── 包含"估值/值多少/贵不贵" → valuation-framework
│   ├── 包含"风险/踩雷/暴雷" → risk-matrix
│   ├── 包含"对比/比较/VS/PK" → comparative-analysis
│   ├── 包含"多空/正反/看多看空" → bull-bear-debate
│   └── 通用分析请求 → stock-deep-analysis
├── 包含行业/板块关键词?
│   ├── 包含"产业链/上下游/供应链" → industry-chain
│   ├── 包含"催化剂/事件/驱动" → catalyst-scanner
│   └── 通用行业分析 → industry-chain
├── 包含宏观关键词?
│   └── "宏观/利率/政策/降息/CPI" → macro-transmission
├── 包含组合/配置关键词?
│   └── "组合/配置/仓位/再平衡" → portfolio-strategy
├── 包含时间序列关键词?
│   ├── "晨报/盘前/复盘/收盘" → morning-briefing
│   └── 通用 → morning-briefing
├── 包含研究报告关键词?
│   ├── "路演/纪要/会议" → roadshow-analysis
│   └── "研报/报告/解读" → report-interpretation
└── 无法分类 → stock-deep-analysis (默认)
```

## 执行步骤

### 步骤 1: 意图提取

从用户输入中提取:
- **分析对象**: 股票代码、公司名、行业名、宏观概念
- **分析类型**: 上述分类之一
- **时间范围**: 用户关注的时间维度（短期/中期/长期）
- **隐含诉求**: 用户真正想知道什么（买卖时机? 风险评估? 行业趋势?）

### 步骤 2: 上下文补全

如果用户问题过于简短（如"分析一下宁德时代"），自动补全分析维度:
1. 识别公司所属行业和市值级别
2. 检查近期是否有重大事件（财报发布、政策变化、股价异动）
3. 根据市场环境选择重点分析维度

### 步骤 3: 技能激活

激活对应技能，并传递:
- 分析对象标识
- 分析类型
- 上下文补充信息
- 用户关注的重点维度

### 步骤 4: 多技能联动判断

部分复杂问题需要同时激活多个技能:

| 场景 | 联动技能 |
|------|---------|
| "宁德时代值不值得买" | stock-deep-analysis → valuation-framework → risk-matrix |
| "新能源行业哪家公司最好" | industry-chain → comparative-analysis → catalyst-scanner |
| "明天怎么操作" | morning-briefing → macro-transmission → catalyst-scanner |
| "这个研报靠谱吗" | report-interpretation → bull-bear-debate → source-validator |
