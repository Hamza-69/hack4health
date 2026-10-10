from importlib import import_module

# Package names under modules/. Listing a module here registers its tables
# (and later its MCP tools and admin routes).
MODULES: list[str] = []


def load_models() -> None:
    """Import every module's models so their tables attach to Base.metadata."""
    import core.models  # noqa: F401

    for name in MODULES:
        import_module(f"modules.{name}.models")
