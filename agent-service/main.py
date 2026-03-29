"""
Horiz Quant Researcher — Agent Service
基于 Claude Agent SDK 的 AI 量化研究员服务

启动方式:
    cd horiz-quant-researcher
    pip install -r agent-service/requirements.txt
    uvicorn agent-service.main:app --host 0.0.0.0 --port 8900

环境变量:
    ANTHROPIC_API_KEY  — Claude API 密钥 (必须)
    TAVILY_API_KEY     — Tavily 搜索 API 密钥 (必须)
    DATASOURCE_API_URL — horiz-quant-datasource API 地址 (默认 http://localhost:3001)
"""

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

# 项目根目录 — Agent SDK 会从这里加载 CLAUDE.md / .claude/skills/ / .mcp.json
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)

DATASOURCE_URL = os.getenv("DATASOURCE_API_URL", "http://localhost:3001")

# ---------------------------------------------------------------------------
# Skills & tools 清单
# ---------------------------------------------------------------------------

# SDK 通过 setting_sources=["project"] 自动发现 .claude/skills/ 下的所有技能
# allowed_tools 中的 "Skill" 使 agent 可以调用这些技能

ALLOWED_TOOLS = [
    # 核心能力
    "Skill",                          # 调用 .claude/skills/ 下的技能
    "Agent",                          # 子代理 (用于路由到专项分析)
    # 文件读取 (用于读取 references/ 知识库)
    "Read",
    "Glob",
    "Grep",
    # 代码执行 (用于数据处理和计算)
    "Bash",
    # MCP 数据源
    "mcp__horiz-datasource__*",       # 私域数据: 路演/研报/文章/热股/分析师点评
    "mcp__tavily__*",                 # Web 搜索: 新闻/公司信息/行业动态
    # Playwright (可选，用于抓取财经页面)
    "mcp__playwright__*",
]

# ---------------------------------------------------------------------------
# MCP 服务器配置
# ---------------------------------------------------------------------------

# 方式 A: SDK 自动读取项目根目录的 .mcp.json (推荐)
#   只需 cwd 指向项目根目录即可，无需额外配置
#
# 方式 B: 显式传入 mcp_servers 参数 (用于覆盖或补充 .mcp.json)
#   见下方 get_mcp_servers()

def get_mcp_servers() -> dict:
    """
    返回 MCP 服务器配置 (仅在需要覆盖 .mcp.json 时使用)
    正常情况下 SDK 会自动读取 .mcp.json，此函数作为备选方案。
    """
    return {
        "horiz-datasource": {
            "command": "npx",
            "args": ["-y", "@anthropic-ai/mcp-proxy", "--endpoint", DATASOURCE_URL],
        },
        "tavily": {
            "command": "npx",
            "args": ["-y", "tavily-mcp@latest"],
            "env": {
                "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", ""),
            },
        },
    }


# ---------------------------------------------------------------------------
# Agent Options Builder
# ---------------------------------------------------------------------------

def build_agent_options(
    tools: Optional[list[str]] = None,
    model: str = "claude-sonnet-4-20250514",  # 默认用 sonnet 控成本; 深度分析用 opus
    max_turns: int = 30,
    use_opus: bool = False,
) -> ClaudeAgentOptions:
    """构建 ClaudeAgentOptions"""

    if use_opus:
        model = "claude-opus-4-20250514"

    return ClaudeAgentOptions(
        # 项目目录 — SDK 从这里加载 CLAUDE.md, .claude/skills/, .mcp.json
        cwd=PROJECT_DIR,

        # 加载项目级配置 (skills, commands, settings)
        setting_sources=["project"],

        # 允许使用的工具
        allowed_tools=tools or ALLOWED_TOOLS,

        # 模型
        model=model,

        # 最大交互轮次
        max_turns=max_turns,

        # 权限模式: acceptEdits 允许文件操作, bypassPermissions 跳过确认
        permission_mode="acceptEdits",
    )


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Horiz Quant Researcher",
    description="AI 量化研究员 API — 基于 Claude Agent SDK",
    version="0.1.0",
)

# Job store (生产环境换成 Redis)
jobs: dict[str, dict] = {}


class AgentRequest(BaseModel):
    """研究请求"""
    prompt: str = Field(..., description="用户的研究问题", examples=["帮我深度分析贵州茅台"])
    use_opus: bool = Field(False, description="是否使用 Opus 模型 (深度分析建议开启)")
    session_id: Optional[str] = Field(None, description="会话 ID (用于多轮对话)")
    max_turns: int = Field(30, description="最大交互轮次", ge=1, le=100)


