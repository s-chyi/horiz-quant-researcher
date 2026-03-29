# horiz-quant-researcher — Engineering Heartbeat

> **执行者**: Engineering Team (Claude Code Agent)
> **执行频率**: 每 30 天执行一次本检查清单
> **目标**: 从零到可交付版本，完成 AI 量化研究员的数据基建、服务整合和质量验证
> **交付标准**: 所有检查项通过 + 端到端测试达标 → 合并到 production

---

## 重要原则

1. **所有开发在 `dev` 分支进行**，禁止直接修改 `master`/`main`
2. **测试环境验证通过后**，才允许创建 PR 合并到正式环境
3. **每次 heartbeat 执行后**，在本文件末尾的执行记录表中填写结果
4. **发现阻塞问题**，立即通知 Nick (CTO)，不要等到下次 heartbeat
5. **所有代码和注释使用简体中文**，commit message 使用 English (conventional commits)

---

## 环境定义

| 环境 | 分支 | 部署地址 | 用途 |
|------|------|---------|------|
| 开发环境 | `dev` | localhost | 本地开发和单元测试 |
| 测试环境 | `dev` | staging VM (TBD) | 集成测试、端到端验证 |
| 正式环境 | `master` | production VM | 面向用户的服务 |

**合并流程**: `feature/* → dev → staging 验证 → PR to master → production`

---

## Phase 0: 基础设施就绪检查 (首次执行)

> 目标: 确认项目骨架完整，开发环境可正常运行

### 0.1 项目结构验证

- [ ] 克隆仓库: `git clone https://github.com/s-chyi/horiz-quant-researcher.git`
- [ ] 切换到 dev 分支: `git checkout -b dev` (首次) 或 `git checkout dev`
- [ ] 确认 `.claude/skills/` 下有 21 个技能目录，每个含 `SKILL.md`
- [ ] 确认 `.claude/commands/` 下有 8 个命令目录，每个含 `COMMAND.md`
- [ ] 确认 `references/` 下有 6 个 `.md` 参考文档
- [ ] 确认 `CLAUDE.md` 存在且目录结构章节指向 `.claude/` 路径
- [ ] 确认 `.mcp.json` 存在且包含 horiz-datasource、tavily、playwright 三个 MCP 服务器
- [ ] 确认 `agent-service/` 包含 `main.py`、`test_local.py`、`requirements.txt`

```bash
# 快速验证命令
python agent-service/test_local.py
```

预期输出: 所有项显示 ✅，环境变量提示设置

### 0.2 环境变量配置

