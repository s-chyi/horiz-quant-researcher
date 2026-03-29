# horiz-quant-researcher

> 基于 Claude Code 的 AI 量化研究员 — 专业级投资研究分析系统

## 项目简介

horiz-quant-researcher 是一个基于 Claude Code (Opus 4.6) 构建的专业 AI 投资研究助手。通过精心设计的技能体系、多维分析框架和质量控制体系，提供超越市面竞品的投研分析质量。

### 核心优势

| 维度 | 本项目 | 传统AI研究工具 |
|------|--------|--------------|
| 推理深度 | 6种思维链模式，强制多维分析 | 黑箱输出，思维链不透明 |
| 分析质量 | 质量门控 ≥85分通过，不达标自动补充 | 无质量控制机制 |
| 多空辩论 | 强制对立面论证，devil's advocate | 通常只呈现单一观点 |
| 数据溯源 | 🟢🟡🔴 三级数据可靠性标注 | 数据来源不透明 |
| 私域数据 | 接入路演纪要/研报/公众号分析 | 仅依赖公开数据 |
| 估值体系 | ≥3种方法交叉验证 + DCF敏感性分析 | 单一估值方法 |

## 架构概览

```
horiz-quant-researcher/
├── CLAUDE.md                 # 核心项目指南 (思维链/质量门控/路由)
├── .mcp.json                 # MCP服务器配置
├── DATA_GAP_REPORT.md        # 数据缺口报告
│
├── skills/                   # 技能体系 (17个技能)
│   ├── meta/                 # 元技能 (4个)
│   │   ├── question-classifier/   # 问题分类路由
│   │   ├── quality-gate/          # 质量门控
│   │   ├── thinking-chain-builder/ # 思维链构建器
│   │   └── source-validator/      # 数据源验证
│   │
│   ├── core/                 # 核心分析技能 (10个)
│   │   ├── stock-deep-analysis/   # 个股深度分析
│   │   ├── earnings-review/       # 业绩解读
│   │   ├── industry-chain/        # 产业链分析
│   │   ├── bull-bear-debate/      # 多空辩论
│   │   ├── catalyst-scanner/      # 催化剂扫描
│   │   ├── valuation-framework/   # 估值框架
│   │   ├── risk-matrix/           # 风险矩阵
│   │   ├── macro-transmission/    # 宏观传导链
│   │   ├── morning-briefing/      # 晨报/复盘
│   │   ├── report-interpretation/ # 研报解读
│   │   ├── roadshow-analysis/     # 路演分析
│   │   ├── comparative-analysis/  # 比较分析
│   │   └── portfolio-strategy/    # 组合策略
│   │
│   └── data/                 # 数据技能 (4个)
│       ├── datasource-query/      # 私域数据查询
│       ├── market-data/           # 市场行情
│       ├── fund-flow/             # 资金流向
│       └── news-sentiment/        # 新闻舆情
│
├── commands/                 # 命令调度器 (8个)
│   ├── analyze/              # 综合分析入口
│   ├── briefing/             # 晨报/复盘
│   ├── deep-dive/            # 深度研究 (核心竞争力)
│   ├── compare/              # 对比分析
│   ├── debate/               # 多空辩论
│   ├── risk-check/           # 风险检查
│   ├── valuation/            # 估值分析
│   └── macro/                # 宏观分析
│
└── references/               # 参考知识库 (6个)
    ├── valuation-methods.md       # 估值方法论
    ├── financial-analysis-framework.md # 财务分析框架
    ├── industry-analysis-template.md  # 行业分析模板
    ├── risk-assessment-matrix.md      # 风险评估方法论
    ├── macro-indicators.md            # 宏观指标体系
    └── a-share-calendar.md            # A股重要日历
```

## 快速开始

### 环境要求
- Claude Code CLI (最新版本)
- Claude Opus 4.6 模型访问权限
- Node.js 18+ (MCP服务器依赖)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/s-chyi/horiz-quant-researcher.git
cd horiz-quant-researcher

# 2. 配置MCP服务器 (编辑 .mcp.json 中的API地址和密钥)
# - horiz-datasource: 私域数据API
# - tavily: Web搜索
# - playwright: 网页交互

# 3. 启动Claude Code
claude

# 4. 开始使用
# 输入任何投研问题即可，系统自动路由到合适的技能
```

### 使用示例

```
# 个股深度分析
"帮我深度分析一下贵州茅台"

# 多空辩论
"宁德时代现在能买吗？帮我做个多空辩论"

# 估值分析
"比亚迪现在贵不贵？"

# 行业分析
"AI产业链分析，哪些环节最值得投资？"

# 宏观分析
"降息对A股有什么影响？"

# 晨报
"今天市场怎么样？"

# 风险检查
"帮我检查一下恒大的风险"

