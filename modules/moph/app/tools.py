"""MCP tools the agent calls to answer questions about the Ministry of Public Health.

Every result says whether anything was found and carries official source links. Searches are
logged anonymously (tool, query, result count) so admins can see what people ask, and so are the
rumours the agent checks.
"""

from typing import Annotated, Literal

from h4h import ToolError
from mcp.server.mcpserver import Context
from pydantic import Field
from sqlalchemy import select

from app.catalog import Catalog, FacilityType, get_catalog
from app.models import Claim, Gap, SearchLog
from app.module import module
from app.search_index import SearchUnavailable
from app.text import claim_key

Query = Annotated[
    str,
    Field(description="The user's question or its key terms, in Arabic: the ministry's content is Arabic, so translate English or Arabizi first, e.g. 'كيف أحصل على أدوية السرطان من الوزارة'"),
]


async def _catalog(ctx: Context):
    await module.user(ctx)  # only calls that come through the core
    catalog = await get_catalog()
    if not catalog.services:
        raise ToolError("ministry data is not loaded yet; an admin must load it from the Ministry Info page")
    return catalog


async def _search(results):
    """Await a search; a search outage reaches the agent as a tool error it can explain."""
    try:
        return await results
    except SearchUnavailable as e:
        raise ToolError(f"{e}. Meanwhile point the user to the hotline 1214.") from e


async def _search_answer(catalog, tool: str, query: str, results: list) -> dict:
    """Search always returns the closest records; only a strong match counts as found."""
    strong = sum(r["match"] == "strong" for r in results)
    await _log(tool, query, strong)
    return _answer(catalog, results, found=bool(strong))


async def _log(tool: str, query: str, results: int) -> None:
    async with module.db() as session:
        session.add(SearchLog(tool=tool, query=query[:500], results=results))
        await session.commit()


def _answer(catalog, results: list, found: bool | None = None, **extra) -> dict:
    found = bool(results) if found is None else found
    out = {"found": found, "results": results, "data_as_of": catalog.data_date, **extra}
    if not found:
        out["fallback_contacts"] = catalog.contacts()
    return out


@module.mcp.tool()
async def search_services(query: Query, ctx: Context) -> dict:
    """Find ministry services and procedures (المعاملات): how to apply for something, required
    documents, eligibility, the responsible office with address/email/hours, fees, processing time,
    forms and the official page. Use for "how do I get/apply for/register...", medicine assistance,
    licences, permits, registries, certificates."""
    catalog = await _catalog(ctx)
    results = await _search(catalog.search_services(query))
    return await _search_answer(catalog, "search_services", query, results)


@module.mcp.tool()
async def get_service(service_id: int, ctx: Context) -> dict:
    """Full details of one service by its service_id (from search_services)."""
    catalog = await _catalog(ctx)
    service = catalog.get_service(service_id)
    if service is None:
        raise ToolError(f"no service {service_id}")
    return service


@module.mcp.tool()
async def search_ministry_site(query: Query, ctx: Context) -> dict:
    """Search the ministry website and its documents: pages and news (programmes, campaigns, health
    guidance, announcements, what the ministry covers and for whom) and the files linked from them
    (laws, ministerial decisions, circulars, memos, guidelines, reports). Each result has its kind
    (page, news or document), date when known, text and URL; documents also say which page links
    to them."""
    catalog = await _catalog(ctx)
    results = await _search(catalog.search_site(query))
    return await _search_answer(catalog, "search_ministry_site", query, results)


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
    area: Annotated[str | None, Field(description="Governorate, caza (qada) or a common neighbourhood or town, in English or Arabic, e.g. 'Akkar', 'زحلة', 'Hamra'")] = None,
    name: Annotated[str | None, Field(description="Part of the facility's name")] = None,
    lat: Annotated[float | None, Field(ge=-90, le=90, description="Latitude of a location the user shared, e.g. 33.8963")] = None,
    lon: Annotated[float | None, Field(ge=-180, le=180, description="Longitude of that location, e.g. 35.4826")] = None,
    limit: Annotated[int, Field(ge=1, le=25)] = 10,
) -> dict:
    """Find licensed health facilities from the ministry's Facility Locator by type, area and/or
    name, or near a location the user shared (lat and lon, used when no area is given): hospitals,
    primary health care centres, pharmacies, radiology labs, physiotherapy centres, dental labs,
    nurseries. Gives the address (in Arabic), phone, caza, the official page and a Google Maps link.
    A location is matched to its caza (area_from_location), not to distances. There is no stock:
    for whether a pharmacy has a medicine, give pharmacies in the area to call."""
    if (lat is None) != (lon is None):
        raise ToolError("give both lat and lon")
    if not (type or area or name or lat is not None):
        raise ToolError("give at least one of type, area, name or lat and lon")
    catalog = await _catalog(ctx)
    result = catalog.find_facilities(type=type, area=area, name=name, limit=limit, lat=lat, lon=lon)
    where = result.get("area_from_location") and f"location: {result['area_from_location']}"
    await _log("find_facilities", " | ".join(filter(None, [type, area or where, name])), result["total"])
    return _answer(catalog, result.pop("facilities"), **result)


@module.mcp.tool()
async def get_contacts(ctx: Context) -> dict:
    """The ministry's hotlines, for when the user needs to talk to someone or nothing else answers."""
    await module.user(ctx)
    return {"contacts": Catalog.contacts()}


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


@module.mcp.tool()
async def report_claim(
    claim: Annotated[str, Field(description="The claim as one short neutral sentence in Arabic, without personal details, e.g. 'الوزارة تغطي عمليات زرع الأعضاء'")],
    verdict: Annotated[
        Literal["confirmed", "contradicted", "not_found"],
        Field(description="confirmed: a ministry statement says it; contradicted: a newer ministry statement says otherwise; not_found: the ministry has published nothing on it"),
    ],
    ctx: Context,
    source_url: Annotated[str | None, Field(description="The official link you gave the user")] = None,
    source_date: Annotated[str | None, Field(description="That statement's date, YYYY-MM-DD")] = None,
) -> str:
    """Record a forwarded message or rumour you checked, with your verdict, so the ministry sees
    rumours early. Call it after every check."""
    await module.user(ctx)
    async with module.db() as session:
        known = await session.scalars(select(Claim.key).distinct())
        session.add(
            Claim(
                claim=claim[:2000],
                key=claim_key(claim, known),
                verdict=verdict,
                source_url=source_url and source_url[:2000],
                source_date=source_date and source_date[:40],
            )
        )
        await session.commit()
    return "recorded"