- [ ] 创建 `.env` 文件 (已在 .gitignore 中):
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  TAVILY_API_KEY=tvly-...
  DATASOURCE_API_URL=http://localhost:3001
  ```
- [ ] 验证 ANTHROPIC_API_KEY 可正常调用 Claude API
- [ ] 验证 TAVILY_API_KEY 可正常搜索
- [ ] 验证 horiz-quant-datasource 服务可访问 (http://localhost:3001/health)

### 0.3 Agent SDK 基础连通测试

- [ ] 安装依赖: `pip install -r agent-service/requirements.txt`
- [ ] 运行连通测试: `python agent-service/test_local.py --run`
- [ ] 确认 Agent 能正常返回中文回答
- [ ] 确认 Agent 能调用 Tavily 搜索 (观察日志中是否出现 mcp__tavily 调用)
- [ ] 确认 Agent 能读取 references/ 下的知识库文件

**Phase 0 通过标准**: test_local.py 全 ✅ + `--run` 模式返回有意义的中文分析

---

## Phase 1: 核心数据 API (🔴 高优先级)

> 目标: 让 stock-deep-analysis、earnings-review、valuation-framework 等核心技能拿到真实数据
> 参考: DATA_GAP_REPORT.md 第一阶段

### 1.1 实时行情 API

**需要在 horiz-quant-datasource 中新增** (或新建 Python 数据微服务):

- [ ] `GET /api/quote/realtime?codes=SH600519,SZ000001`
  - 返回: 股票名称、现价、涨跌幅、成交量、成交额、换手率、市盈率、市净率
  - 数据源: AKShare `ak.stock_zh_a_spot_em()` 或新浪实时 API
  - 响应时间要求: < 3 秒
- [ ] `GET /api/quote/index?codes=SH000300,SH000905,SZ399006`
  - 返回: 指数名称、点位、涨跌幅、成交额
- [ ] 编写单元测试: 至少覆盖 5 只主流个股 + 3 个主要指数
- [ ] 测试环境验证: 连续 3 天无报错

### 1.2 历史 K 线 API

- [ ] `GET /api/quote/kline?code=SH600519&period=daily&start=2024-01-01&end=2025-03-30&adjust=qfq`
  - 返回: 日期、开盘、最高、最低、收盘、成交量、成交额、换手率
  - 支持 period: daily / weekly / monthly
  - 支持 adjust: qfq (前复权) / hfq (后复权) / none
  - 数据源: AKShare `ak.stock_zh_a_hist()`
- [ ] 数据落库 PostgreSQL，增量更新 (每日收盘后)
- [ ] 编写单元测试: 验证复权因子正确性 (对比东方财富手动查询)
- [ ] 测试环境验证: 至少 3000 只 A 股有完整 5 年日 K 数据

### 1.3 财务报表 API

- [ ] `GET /api/financial/statements?code=SH600519&type=income&periods=8`
  - type: income (利润表) / balance (资产负债表) / cashflow (现金流量表)
  - periods: 返回最近 N 个报告期
  - 数据源: AKShare `ak.stock_financial_report_sina()`
- [ ] `GET /api/financial/indicators?code=SH600519&periods=8`
  - 返回: ROE、ROA、毛利率、净利率、资产负债率、流动比率、营收增速、净利增速
  - 数据源: AKShare 财务指标接口
- [ ] 数据落库: 全 A 股至少 5 年 (20 个季度) 财报数据
- [ ] 编写单元测试: 验证贵州茅台 2024 年报关键指标与公开数据一致
- [ ] 测试环境验证: 财报数据覆盖率 ≥ 95% 的 A 股上市公司

### 1.4 现有数据质量修复

- [ ] 回填 2025-03-23 之前 1,201 条路演纪要的 content 字段
- [ ] 启动 hot-stocks 和 analyst-comments 的每日定时采集任务
- [ ] 验证 articles 去重逻辑 (当前 ~976 条可能有重复)
- [ ] 验证 analyst-comments 字段标准化 (评级映射统一)

### 1.5 MCP SSE 端点暴露

所有新 API 必须同时暴露 REST 和 MCP SSE 端点，以便 Agent SDK 直接调用:

- [ ] 在 `.mcp.json` 中注册新数据源:
  ```json
  {
    "horiz-market-data": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-proxy", "--endpoint", "http://localhost:3002"]
    }
  }
  ```
- [ ] 或扩展现有 horiz-datasource 端点以覆盖新 API
- [ ] 验证 Agent SDK 可通过 `mcp__horiz-datasource__*` 工具名称调用新 API

**Phase 1 通过标准**:
```
✅ 实时行情 API 响应 < 3s，覆盖全 A 股
✅ K 线数据覆盖 ≥ 3000 只 A 股 × 5 年
✅ 财务三表覆盖 ≥ 95% A 股 × 20 季度
✅ 路演纪要 content 回填完成
✅ 定时采集任务稳定运行 7 天无中断
✅ Agent SDK 可通过 MCP 调用所有新 API
```

---

## Phase 2: 增强数据 (🟡 中优先级)

> 目标: 让 bull-bear-debate、risk-matrix、fund-flow、comparative-analysis 达到专业水准
> 参考: DATA_GAP_REPORT.md 第二阶段

### 2.1 分析师一致预期

- [ ] `GET /api/consensus/forecast?code=SH600519`
  - 返回: 一致预期 EPS/营收/净利 (今年+明年+后年)、评级分布、目标价区间、覆盖分析师数
  - 数据源: 东方财富一致预期页面爬取 或 AKShare
- [ ] 数据落库 + 每周更新
- [ ] 单元测试: 与东方财富网页手动核对

### 2.2 北向资金

- [ ] `GET /api/fund-flow/northbound?date=2025-03-28`
  - 返回: 沪股通/深股通净买入额、前 10 大活跃股及净买入额
- [ ] `GET /api/fund-flow/northbound/stock?code=SH600519&days=30`
  - 返回: 个股北向持仓变化时序
- [ ] 数据源: 东方财富 / AKShare `ak.stock_hsgt_north_net_flow_in_em()`
- [ ] 每日收盘后自动采集

### 2.3 融资融券

- [ ] `GET /api/fund-flow/margin?code=SH600519&days=30`
  - 返回: 融资余额、融券余额、融资买入额、融资偿还额
- [ ] 市场级汇总: `GET /api/fund-flow/margin/market?days=30`
- [ ] 数据源: AKShare `ak.stock_margin_detail_szse()`

### 2.4 行业分类与可比公司

- [ ] `GET /api/industry/classify?code=SH600519`
  - 返回: 申万一级/二级/三级行业、中信行业、同行业公司列表
- [ ] `GET /api/industry/peers?code=SH600519&level=2`
  - 返回: 同申万二级行业的所有公司及关键指标
- [ ] 数据源: AKShare `ak.stock_board_industry_name_em()`
- [ ] 数据落库 + 每季度更新

### 2.5 大宗交易与股东数据

- [ ] `GET /api/holder/top10?code=SH600519&periods=4`
  - 返回: 十大股东/十大流通股东，含持股数量和变化
- [ ] `GET /api/holder/block-trade?code=SH600519&days=90`
  - 返回: 大宗交易记录 (日期、价格、折溢价、买卖方营业部)
- [ ] `GET /api/holder/count?code=SH600519&periods=8`
  - 返回: 股东户数变化趋势
- [ ] 数据源: AKShare

**Phase 2 通过标准**:
```
✅ 一致预期数据覆盖沪深 300 成分股
✅ 北向资金每日自动采集，延迟 < 1 小时
✅ 融资融券数据可查询任意 A 股近 90 天
✅ 行业分类覆盖全 A 股，可比公司自动匹配
✅ 大宗交易 + 股东数据覆盖全 A 股
✅ 所有新 API 通过 MCP 可被 Agent 调用
```

---

## Phase 3: 进阶数据与全面覆盖 (🟢 低优先级)

> 目标: 数据维度全面超越 PaiPai
> 参考: DATA_GAP_REPORT.md 第三阶段

### 3.1 宏观经济数据

- [ ] `GET /api/macro/indicator?name=pmi&months=24`
  - 支持指标: GDP、PMI、CPI、PPI、M2、社融、工业增加值、固投、社零、进出口
- [ ] `GET /api/macro/rate?type=lpr&months=24`
  - 支持: LPR (1Y/5Y)、MLF、DR007、国债收益率 (1Y/5Y/10Y)、USD/CNY
- [ ] 数据源: AKShare 宏观经济接口

### 3.2 ETF 与基金数据

- [ ] `GET /api/fund/etf?code=SH510300&days=30`
  - 返回: ETF 行情、折溢价、份额变化
- [ ] `GET /api/fund/holding?code=SH600519`
  - 返回: 持有该股的主动基金列表及持仓比例

### 3.3 AlphaPai 行业研究入库

- [ ] 筛选 AlphaPai type=301 行业研究总结 (原始 3.77M 条)
  - 筛选规则: 最近 1 年 + 有研究结论的条目
  - 预计入库: ~50,000 条
- [ ] API: `GET /api/industry-research?industry=白酒&days=90`

### 3.4 上市公司公告

- [ ] `GET /api/announcement?code=SH600519&days=90&type=all`
  - type: all / financial / major / holder
- [ ] 数据源: 巨潮资讯网

**Phase 3 通过标准**:
```
✅ 宏观数据覆盖 references/macro-indicators.md 中列举的所有指标
✅ ETF 份额数据每日更新
✅ 行业研究入库 ≥ 30,000 条有效记录
✅ 公告数据可查询任意 A 股近 1 年
```

---

## Phase 4: Agent 服务整合与端到端测试

> 目标: Agent SDK 服务能正确调用所有数据源 + 所有技能，输出质量达到交付标准

### 4.1 Agent Service 集成测试

- [ ] 启动 agent-service: `uvicorn agent-service.main:app --port 8900`
- [ ] 健康检查通过: `curl http://localhost:8900/health`
  - 返回: skills_count=21, mcp_json_exists=true, claude_md_exists=true
