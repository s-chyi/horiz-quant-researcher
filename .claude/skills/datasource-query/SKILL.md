---
name: datasource-query
description: "数据源查询 — 从 horiz-datasource-api 检索路演纪要、研报观点、微信文章等私域数据"
version: "1.0"
triggers:
  - "搜索"
  - "查询"
  - "检索"
  - "找"
  - "有没有"
  - "路演"
  - "纪要"
  - "研报"
  - "query"
---

# 数据源查询

## 适用场景

用户需要从 horiz-datasource-api 检索私域数据，包括路演纪要、研报观点、微信公众号文章等。此技能也作为其他技能的数据获取基础层。

## 核心原则

**私域数据是我们相对 PaiPai 的核心差异化优势之一。优先使用私域数据，然后用公开数据补充验证。**

## 可用 API 端点

### 一、私域数据 (horiz-datasource-api, localhost:3001)

> 请求头: `X-API-Key: bb528ea0bea8f7c4ef3546544f048e6c2dbd9ca54107d8cafdd8ce14047e2c80`

#### 路演纪要 (核心数据, 2321条, 每日增长)

```
GET /api/v1/roadshows?limit=20&offset=0         — 列表
GET /api/v1/roadshows/search?q={keyword}&limit=20 — 搜索（支持中文，返回 results 数组）
GET /api/v1/roadshows/{id}                       — 详情（含 AI 摘要）
GET /api/v1/roadshows/{id}/qa                    — Q&A 问答对
GET /api/v1/roadshows/stats                      — 统计

返回结构: { "total": N, "results": [{ "title", "broker", "rd_date", "ai_summary", "heat", "industry", ... }] }
```

#### 研报 (184条)

```
GET /api/v1/reports?limit=20&offset=0
GET /api/v1/reports/{id}
```

#### 其他

```
GET /api/v1/topics       — 热点话题
```

### 二、金融数据 (AKShare API, localhost:8901)

**行情与K线**:
```
GET /api/v1/quote/{code}              — 实时行情 (价格/PE/PB/市值/成交)
GET /api/v1/kline/{code}?days=250     — K线 (OHLCV, 支持 daily/weekly/monthly)
GET /api/v1/index/{code}              — 指数行情 (000300=沪深300, 399006=创业板)
```

**财务数据**:
```
GET /api/v1/financials/{code}         — 财务指标摘要
GET /api/v1/indicators/{code}         — DuPont 分析 (ROE/ROA/净利率等)
GET /api/v1/balance-sheet/{code}      — 资产负债表
GET /api/v1/cash-flow/{code}          — 现金流量表
```

**资金与股东**:
```
GET /api/v1/fund-flow/{code}          — 主力/散户净流入
GET /api/v1/shareholders/{code}       — 十大股东
GET /api/v1/industry/{code}           — 行业分类 + 同行公司
```

**code 格式**: `600519` 或 `600519.SH` 均可

## 执行步骤

### 步骤 1: 理解用户查询意图

```
查询意图识别:

用户输入: [原始问题]

├── 意图类型:
│   ├── 特定公司查询: 找[公司名]的路演/研报
│   ├── 主题搜索: 找关于[主题]的相关资料
│   ├── 时间范围查询: 最近[X天/周/月]的[数据类型]
│   └── 综合搜索: 跨数据源综合检索
│
├── 提取参数:
│   ├── 公司/代码: [如有]
│   ├── 关键词: [如有]
│   ├── 时间范围: [如有]
│   └── 数据类型偏好: [路演/研报/文章/全部]
│
└── 查询策略:
    ├── 精确查询: 有明确公司名/代码时使用
    ├── 模糊搜索: 按关键词跨源搜索
    └── 组合查询: 多条件组合检索
```

### 步骤 2: 构造 API 请求

```
请求构造:

优先级顺序 (按数据可靠性):
1. 路演纪要 (最高价值) → /api/roadshows/search?q=[关键词]
2. 研报观点 → /api/reports/search?q=[关键词]
3. 微信文章 → /api/articles/search?q=[关键词]
4. AI热股 → /api/hot-stocks?date=[日期]

并行请求策略:
├── 同时请求路演 + 研报 + 文章搜索
├── 合并结果，按相关性排序
└── 标注每条结果的来源和可靠性等级
```

### 步骤 3: 结果整理与呈现

```
搜索结果:

共找到 [X] 条相关记录:

📊 路演纪要 ([X]条):
1. [日期] [公司] - [标题/摘要]
   └── 相关度: ★★★★★ | 来源: horiz-datasource 🟢
2. [日期] [公司] - [标题/摘要]
   └── 相关度: ★★★★☆ | 来源: horiz-datasource 🟢
...

📄 研报观点 ([X]条):
1. [日期] [机构] - [标题/核心观点]
   └── 相关度: ★★★☆☆ | 来源: horiz-datasource 🟡
...

📱 微信文章 ([X]条):
1. [日期] [公众号] - [标题]
   └── 相关度: ★★★☆☆ | 来源: horiz-datasource 🟡
...

⚠️ 数据局限提醒:
├── [如有缺失的数据类型/时间范围，明确告知]
├── [建议用Web搜索补充的信息]
└── [需要工程团队补充的数据]
```

### 步骤 4: 数据增强建议

当私域数据不足时:

```
数据增强:

私域数据覆盖情况:
├── 路演纪要: [找到/未找到] [X]条
├── 研报观点: [找到/未找到] [X]条
└── 微信文章: [找到/未找到] [X]条

建议补充数据源:
├── Web搜索: [具体搜索什么关键词]
├── 新浪财经: [需要什么数据]
└── 东方财富: [需要什么数据]

⚠️ 当前数据源缺失 (需工程团队补充):
├── 实时行情数据 → 建议集成 AKShare
├── 财务报表数据 → 建议集成 Tushare/AKShare
├── 宏观经济数据 → 建议集成央行/统计局 API
└── 基金持仓数据 → 建议集成天天基金 API
```

## 数据源

1. **horiz-datasource-api** (MCP Server) — 核心私域数据
2. Web 搜索 — 补充公开数据
