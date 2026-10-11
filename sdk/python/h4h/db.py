import os

from sqlalchemy.engine import make_url

LOCAL_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/hack4health"


def database_url() -> str:
    """DATABASE_URL for SQLAlchemy and asyncpg, or the local compose database.

    Takes the URL as Neon hands it out (postgresql://...?sslmode=require&channel_binding=require):
    asyncpg calls the TLS setting `ssl` and has no channel binding.
    """
    url = make_url(os.environ.get("DATABASE_URL", LOCAL_DATABASE_URL))
    query = dict(url.query)
    if "sslmode" in query:
        query["ssl"] = query.pop("sslmode")
    query.pop("channel_binding", None)
    return url.set(drivername="postgresql+asyncpg", query=query).render_as_string(hide_password=False)