- [ ] 同步接口测试:
  ```bash
  curl -X POST http://localhost:8900/api/research/sync \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "帮我简要分析一下贵州茅台最近的表现"}'
  ```
  - 预期: 返回包含实际股价数据的分析 (非"我无法获取实时数据"之类的回避)
- [ ] 异步接口测试:
  ```bash
  # 提交
  curl -X POST http://localhost:8900/api/research \
    -d '{"prompt": "帮我深度分析贵州茅台", "use_opus": true}'
  # 轮询
  curl http://localhost:8900/api/research/{job_id}
  ```
  - 预期: status 从 queued → running → completed，result 非空

### 4.2 技能调用覆盖测试

以下每个测试用例必须验证 Agent 确实调用了对应的技能和数据 API:

| # | 测试 Prompt | 预期调用的技能 | 预期数据源 | 通过标准 |
|---|------------|---------------|-----------|---------|
| T1 | "帮我深度分析贵州茅台" | stock-deep-analysis | 行情+财报+研报 | 包含5维度分析+数据标注 |
| T2 | "茅台最新财报怎么看" | earnings-review | 财报API+分析师预期 | 包含超预期/不及预期判断 |
| T3 | "白酒产业链分析" | industry-chain | 行业分类+可比公司 | 包含上中下游拆解 |
| T4 | "宁德时代现在能买吗" | bull-bear-debate | 行情+财报+北向+研报 | 包含多空双方论点+仲裁 |
| T5 | "比亚迪现在贵不贵" | valuation-framework | 财报+一致预期 | ≥3种估值方法 |
| T6 | "帮我检查恒大的风险" | risk-matrix | 财报+公告+新闻 | 概率-影响矩阵 |
| T7 | "今天市场怎么样" | morning-briefing | 指数行情+北向+新闻 | 全球市场+资金+策略 |
| T8 | "格力和美的哪个好" | comparative-analysis | 双标的行情+财报+行业 | 7维度对比表格 |
| T9 | "降息对A股影响" | macro-transmission | 宏观数据+利率 | 传导链+行业映射 |
| T10 | "帮我看一下最近的路演" | roadshow-analysis | 路演纪要API | 关键信息+交叉验证 |

