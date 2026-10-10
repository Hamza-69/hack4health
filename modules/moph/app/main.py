from app import api, tools  # noqa: F401  (importing registers the routes and tools)
from app.module import module

app = module.app()
