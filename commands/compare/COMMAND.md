---
name: compare
description: "对比命令 — 多标的横向对比分析"
version: "1.0"
triggers:
  - "对比"
  - "比较"
  - "哪个好"
  - "选哪个"
  - "VS"
  - "PK"
  - "compare"
---

# /compare — 对比分析命令

## 功能

对2-5个投资标的进行系统性横向对比，辅助用户在多个选项中做出取舍。

## 执行流程

1. **标的识别**: 从用户输入中提取所有待比较标的
   - 支持: 股票代码、公司名称、行业名称
   - 自动补全: 如用户只说"白酒龙头"，自动识别为贵州茅台/五粮液等

2. **数据采集** (对每个标的并行):
   - market-data: 行情和估值数据
   - datasource-query: 相关路演纪要/研报
   - Web搜索: 财务数据、行业份额

3. **技能调用**:
   - 主技能: comparative-analysis
   - 辅助: valuation-framework (对每个标的分别估值)
   - 辅助: risk-matrix (风险对比)

4. **输出格式**:
   - 按 comparative-analysis 技能的标准7步格式输出
   - 突出每个标的的独特优势和关键差异
   - 给出明确的排名和建议