- [ ] T1-T10 全部通过 (Agent 返回有实质内容，非模板回避)
- [ ] 每个测试结果中包含 🟢🟡🔴 数据来源标注
- [ ] 每个测试结果通过质量门控 (quality-gate skill) ≥ 85 分

### 4.3 质量基准测试 (vs PaiPai)

选择 5 个标准问题，同时向 PaiPai 和本系统提问，人工对比:

| # | 问题 | 评分维度 |
|---|------|---------|
| Q1 | "帮我深度分析贵州茅台" | 分析深度、数据引用、推理链完整度 |
| Q2 | "宁德时代能不能买" | 多空平衡、风险识别、结论明确度 |
| Q3 | "今天A股怎么样" | 时效性、覆盖面、策略实用性 |
| Q4 | "比亚迪和特斯拉对比" | 比较框架、数据对称性、结论逻辑 |
| Q5 | "AI产业链投资机会" | 行业深度、公司筛选、催化剂识别 |

- [ ] 5 个问题中至少 4 个评分 ≥ PaiPai (由 Nick 评审)
- [ ] 未达标的问题记录原因并制定改进计划

### 4.4 性能与稳定性测试

- [ ] 同步接口平均响应时间 < 120 秒 (Sonnet 模型)
- [ ] 异步接口 (Opus 模型) 平均完成时间 < 300 秒
- [ ] 连续运行 24 小时无崩溃
- [ ] 并发 3 个请求时不互相阻塞 (FastAPI 后台任务)
- [ ] MCP 服务器连接失败时 Agent 能优雅降级 (fallback 到 Web 搜索)

