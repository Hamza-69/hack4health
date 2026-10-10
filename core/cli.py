"""`uv run h4h ...`: setup, admins, modules, tool calls, and running everything in dev."""

import argparse
import asyncio
import getpass
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import select

from core import tokens
from core.registry import config_path, load_modules

MODULES_DIR = Path("modules")
TEMPLATE = "noop"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")
CORE_PORT = 8000
SHELL_PORT = 5173


def main() -> None:
    parser = argparse.ArgumentParser(prog="h4h")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="create the token signing keys")

    admin = commands.add_parser("admin", help="admin panel logins").add_subparsers(dest="sub", required=True)
    create = admin.add_parser("create", help="create an admin, or update it if the email exists")
    create.add_argument("email")
    create.add_argument("--role", choices=["operator", "supplier"], default="operator")
    create.add_argument("--module", action="append", default=[], help="module a supplier can open (repeatable)")
    create.add_argument("--password", help="prompted for when left out")

    module = commands.add_parser("module", help="modules").add_subparsers(dest="sub", required=True)
    new = module.add_parser("new", help=f"create a module from the {TEMPLATE} template and register it")
    new.add_argument("name", help="lowercase letters, digits and _ (used for the schema and tool names)")
    new.add_argument("--title", help="name shown in the admin panel")
    module.add_parser("token", help="write a fresh MODULE_TOKEN to modules/<name>/.env").add_argument("name")
    module.add_parser("list", help="show the registry")

    tools = commands.add_parser("tools", help="call module tools the way the agent does").add_subparsers(dest="sub", required=True)
    tools.add_parser("list", help="every registered module's tools")
    call = tools.add_parser("call", help="call a tool as a user")
    call.add_argument("name", help="<module>__<tool>")
    call.add_argument("--user", required=True, help="wa:<phone>, tg:<id>, web:<uuid>, or a user uuid")
    call.add_argument("--args", default="{}", help="tool arguments as JSON")

    commands.add_parser("dev", help="run the core, the admin panel and every local module")

    args = parser.parse_args()
    match args.command, getattr(args, "sub", None):
        case "init", _:
            init()
        case "admin", "create":
            asyncio.run(create_admin(args.email, args.role, args.module, args.password))
        case "module", "new":
            new_module(args.name, args.title)
        case "module", "token":
            write_module_token(args.name)
        case "module", "list":
            for m in load_modules().values():
                print(f"{m.name:<16} {m.url:<28} ui {m.ui_url}")
        case "tools", "list":
            asyncio.run(list_tools())
        case "tools", "call":
            asyncio.run(call_tool(args.name, args.user, json.loads(args.args)))
        case "dev", _:
            dev()


def init() -> None:
    if tokens.generate_keys():
        print(f"Wrote signing keys to {tokens.keys_dir()}/ (keep private.pem secret).")
    else:
        print(f"Signing keys already exist in {tokens.keys_dir()}/.")
    for name in load_modules():
        if (MODULES_DIR / name).is_dir() and not (MODULES_DIR / name / ".env").exists():
            write_module_token(name)


async def create_admin(email: str, role: str, modules: list[str], password: str | None) -> None:
    from core.db import Session
    from core.models import Admin, AdminRole
    from core.passwords import hash_password

    password = password or getpass.getpass("Password: ")
    async with Session() as session:
        admin = await session.scalar(select(Admin).where(Admin.email == email.lower()))
        verb = "Updated" if admin else "Created"
        admin = admin or Admin(email=email.lower())
        admin.password_hash = hash_password(password)
        admin.role = AdminRole(role)
        admin.modules = modules
        session.add(admin)
        await session.commit()
    print(f"{verb} {role} {email}" + (f" for {', '.join(modules)}" if modules else ""))


def new_module(name: str, title: str | None) -> None:
    if not NAME_RE.match(name):
        sys.exit("name must be lowercase letters, digits and _, starting with a letter")
    registry = load_modules()
    target = MODULES_DIR / name
    if name in registry or target.exists():
        sys.exit(f"module {name!r} already exists")
    title = title or name.replace("_", " ").title()

    shutil.copytree(
        MODULES_DIR / TEMPLATE,
        target,
        ignore=shutil.ignore_patterns(
            ".venv", "node_modules", "dist", ".env", "__pycache__", "uv.lock", ".pytest_cache"
        ),
    )
    for path in target.rglob("*"):
        if path.is_file():
            text = path.read_text()
            path.write_text(text.replace(TEMPLATE, name).replace(TEMPLATE.title(), title))

    ports = [urlsplit(m.url).port or 0 for m in registry.values()]
    ui_ports = [urlsplit(m.ui_url).port or 0 for m in registry.values()]
    port, ui_port = max([CORE_PORT, *ports]) + 1, max([SHELL_PORT, *ui_ports]) + 1
    with config_path().open("a") as f:
        f.write(
            f'\n[{name}]\ntitle = "{title}"\n'
            f'url = "http://localhost:{port}"\nui_url = "http://localhost:{ui_port}"\n'
        )
    write_module_token(name)

    print(f"Created {target}/ and registered it in {config_path()} (backend :{port}, UI :{ui_port}).")
    if shutil.which("npm"):
        subprocess.run(["npm", "install", "--silent"], check=False)
    else:
        print("Run `npm install` at the repo root to link the new UI.")
    print("Restart `uv run h4h dev` to start it. Give a supplier access with:")
    print(f"  uv run h4h admin create <email> --role supplier --module {name}")


