---
name: analyze
description: "分析命令 — 综合分析入口，自动路由到最合适的分析技能"
version: "1.0"
triggers:
  - "分析"
  - "看看"
  - "怎么看"
  - "什么情况"
  - "帮我分析"
  - "analyze"
---

# /analyze — 综合分析命令

## 功能

这是最常用的入口命令。自动识别用户意图，路由到合适的分析技能组合。

## 路由逻辑

```
用户输入 → 意图识别 → 技能路由

├── 包含个股名/代码:
│   ├── "怎么看[股票]" → stock-deep-analysis (全面分析)
│   ├── "[股票]财报" → earnings-review
│   ├── "[股票]估值/贵不贵" → valuation-framework
│   ├── "[股票]风险" → risk-matrix
│   ├── "[股票]A vs [股票]B" → comparative-analysis
│   └── "[股票]路演/纪要" → roadshow-analysis
│
├── 包含行业/板块:
│   ├── "[行业]产业链" → industry-chain
│   ├── "[行业]前景/趋势" → industry-chain + catalyst-scanner
│   └── "[行业]哪家好" → comparative-analysis
│
├── 包含宏观关键词:
│   ├── "降息/降准/政策" → macro-transmission
│   ├── "宏观/经济" → macro-transmission + morning-briefing
│   └── "CPI/PMI/GDP" → macro-transmission
│
├── 包含策略关键词:
│   ├── "组合/配置/仓位" → portfolio-strategy
│   ├── "多空/看多看空" → bull-bear-debate
│   └── "催化剂/事件" → catalyst-scanner
│
└── 泛泛而问:
    └── "今天怎么看/明天怎么看" → morning-briefing
```

## 执行流程

1. **意图识别**: 使用 question-classifier 技能分析用户意图
2. **数据预取**: 并行调用 datasource-query + market-data 获取基础数据
3. **技能执行**: 调用路由确定的主技能
4. **质量检查**: 使用 quality-gate 检查输出质量
5. **补充建议**: 提示用户可以进一步深入的方向
