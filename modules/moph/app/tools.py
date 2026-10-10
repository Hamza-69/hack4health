"""MCP tools the agent calls to answer questions about the Ministry of Public Health.

Every result says whether anything was found and carries official source links. Searches are
logged anonymously (tool, query, result count) so admins can see what people ask.
"""

from typing import Annotated

from h4h import ToolError
from mcp.server.mcpserver import Context
from pydantic import Field

from app.catalog import FacilityType, get_catalog
from app.embeddings import embed_query
from app.models import Gap, SearchLog
from app.module import module

Query = Annotated[
    str,
    Field(description="The user's question or its key terms, in Arabic or English, e.g. 'how to get cancer medicine from the ministry'"),
]


async def _catalog(ctx: Context):
    await module.user(ctx)  # only calls that come through the core
    catalog = await get_catalog()
    if not catalog.services:
        raise ToolError("ministry data is not loaded yet; an admin must load it from the Ministry Info page")
    return catalog


async def _log(tool: str, query: str, results: int) -> None:
    async with module.db() as session:
        session.add(SearchLog(tool=tool, query=query[:500], results=results))
        await session.commit()


def _answer(catalog, results: list, **extra) -> dict:
    out = {"found": bool(results), "results": results, "data_as_of": catalog.data_date, **extra}
    if not results:
        out["fallback_contacts"] = catalog.contacts()
    return out


@module.mcp.tool()
async def search_services(query: Query, ctx: Context) -> dict:
    """Find ministry services and procedures (المعاملات): how to apply for something, required
    documents, eligibility, the responsible office with address/email/hours, fees, processing time,
    forms and the official page. Use for "how do I get/apply for/register...", medicine assistance,
    licences, permits, registries, certificates."""
    catalog = await _catalog(ctx)
    results = catalog.search_services(query, await embed_query(query))
    await _log("search_services", query, len(results))
    return _answer(catalog, results)


@module.mcp.tool()
async def get_service(service_id: int, ctx: Context) -> dict:
    """Full details of one service by its service_id (from search_services)."""
    catalog = await _catalog(ctx)
    service = catalog.get_service(service_id)
    if service is None:
        raise ToolError(f"no service {service_id}")
    return service


@module.mcp.tool()
async def get_official_facts(
    ctx: Context,
    query: Annotated[str, Field(description="Topic keywords; leave empty to get every fact")] = "",
) -> dict:
    """Curated, dated rules: what the ministry covers or pays and for whom (hospitalization, emergency,
    dialysis, transplants, cancer and chronic-disease medicines, displaced people, free programmes),
    and its hotlines. The most authoritative source: check it first for coverage and eligibility."""
    catalog = await _catalog(ctx)
    results = catalog.search_facts(query, await embed_query(query))
    await _log("get_official_facts", query, len(results))
    return _answer(catalog, results)


@module.mcp.tool()
async def search_ministry_site(query: Query, ctx: Context) -> dict:
    """Search the ministry website's pages and news: programmes, campaigns, health guidance,
    announcements and decisions. Each result has its date (when the site shows one) and URL."""
    catalog = await _catalog(ctx)
    results = catalog.search_pages(query, await embed_query(query))
    await _log("search_ministry_site", query, len(results))
    return _answer(catalog, results)


@module.mcp.tool()
async def lookup_drug(
    name: Annotated[str, Field(description="Brand or ingredient name in Latin letters, e.g. 'panadol' or 'paracetamol'")],
    ctx: Context,
) -> dict:
    """Look up a medicine in the ministry's National Drugs Database: official public price, form,
    dosage, cheaper equivalents with the same ingredient, strength and form, and whether it is on a
    list of medicines the ministry provides for free."""
    catalog = await _catalog(ctx)
    result = catalog.lookup_drug(name)
    await _log("lookup_drug", name, len(result["drugs"]))
    return _answer(catalog, result.pop("drugs"), **result)


@module.mcp.tool()
async def find_facilities(
    ctx: Context,
    type: Annotated[FacilityType | None, Field(description="Kind of facility")] = None,
    area: Annotated[str | None, Field(description="Governorate or caza (qada), in English or Arabic, e.g. 'Akkar', 'زحلة'")] = None,
    name: Annotated[str | None, Field(description="Part of the facility's name")] = None,
    limit: Annotated[int, Field(ge=1, le=25)] = 10,
) -> dict:
    """Find licensed health facilities from the ministry's Facility Locator by type, area and/or
    name: hospitals, primary health care centres, pharmacies, radiology labs, physiotherapy centres,
    dental labs, nurseries. Gives phone, caza and the official page. There are no street addresses."""
    if not (type or area or name):
        raise ToolError("give at least one of type, area or name")
    catalog = await _catalog(ctx)
    result = catalog.find_facilities(type=type, area=area, name=name, limit=limit)
    await _log("find_facilities", " | ".join(filter(None, [type, area, name])), result["total"])
    return _answer(catalog, result.pop("facilities"), **result)


@module.mcp.tool()
async def get_contacts(ctx: Context) -> dict:
    """The ministry's hotlines, for when the user needs to talk to someone or nothing else answers."""
    catalog = await _catalog(ctx)
    return {"contacts": catalog.contacts()}


@module.mcp.tool()
async def report_unanswered(
    question: Annotated[str, Field(description="The user's question, in their words, without personal details")],
    reason: Annotated[str, Field(description="What was missing, e.g. 'no service found for ...'")],
    ctx: Context,
) -> str:
    """Record a question our data could not answer, so the team can add the information.
    Call it whenever you tell the user you do not have the information."""
    await module.user(ctx)
    async with module.db() as session:
        session.add(Gap(question=question[:2000], reason=reason[:1000]))
        await session.commit()
    return "recorded"