---

## Phase 5: 交付准备

> 目标: 从 dev 合并到 master，部署到正式环境

### 5.1 代码审查清单

- [ ] 无硬编码的 API Key 或密码
- [ ] 所有环境变量通过 `.env` 读取，有默认值或明确报错
- [ ] `requirements.txt` 版本锁定 (使用 `pip freeze` 生成精确版本)
- [ ] 无未使用的 import 或 dead code
- [ ] 关键函数有 docstring (简体中文)

### 5.2 文档更新

- [ ] README.md 反映最新架构和使用方式
- [ ] CLAUDE.md 数据源配置章节更新 (新增的 API 全部列入)
- [ ] DATA_GAP_REPORT.md 更新各缺口状态 (标记已完成项)
- [ ] agent-service/README.md 或 docstring 说明部署步骤

### 5.3 部署配置

- [ ] 编写 `docker-compose.yml` 或 PM2 ecosystem config:
  ```yaml
  services:
    agent-service:
      build: ./agent-service
      ports: ["8900:8900"]
      env_file: .env
      depends_on: [horiz-datasource]
    horiz-datasource:
      # 现有数据源服务
      ports: ["3001:3001"]
  ```
- [ ] 编写健康检查脚本 (检查所有服务 + MCP 连通性)
- [ ] 配置日志收集 (至少 stdout/stderr 持久化)

### 5.4 正式环境发布

- [ ] 创建 PR: `dev → master`，PR 描述包含:
  - 所有已完成的 Phase 清单
  - T1-T10 测试结果截图或日志
  - Q1-Q5 vs PaiPai 对比结果
  - 性能测试数据
- [ ] Nick (CTO) 审核通过
- [ ] 合并到 master
- [ ] 部署到正式环境
- [ ] 验证正式环境健康检查通过
- [ ] 在正式环境执行 T1、T3、T7 三个烟雾测试

**交付完成标准**:
```
✅ Phase 0-4 所有检查项通过
✅ T1-T10 技能覆盖测试全部通过
✅ Q1-Q5 中至少 4 个 ≥ PaiPai
✅ 性能指标达标
✅ PR 审核通过并合并到 master
✅ 正式环境烟雾测试通过
```

---

## 每次 Heartbeat 执行流程

每 30 天执行以下步骤:

```
1. git pull origin dev
2. 运行 python agent-service/test_local.py → 确认基础结构
3. 按当前所在 Phase 逐项检查
4. 对已完成项打 ✅，未完成项记录阻塞原因
5. 运行适用的测试用例 (T1-T10 中已有数据支撑的)
6. 在下方执行记录表填写本次结果
7. 如果当前 Phase 全部通过，进入下一 Phase
8. 如果所有 Phase 通过，启动 Phase 5 交付流程
```

---

## 执行记录