# 比较分析
"格力和美的哪个更值得投资？"
```

## 技能体系详解

### 元技能 (Meta Skills)
基础设施层，为所有分析提供底层支持：

| 技能 | 功能 | 说明 |
|------|------|------|
| question-classifier | 问题分类路由 | 自动识别用户意图，路由到最佳技能组合 |
| quality-gate | 质量门控 | 5维度评分，≥85分通过，不达标自动补充 |
| thinking-chain-builder | 思维链构建 | 6种模式: 基本面/估值/事件/比较/宏观/组合 |
| source-validator | 数据源验证 | 🟢财报🟡研报🔴推测，强制溯源标注 |

### 核心分析技能 (Core Skills)
13个专业分析技能覆盖投研全流程：

| 技能 | 功能 | 核心特色 |
|------|------|---------|
| stock-deep-analysis | 5维度基本面分析 | 杜邦拆解+产业链定位+竞争力评估 |
| earnings-review | 业绩解读 | 超预期/不及预期量化+边际变化追踪 |
| industry-chain | 产业链分析 | 上中下游全景+利润分配+景气传导 |
| bull-bear-debate | 多空辩论 | 强制对立面论证+仲裁评分 |
| catalyst-scanner | 催化剂扫描 | 4级分类+时间窗口+概率评估 |
| valuation-framework | 多方法估值 | ≥3种方法交叉+DCF敏感性 |
| risk-matrix | 风险矩阵 | 概率×影响矩阵+压力测试 |
| macro-transmission | 宏观传导链 | 3阶传导+历史类比+时滞标注 |
| morning-briefing | 晨报/复盘 | 全球市场+资金流向+策略建议 |
| report-interpretation | 研报解读 | 偏见识别+独立评估+核心假设检验 |
| roadshow-analysis | 路演分析 | 措辞变化+未说的信息+交叉验证 |
| comparative-analysis | 比较分析 | 7维度对比+雷达图+适配投资风格 |
| portfolio-strategy | 组合策略 | 资产配置+风险预算+情景分析 |

### 数据技能 (Data Skills)
4个数据获取与处理技能：

| 技能 | 数据源 | 说明 |
|------|--------|------|
| datasource-query | horiz-datasource API | 路演/研报/公众号私域数据 |
| market-data | 新浪/腾讯API | 实时行情+K线 (临时方案) |
| fund-flow | 东方财富/新浪 | 北向/融资/主力资金流向 |
| news-sentiment | Tavily搜索 | 新闻采集+情绪分析 |

## 命令系统

8个命令调度器，编排多技能协同工作：

| 命令 | 触发词 | 编排的技能 |
|------|--------|-----------|
| /analyze | 分析、看看 | 自动路由到最佳技能组合 |
| /deep-dive | 深度、详细 | 6技能串行流水线 + 质量门控 |
| /briefing | 晨报、复盘 | morning-briefing + fund-flow + news |
| /compare | 对比、比较 | comparative-analysis + valuation |
| /debate | 多空、能买吗 | bull-bear-debate + risk-matrix |
| /risk-check | 风险、踩雷 | risk-matrix + news-sentiment |
| /valuation | 估值、贵不贵 | valuation-framework + earnings |
| /macro | 宏观、降息 | macro-transmission + catalyst |

## 参考知识库

6个参考文档为分析提供专业框架支撑：

| 文档 | 内容 | 页数 |
|------|------|------|
| valuation-methods.md | 9种估值方法+决策树+交叉验证 | ~230行 |
| financial-analysis-framework.md | 杜邦分析+三表分析+红旗清单 | ~270行 |
| industry-analysis-template.md | 生命周期+波特五力+行业模板 | ~350行 |
| risk-assessment-matrix.md | 概率-影响矩阵+风控体系 | ~350行 |
| macro-indicators.md | 中美宏观指标+库存周期+传导链 | ~400行 |
| a-share-calendar.md | 财报/政策/行业日历+节假日效应 | ~350行 |

## 数据源

### 已接入
- **horiz-quant-datasource**: 路演纪要、研究报告、微信文章 (私域数据)
- **Tavily**: Web搜索 (实时新闻、公开数据)
- **新浪/腾讯财经API**: 实时行情 (临时方案)
- **Playwright**: 网页交互 (数据验证)

### 待接入 (详见 DATA_GAP_REPORT.md)
- 🔴 历史K线与行情数据 (AKShare)
- 🔴 财务报表数据 (三表+财务指标)
- 🔴 分析师一致预期
- 🔴 大宗交易与股东数据
- 🟡 北向资金、融资融券
- 🟡 宏观经济时间序列
- 🟡 ETF/基金数据

## 质量保障体系

```
用户提问
  │
  ▼
问题分类 (question-classifier)
  │
  ▼
思维链构建 (thinking-chain-builder)
  │ 选择6种模式之一
  ▼
数据采集 (data skills × N 并行)
  │
  ▼
核心分析 (core skills × N 串行/并行)
  │
  ▼
数据溯源标注 (source-validator)
  │ 🟢🟡🔴 三级标注
  ▼
质量门控 (quality-gate)
  │ ≥85分 → 输出
  │ 70-84分 → 补充后输出
  │ <70分 → 重做
  ▼
最终报告输出
```

## 与竞品(PaiPai/Alpha派)的差异化

| 维度 | horiz-quant-researcher | PaiPai (Alpha派) |
|------|----------------------|-----------------|
| 模型 | Claude Opus 4.6 (最强推理) | 未公开 (推测多模型混合) |
| 思维链 | 完全透明，6种模式 | 部分可见，模式有限 |
| 多空辩论 | 强制对立面+仲裁裁决 | 有但不强制 |
| 数据标注 | 每条结论标注数据来源和可靠性 | 数据源不透明 |
| 私域数据 | 路演纪要/研报/公众号 | 公开数据为主 |
| 估值 | ≥3种方法+敏感性分析 | 单一或少数方法 |
| 质量控制 | 85分门槛+自动补充 | 无公开质控机制 |
| 可定制 | 完全开源，技能可扩展 | 封闭系统 |
| 成本 | Claude API成本 | SaaS订阅费 |

## 开发路线

- [x] 核心项目结构 (CLAUDE.md + .mcp.json)
- [x] 17个技能文件
- [x] 8个命令调度器
- [x] 6个参考知识库
- [x] 数据缺口报告
- [ ] 数据源第一阶段集成 (行情 + 财报)
- [ ] 数据源第二阶段集成 (一致预期 + 资金)
- [ ] 回测质量评估 (vs PaiPai 对比测试)
- [ ] 用户反馈迭代优化

## 许可证

MIT License

## 作者

Horiz AI Agency — AI量化研究团队
