"""
快速测试脚本 — 在本地验证 Agent SDK + Skills 是否正常工作

用法:
    cd horiz-quant-researcher
    pip install claude-agent-sdk python-dotenv
    python agent-service/test_local.py

环境变量:
    ANTHROPIC_API_KEY=sk-ant-...
    TAVILY_API_KEY=tvly-...
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 确保项目根目录正确
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)


async def test_health():
    """验证项目结构是否正确"""
    print("=" * 60)
    print("  Horiz Quant Researcher — 配置验证")
    print("=" * 60)

    # 检查 CLAUDE.md
    claude_md = Path(PROJECT_DIR, "CLAUDE.md")
    print(f"\n  CLAUDE.md:       {'✅ 存在' if claude_md.exists() else '❌ 缺失'}")

    # 检查 .mcp.json
    mcp_json = Path(PROJECT_DIR, ".mcp.json")
    print(f"  .mcp.json:       {'✅ 存在' if mcp_json.exists() else '❌ 缺失'}")

    # 检查 skills
    skills_dir = Path(PROJECT_DIR, ".claude", "skills")
    skills = list(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    print(f"  .claude/skills:  {'✅' if skills else '❌'} {len(skills)} 个技能")
    for s in sorted(skills):
        print(f"    ├── {s.parent.name}")

    # 检查 commands
    commands_dir = Path(PROJECT_DIR, ".claude", "commands")
    commands = list(commands_dir.glob("*/COMMAND.md")) if commands_dir.exists() else []
    print(f"  .claude/commands: {'✅' if commands else '❌'} {len(commands)} 个命令")
    for c in sorted(commands):
        print(f"    ├── /{c.parent.name}")

    # 检查 references
    refs_dir = Path(PROJECT_DIR, "references")
    refs = list(refs_dir.glob("*.md")) if refs_dir.exists() else []
    print(f"  references:      {'✅' if refs else '❌'} {len(refs)} 个参考文档")

    # 检查环境变量
    print(f"\n  ANTHROPIC_API_KEY: {'✅ 已设置' if os.getenv('ANTHROPIC_API_KEY') else '❌ 未设置'}")
    print(f"  TAVILY_API_KEY:   {'✅ 已设置' if os.getenv('TAVILY_API_KEY') else '❌ 未设置'}")

    print("\n" + "=" * 60)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n  ⚠️  请设置 ANTHROPIC_API_KEY 后再运行 Agent 测试")
        return False
    return True


async def test_agent_query():
    """测试 Agent SDK 调用"""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
    except ImportError:
        print("\n  ❌ claude-agent-sdk 未安装")
        print("     请运行: pip install claude-agent-sdk")
        return

    print("\n  🚀 启动 Agent SDK 测试...")
    print("  测试 Prompt: '今天A股整体情况如何？简要概述即可'")
    print("  (使用 Sonnet 模型, max_turns=5)")
    print("-" * 60)

    options = ClaudeAgentOptions(
        cwd=PROJECT_DIR,
        setting_sources=["project"],
        allowed_tools=[
            "Skill",
            "Read",
            "Glob",
            "Grep",
            "mcp__tavily__*",
        ],
        model="claude-sonnet-4-20250514",
        max_turns=5,
        permission_mode="acceptEdits",
    )

    result = ""
    async for message in query(
        prompt="今天A股整体情况如何？简要概述即可，控制在200字以内",
        options=options,
    ):
        if isinstance(message, ResultMessage):
            if message.subtype == "success":
                result = message.result or "(empty)"
            elif message.subtype == "error":
                result = f"[Error] {message.error}"
            print(f"\n  Agent 返回 ({message.subtype}):")
            print(f"  {result[:500]}")

    print("\n" + "=" * 60)
    print("  ✅ Agent SDK 测试完成")


async def main():
    ok = await test_health()
    if ok and "--run" in sys.argv:
        await test_agent_query()
    elif ok:
        print("\n  配置验证通过! 添加 --run 参数执行 Agent SDK 调用测试:")
        print("    python agent-service/test_local.py --run")


if __name__ == "__main__":
    asyncio.run(main())