class AgentResponse(BaseModel):
    """研究响应"""
    job_id: str
    status: str


class JobResult(BaseModel):
    """任务结果"""
    job_id: str
    status: str  # queued | running | completed | failed
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    session_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Agent Runner
# ---------------------------------------------------------------------------

async def run_agent(job_id: str, prompt: str, use_opus: bool, max_turns: int, session_id: Optional[str] = None):
    """执行 Agent 任务 (后台运行)"""
    jobs[job_id]["status"] = "running"

    try:
        options = build_agent_options(use_opus=use_opus, max_turns=max_turns)

        # 如果有 session_id，恢复会话
        if session_id:
            options.resume = session_id

        result_text = ""
        captured_session_id = None

        async for message in query(prompt=prompt, options=options):
            # 捕获 session_id (来自第一条 init 消息)
            if hasattr(message, "session_id") and message.session_id:
                captured_session_id = message.session_id

            # 收集最终结果
            if isinstance(message, ResultMessage):
                if message.subtype == "success":
                    result_text = message.result or ""
                elif message.subtype == "error":
                    result_text = f"[Agent Error] {message.error}"

        jobs[job_id].update({
            "status": "completed",
            "result": result_text,
            "completed_at": datetime.now().isoformat(),
            "session_id": captured_session_id,
        })

    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        })


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/research", response_model=AgentResponse)
async def start_research(req: AgentRequest, background_tasks: BackgroundTasks):
    """
    提交研究任务 (异步执行)

    用法:
        curl -X POST http://localhost:8900/api/research \
          -H 'Content-Type: application/json' \
          -d '{"prompt": "帮我深度分析贵州茅台", "use_opus": true}'
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "session_id": req.session_id,
    }

    background_tasks.add_task(
        run_agent, job_id, req.prompt, req.use_opus, req.max_turns, req.session_id
    )

    return AgentResponse(job_id=job_id, status="queued")


@app.get("/api/research/{job_id}", response_model=JobResult)
async def get_research_result(job_id: str):
    """
    查询研究任务结果

    用法:
        curl http://localhost:8900/api/research/{job_id}
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobResult(job_id=job_id, **job)


@app.post("/api/research/sync")
async def research_sync(req: AgentRequest):
    """
    同步执行研究任务 (等待完成后返回，适合短查询)

    用法:
        curl -X POST http://localhost:8900/api/research/sync \
          -H 'Content-Type: application/json' \
          -d '{"prompt": "今天市场怎么样？"}'
    """
    options = build_agent_options(use_opus=req.use_opus, max_turns=req.max_turns)

    if req.session_id:
        options.resume = req.session_id

    result_text = ""
    captured_session_id = None

    async for message in query(prompt=req.prompt, options=options):
        if hasattr(message, "session_id") and message.session_id:
            captured_session_id = message.session_id
        if isinstance(message, ResultMessage) and message.subtype == "success":
            result_text = message.result or ""

    return {
        "result": result_text,
        "session_id": captured_session_id,
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "project_dir": PROJECT_DIR,
        "skills_count": len(list(Path(PROJECT_DIR, ".claude", "skills").glob("*/SKILL.md"))),
        "mcp_json_exists": Path(PROJECT_DIR, ".mcp.json").exists(),
        "claude_md_exists": Path(PROJECT_DIR, "CLAUDE.md").exists(),
    }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    """启动时验证配置"""
    skills_dir = Path(PROJECT_DIR, ".claude", "skills")
    skills_count = len(list(skills_dir.glob("*/SKILL.md")))
    print(f"[Horiz Researcher] Project dir: {PROJECT_DIR}")
    print(f"[Horiz Researcher] Skills loaded: {skills_count}")
    print(f"[Horiz Researcher] CLAUDE.md: {'✅' if Path(PROJECT_DIR, 'CLAUDE.md').exists() else '❌'}")
    print(f"[Horiz Researcher] .mcp.json: {'✅' if Path(PROJECT_DIR, '.mcp.json').exists() else '❌'}")

    # 验证必要的环境变量
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[Horiz Researcher] ⚠️  ANTHROPIC_API_KEY not set!")
    if not os.getenv("TAVILY_API_KEY"):
        print("[Horiz Researcher] ⚠️  TAVILY_API_KEY not set!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8900)