def write_module_token(name: str) -> None:
    if name not in load_modules():
        sys.exit(f"module {name!r} is not in {config_path()}")
    env = MODULES_DIR / name / ".env"
    lines = env.read_text().splitlines() if env.exists() else []
    lines = [line for line in lines if not line.startswith("MODULE_TOKEN=")]
    lines.append(f"MODULE_TOKEN={tokens.module_token(name)}")
    env.write_text("\n".join(lines) + "\n")
    env.chmod(0o600)
    print(f"Wrote MODULE_TOKEN to {env}")


async def list_tools() -> None:
    from core.tools import list_tools

    for tool in await list_tools():
        print(f"{tool.name}\n    {tool.description or ''}\n    args: {json.dumps(tool.input_schema.get('properties', {}))}")


async def call_tool(name: str, user: str, arguments: dict) -> None:
    from core.identity import user_id_for
    from core.tools import call_tool

    app, _, account = user.partition(":")
    user_id = user_id_for(app, account) if account else uuid.UUID(user)
    result = await call_tool(user_id, name, arguments)
    print(f"user {user_id}" + ("  (tool error)" if result.is_error else ""))
    if result.structured_content is not None:
        print(json.dumps(result.structured_content, indent=2))
    else:
        for block in result.content:
            print(getattr(block, "text", block))


def dev() -> None:
    """Run the core, the admin shell, and each local module's backend and UI, with merged output."""
    core_url = f"http://localhost:{CORE_PORT}"
    shell_origin = f"http://localhost:{SHELL_PORT}"
    processes = [
        ("core", ["uv", "run", "uvicorn", "core.app:app", "--reload", "--port", str(CORE_PORT)], {}),
        ("admin", ["npm", "run", "dev", "-w", "admin", "--", "--port", str(SHELL_PORT), "--strictPort"], {"CORE_URL": core_url}),
    ]
    for m in load_modules().values():
        folder, url, ui = MODULES_DIR / m.name, urlsplit(m.url), urlsplit(m.ui_url)
        if not folder.is_dir() or url.hostname not in ("localhost", "127.0.0.1"):
            continue  # hosted elsewhere
        processes.append((m.name, ["uv", "run", "--directory", str(folder), "uvicorn", "app.main:app", "--reload", "--port", str(url.port)], {"CORE_URL": core_url}))
        if (folder / "ui").is_dir() and ui.port != url.port:
            processes.append((f"{m.name}-ui", ["npm", "run", "dev", "-w", f"{folder}/ui", "--", "--port", str(ui.port), "--strictPort"], {"MODULE_URL": m.url, "VITE_SHELL_ORIGIN": shell_origin}))
    try:
        asyncio.run(_run_all(processes))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


async def _run_all(processes: list[tuple[str, list[str], dict]]) -> None:
    width = max(len(name) for name, _, _ in processes)
    started = []
    # Stop the children on SIGTERM too, not only Ctrl-C; they run in their own process groups.
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, asyncio.current_task().cancel)

    async def pump(name: str, proc: asyncio.subprocess.Process) -> None:
        async for line in proc.stdout:
            print(f"{name:>{width}} | {line.decode(errors='replace').rstrip()}", flush=True)
        await proc.wait()
        print(f"{name:>{width}} | exited with {proc.returncode}", flush=True)

    try:
        for name, cmd, env in processes:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                # Each module has its own venv; the core's must not leak into it.
                env={k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
            started.append(proc)
            asyncio.create_task(pump(name, proc))
        await asyncio.gather(*(p.wait() for p in started))
    finally:
        for proc in started:
            if proc.returncode is None:
                os.killpg(proc.pid, signal.SIGTERM)
        await asyncio.gather(*(p.wait() for p in started), return_exceptions=True)
