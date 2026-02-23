"""
秘塔AI搜索 MCP Server
用于接入Claude，提供高质量中文搜索能力。
特别适合商务人物/企业情报搜集。
"""

import os
import json
import httpx
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── 配置 ──────────────────────────────────────────────
METASO_API_KEY = os.environ.get("METASO_API_KEY", "")
METASO_API_URL = "https://api.metaso.cn/search"
DEFAULT_TIMEOUT = 60  # 秘塔深度搜索可能较慢

mcp = FastMCP("metaso_mcp")


# ── 共用工具函数 ──────────────────────────────────────

async def _metaso_request(query: str, mode: str = "concise") -> dict:
    """发送请求到秘塔API"""
    if not METASO_API_KEY:
        return {"error": "METASO_API_KEY 未设置。请在环境变量中配置。"}

    headers = {
        "Authorization": f"Bearer {METASO_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": mode,
        "messages": [
            {"role": "user", "content": query}
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.post(METASO_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"秘塔API返回错误 {e.response.status_code}: {e.response.text[:500]}"}
        except httpx.TimeoutException:
            return {"error": "秘塔API请求超时，请稍后重试。深度模式通常需要更长时间。"}
        except Exception as e:
            return {"error": f"请求失败: {type(e).__name__}: {str(e)[:300]}"}


def _extract_content(response: dict) -> str:
    """从秘塔响应中提取内容"""
    if "error" in response:
        return f"❌ {response['error']}"

    try:
        choices = response.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "未返回内容")
        return "秘塔API返回了空结果"
    except (KeyError, IndexError, TypeError):
        return f"解析响应失败: {json.dumps(response, ensure_ascii=False)[:500]}"


# ── 搜索模式枚举 ──────────────────────────────────────

class SearchMode(str, Enum):
    CONCISE = "concise"       # 简洁模式 - 快速获取要点
    DETAIL = "detail"         # 深入模式 - 详细分析
    RESEARCH = "research"     # 研究模式 - 深度研究报告


# ── Tool 1: 通用搜索 ─────────────────────────────────

class MetasoSearchInput(BaseModel):
    """秘塔搜索输入参数"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="搜索关键词或问题，中文效果最佳。例如：'张三 某某科技 CEO'、'某某公司 最新融资'",
        min_length=1,
        max_length=500,
    )
    mode: SearchMode = Field(
        default=SearchMode.CONCISE,
        description="搜索深度: concise(快速要点) / detail(详细分析) / research(深度研究报告)",
    )


@mcp.tool(
    name="metaso_search",
    annotations={
        "title": "秘塔AI搜索 - 中文信息检索",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def metaso_search(params: MetasoSearchInput) -> str:
    """使用秘塔AI搜索引擎检索中文互联网信息。

    特别适合搜索中国企业信息、商业人物背景、行业动态、政策法规等。
    比普通英文搜索引擎在中文信息检索上更精准、更全面。

    支持三种模式：
    - concise: 快速获取关键要点（默认，适合快速查询）
    - detail: 深入分析，返回更详细的信息
    - research: 研究级报告，适合深度调研

    Args:
        params (MetasoSearchInput): 搜索参数
            - query (str): 搜索关键词
            - mode (SearchMode): 搜索深度

    Returns:
        str: 搜索结果，包含结构化的信息摘要和来源引用
    """
    response = await _metaso_request(params.query, params.mode.value)
    content = _extract_content(response)
    return f"🔍 秘塔搜索结果 [{params.mode.value}模式]\n查询: {params.query}\n\n{content}"


# ── Tool 2: 人物情报搜索（专门优化） ─────────────────

class PersonIntelInput(BaseModel):
    """人物情报搜索输入"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ...,
        description="人物姓名，例如：'王兴'、'张一鸣'",
        min_length=1,
        max_length=50,
    )
    company: Optional[str] = Field(
        default=None,
        description="所在公司名称，帮助精确定位，例如：'美团'、'字节跳动'",
    )
    focus: Optional[str] = Field(
        default=None,
        description="关注重点，例如：'近期动态'、'投资布局'、'公开演讲'",
    )


@mcp.tool(
    name="metaso_person_intel",
    annotations={
        "title": "秘塔人物情报 - 商务人物背景调研",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def metaso_person_intel(params: PersonIntelInput) -> str:
    """搜索中国商务人物的背景信息和近期动态。

    自动构建优化的搜索查询，从多个维度收集人物情报：
    基本背景、职业经历、近期动态、公开言论等。
    特别适合会议前的人物调研。

    Args:
        params (PersonIntelInput): 人物搜索参数
            - name (str): 人物姓名
            - company (Optional[str]): 公司名称
            - focus (Optional[str]): 关注重点

    Returns:
        str: 结构化的人物情报摘要
    """
    # 构建优化的搜索查询
    query_parts = [params.name]
    if params.company:
        query_parts.append(params.company)
    if params.focus:
        query_parts.append(params.focus)
    else:
        query_parts.append("背景 经历 最新动态")

    query = " ".join(query_parts)
    response = await _metaso_request(query, "detail")
    content = _extract_content(response)

    header = f"👤 人物情报: {params.name}"
    if params.company:
        header += f" | {params.company}"

    return f"{header}\n{'='*40}\n\n{content}"


# ── Tool 3: 企业情报搜索（专门优化） ─────────────────

class CompanyIntelInput(BaseModel):
    """企业情报搜索输入"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    company: str = Field(
        ...,
        description="公司名称，例如：'蚂蚁集团'、'比亚迪'",
        min_length=1,
        max_length=100,
    )
    aspect: Optional[str] = Field(
        default=None,
        description="关注维度，例如：'融资历程'、'竞争格局'、'最新产品'、'管理团队'",
    )


@mcp.tool(
    name="metaso_company_intel",
    annotations={
        "title": "秘塔企业情报 - 公司背景与动态调研",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def metaso_company_intel(params: CompanyIntelInput) -> str:
    """搜索中国企业的背景信息、业务动态和行业地位。

    自动构建多维度搜索查询，覆盖公司概况、融资、产品、
    竞争格局、管理团队等。适合商务会议前的企业调研。

    Args:
        params (CompanyIntelInput): 企业搜索参数
            - company (str): 公司名称
            - aspect (Optional[str]): 关注维度

    Returns:
        str: 结构化的企业情报摘要
    """
    query_parts = [params.company]
    if params.aspect:
        query_parts.append(params.aspect)
    else:
        query_parts.append("公司介绍 业务 融资 最新动态 2025 2026")

    query = " ".join(query_parts)
    response = await _metaso_request(query, "detail")
    content = _extract_content(response)

    return f"🏢 企业情报: {params.company}\n{'='*40}\n\n{content}"


# ── 启动入口 ──────────────────────────────────────────

if __name__ == "__main__":
    import sys
    # 支持两种启动模式
    if "--http" in sys.argv:
        port = int(os.environ.get("PORT", 8000))
        mcp.run(transport="streamable_http", port=port)
    else:
        mcp.run()  # 默认 stdio