| 日期 | 执行者 | 当前 Phase | 已完成项 | 阻塞项 | 下次目标 | 备注 |
|------|--------|-----------|---------|--------|---------|------|
| 2026-04-?? | Engineer | Phase 0 | — | — | Phase 0 全部通过 | 首次执行 |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

---

## 附录: API 响应格式规范

所有新 API 统一使用以下响应格式:

```json
// 成功
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-03-30T10:00:00+08:00"
}

// 错误
{
  "code": 40001,
  "message": "invalid stock code",
  "data": null,
  "timestamp": "2026-03-30T10:00:00+08:00"
}
```

错误码规范:
| 范围 | 含义 |
|------|------|
| 0 | 成功 |
| 40000-40099 | 参数错误 |
| 40100-40199 | 认证错误 |
| 50000-50099 | 服务内部错误 |
| 50100-50199 | 上游数据源错误 |

## 附录: PostgreSQL 表结构参考

```sql
-- 日K线数据
CREATE TABLE stock_kline_daily (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(10) NOT NULL,    -- SH600519
    trade_date  DATE NOT NULL,
    open        DECIMAL(12,4),
    high        DECIMAL(12,4),
    low         DECIMAL(12,4),
    close       DECIMAL(12,4),
    volume      BIGINT,                  -- 成交量(股)
    amount      DECIMAL(16,2),           -- 成交额(元)
    turnover    DECIMAL(8,4),            -- 换手率
    adjust_flag SMALLINT DEFAULT 0,      -- 0:未复权 1:前复权 2:后复权
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(code, trade_date, adjust_flag)
);
CREATE INDEX idx_kline_code_date ON stock_kline_daily(code, trade_date);

-- 财务报表
CREATE TABLE stock_financial (
    id             BIGSERIAL PRIMARY KEY,
    code           VARCHAR(10) NOT NULL,
    report_date    DATE NOT NULL,         -- 报告期 (2024-12-31)
    report_type    VARCHAR(20) NOT NULL,  -- income/balance/cashflow/indicator
    data           JSONB NOT NULL,        -- 财务数据 (灵活schema)
    publish_date   DATE,                  -- 实际披露日期
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(code, report_date, report_type)
);
CREATE INDEX idx_financial_code ON stock_financial(code, report_date);

-- 分析师一致预期
CREATE TABLE consensus_forecast (
    id             BIGSERIAL PRIMARY KEY,
    code           VARCHAR(10) NOT NULL,
    forecast_year  INT NOT NULL,
    eps            DECIMAL(10,4),
    revenue        DECIMAL(16,2),         -- 亿元
    net_profit     DECIMAL(16,2),         -- 亿元
    target_price   DECIMAL(10,2),
    rating_buy     INT,                   -- 买入评级数
    rating_hold    INT,                   -- 持有评级数
    rating_sell    INT,                   -- 卖出评级数
    analyst_count  INT,
    updated_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(code, forecast_year)
);

-- 北向资金
CREATE TABLE northbound_flow (
    id             BIGSERIAL PRIMARY KEY,
    trade_date     DATE NOT NULL,
    channel        VARCHAR(10) NOT NULL,  -- sh_connect / sz_connect
    net_buy_amount DECIMAL(16,2),         -- 净买入(亿元)
    buy_amount     DECIMAL(16,2),
    sell_amount    DECIMAL(16,2),
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, channel)
);

-- 北向个股持仓
CREATE TABLE northbound_holding (
    id             BIGSERIAL PRIMARY KEY,
    trade_date     DATE NOT NULL,
    code           VARCHAR(10) NOT NULL,
    holding_shares BIGINT,                -- 持股数量
    holding_ratio  DECIMAL(8,4),          -- 占流通盘比例
    net_change     BIGINT,                -- 较上日变化
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, code)
);
```

---

*本文件由 Claude Opus 4.6 生成，首次创建: 2026-03-30*
*GitHub: https://github.com/s-chyi/horiz-quant-researcher*
