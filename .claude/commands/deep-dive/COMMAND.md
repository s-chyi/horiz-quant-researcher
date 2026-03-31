---
name: deep-dive
description: "深度研究命令 — 对单一标的进行全方位深度分析，输出投研级别报告"
version: "1.0"
triggers:
  - "深度"
  - "深入"
  - "详细分析"
  - "全面分析"
  - "值不值得买"
  - "deep dive"
---

# /deep-dive — 深度研究命令

## 功能

对单一标的进行全方位深度研究，组合多个技能产生投研级别的完整报告。这是与 PaiPai 正面竞争的核心命令。

## 执行流程

1. **数据全面采集** (并行执行以加速):
   - **组 A (AKShare, 并行)**: quote + kline + financials + indicators + balance-sheet + cash-flow + fund-flow + shareholders + industry (全部通过 localhost:8901)
   - **组 B (Datasource, 并行)**: roadshows/search + reports (通过 localhost:3001)
   - **组 C (Web, 并行)**: Tavily 搜索最新新闻 + 行业动态
   
   > **重要**: 组 A/B/C 之间并行，组内串行。用 Bash 的 `curl` 并发请求，或按 MCP tool 分别调用。

2. **多技能串联执行**:
   ```
   步骤1: stock-deep-analysis (基本面5维分析)
     ↓
   步骤2: valuation-framework (多方法估值)
     ↓
   步骤3: risk-matrix (风险评估)
     ↓
   步骤4: catalyst-scanner (催化剂扫描)
     ↓
   步骤5: bull-bear-debate (多空辩论)
     ↓
   步骤6: 综合结论
   ```

3. **思维链构建**:
   使用 thinking-chain-builder 选择适合的思维链模式:
   - 估值相关 → 演绎链
   - 行业趋势 → 传导链
   - 不确定性高 → 辩证链

4. **质量门控**:
   使用 quality-gate 对最终输出进行评分
   - ≥85分: 直接输出
   - 70-84分: 补充不足部分后输出
   - <70分: 识别缺失维度，额外搜索数据后重新分析

5. **输出格式**:
   ```
   ═══════════════════════════════════════
   [公司名称] ([代码]) 深度研究报告
   生成时间: [日期时间]
   ═══════════════════════════════════════

   📋 执行摘要 (30秒速读版)
   ├── 综合评级: [强烈推荐/推荐/中性/回避/强烈回避]
   ├── 估值判断: [低估X%/合理/高估X%]
   ├── 核心逻辑: [1-2句话]
   └── 关键催化剂: [最近的催化事件]

   📊 详细分析 (以下各节)
   ├── 一、基本面分析 (stock-deep-analysis)
   ├── 二、估值分析 (valuation-framework)
   ├── 三、风险评估 (risk-matrix)
   ├── 四、催化剂日历 (catalyst-scanner)
   ├── 五、多空辩论 (bull-bear-debate)
   └── 六、综合结论与操作建议

   📎 数据来源声明
   └── [逐一列出引用的数据源和可靠性等级]
   ```

## 差异化优势 (vs PaiPai)

- **透明推理链**: 每个结论都展示完整推导过程
- **强制对立面**: bull-bear-debate 确保不遗漏反面论点
- **数据溯源**: 每个数据点都标注来源和可靠性
- **多方法交叉**: 估值至少使用3种方法交叉验证
- **私域数据**: 整合路演纪要等独家信息源
