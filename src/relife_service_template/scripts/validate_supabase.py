"""
Validates the integration of this service with a production Supabase instance by
starting a temporary instance of the API, connecting to the remote Supabase to
authenticate a user, and then verifying authentication via the /whoami endpoint.
"""

import argparse
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

import httpx
import uvicorn
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from supabase import create_client
from supabase.client import ClientOptions

# Configuration constants
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
SERVER_STARTUP_MAX_ATTEMPTS = 10
SERVER_STARTUP_RETRY_DELAY = 0.5
SERVER_HEALTH_CHECK_TIMEOUT = 5.0
SERVER_SHUTDOWN_TIMEOUT = 5.0
API_REQUEST_TIMEOUT = 30.0
ADMIN_ROLE_NAME = "relife_admin"


def load_environment() -> Dict[str, str]:
    """Load and validate required environment variables."""

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "KEYCLOAK_CLIENT_ID",
        "KEYCLOAK_CLIENT_SECRET",
    ]

    missing_vars = []
    config = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var] = value

    if missing_vars:
        console = Console()
        console.print(
            f"[red]ERROR: Missing environment variables: {', '.join(missing_vars)}[/red]"
        )
        console.print(
            "[blue]Please set these environment variables before running the script.[/blue]"
        )
        sys.exit(1)

    return config


def prompt_password(email: str) -> str:
    """Prompt user for password securely."""

    console = Console()
    console.print()
    console.print("[bold blue]Authentication Required[/bold blue]")
    console.print(f"Enter password for [bold cyan]{email}[/bold cyan]:")
    console.print()

    return Prompt.ask("Password", password=True, console=console)


def show_info_panel():
    """Display information about what this script does."""

    console = Console()
    info_md = """
**This script connects to production Supabase for verification:**

1. **Authenticate** with email/password via Supabase
2. **Start** temporary API server
3. **Verify** `/whoami` endpoint 
4. **Display** user information and roles
5. **Shutdown** server after verification
"""
    panel = Panel(
        Markdown(info_md),
        border_style="yellow",
        padding=(1, 2),
        title="Script to Check Supabase Integration",
    )
    console.print(panel)


async def authenticate_user(email: str, password: str, config: Dict[str, str]) -> str:
    """Authenticate with Supabase and return access token."""

    console = Console()
    console.print(f"[blue]Authenticating user: {email}[/blue]")

    try:
        client = create_client(
            config["SUPABASE_URL"],
            config["SUPABASE_KEY"],
            options=ClientOptions(),
        )

        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response.user and response.session:
            console.print("[green]Authentication successful[/green]")
            return response.session.access_token
        else:
            console.print("[red]Authentication failed - no session returned[/red]")
            console.print(
                "[yellow]User may only exist in Keycloak - sign in via web interface first[/yellow]"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Authentication failed: {e}[/red]")
        sys.exit(1)


@asynccontextmanager
async def run_api_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Start and manage temporary API server."""

    from relife_service_template.app import app

    console = Console()

    # Configure server
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )

    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    try:
        # Wait for server to start
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Starting server...", total=None)

            for attempt in range(SERVER_STARTUP_MAX_ATTEMPTS):
                await asyncio.sleep(SERVER_STARTUP_RETRY_DELAY)
                try:
                    async with httpx.AsyncClient(
                        timeout=SERVER_HEALTH_CHECK_TIMEOUT
                    ) as client:
                        response = await client.get(f"http://{host}:{port}/docs")
                        if response.status_code in [200, 404]:
                            progress.update(task, description="Server ready")
                            break
                except Exception:
                    if attempt == SERVER_STARTUP_MAX_ATTEMPTS - 1:
                        progress.update(task, description="Server failed")
                        console.print("[red]Server failed to start[/red]")
                        raise

        console.print(f"[green]Server running on http://{host}:{port}[/green]")
        yield f"http://{host}:{port}"

    finally:
        # Shutdown server
        server.should_exit = True
        try:
            await asyncio.wait_for(server_task, timeout=SERVER_SHUTDOWN_TIMEOUT)
        except asyncio.TimeoutError:
            console.print("[yellow]Server shutdown timed out[/yellow]")


async def verify_whoami_endpoint(base_url: str, auth_token: str):
    """Verify the /whoami endpoint and display results."""

    console = Console()
    console.print(f"[blue]Verifying {base_url}/whoami[/blue]")

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=API_REQUEST_TIMEOUT) as client:
            response = await client.get(f"{base_url}/whoami", headers=headers)
            console.print(f"[blue]Response: {response.status_code}[/blue]")

            if response.status_code == 200:
                data = response.json()
                console.print("[green]Authentication verified[/green]")
                display_user_info(data)
            else:
                console.print(f"[red]Request failed: {response.status_code}[/red]")
                console.print(f"[yellow]{response.text}[/yellow]")

    except httpx.TimeoutException:
        console.print("[red]Request timed out[/red]")
    except Exception as e:
        console.print(f"[red]Request failed: {e}[/red]")


def display_user_info(data: Dict[str, Any]):
    """Display user information in a table."""

    console = Console()
    table = Table(title="User Information", show_header=True, header_style="bold blue")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Basic user info
    user_info = data.get("user", {}).get("user", {})
    table.add_row("User ID", user_info.get("id", "N/A"))
    table.add_row("Email", user_info.get("email", "N/A"))
    table.add_row("Created", user_info.get("created_at", "N/A"))

    # Keycloak roles
    roles = data.get("keycloak_roles", [])
    if roles:
        roles_text = f"{len(roles)} roles:"
        for role in roles:
            roles_text += f"\n• {role.get('name', 'Unknown')}"
            if role.get("description"):
                roles_text += f": {role['description']}"
    else:
        roles_text = "None"
    table.add_row("Keycloak Roles", roles_text)

    # Admin status
    has_admin = any(role.get("name") == ADMIN_ROLE_NAME for role in roles)
    admin_text = Text("Yes" if has_admin else "No")
    admin_text.stylize("green" if has_admin else "red")
    table.add_row("Admin Role", admin_text)

    console.print(table)


async def main():
    """Main script function."""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Validate integration with production Supabase instance"
    )
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    args = parser.parse_args()

    console = Console()

    # Show info panel
    show_info_panel()

    # Load environment
    config = load_environment()
    console.print(
        f"[green]Environment loaded - connecting to {config['SUPABASE_URL']}[/green]"
    )

    # Get password
    password = prompt_password(args.email)

    # Authenticate
    auth_token = await authenticate_user(args.email, password, config)

    # Verify API
    console.print(f"[blue]Starting server on {args.host}:{args.port}[/blue]")

    try:
        async with run_api_server(args.host, args.port) as server_url:
            await verify_whoami_endpoint(server_url, auth_token)
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")

    console.print("[blue]Verification complete[/blue]")


def cli():
    """CLI entry point."""

    asyncio.run(main())


if __name__ == "__main__":
    cli()
