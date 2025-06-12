"""CLI interface for diocesan persona builder."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from difflib import get_close_matches

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from dotenv import load_dotenv
import openai
from openai import ChatCompletion

from .core.config import load_settings, Settings
from .core.csv_loader import CSVLoader
from .agents.persona_builder_agent import PersonaBuilderAgent


# Load environment variables
load_dotenv()

# Initialize Rich console for beautiful output
console = Console()

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None):
    """Setup logging configuration with optional file handler."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    else:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        handlers.append(logging.FileHandler(log_dir / f"run_{timestamp}.log"))
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--log-file', type=click.Path(path_type=Path), default=None, help='Path to log file')
@click.pass_context
def cli(ctx, log_level, log_file):
    """Diocesan Persona Builder - Generate data-driven personas using O*NET."""
    setup_logging(log_level, log_file)
    ctx.ensure_object(dict)
    
    try:
        settings = load_settings(log_level=log_level, log_file=log_file)
        ctx.obj['settings'] = settings
    except Exception as e:
        console.print(f"[red]Error loading settings: {e}[/red]")
        console.print("[yellow]Make sure you have a .env file with O*NET credentials[/yellow]")
        sys.exit(1)


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def validate(ctx, csv_path: Path):
    """Validate a CSV file structure."""
    console.print(f"[cyan]Validating CSV file:[/cyan] {csv_path}")
    
    try:
        settings = ctx.obj['settings']
        csv_config = settings.get_csv_config(csv_path)
        loader = CSVLoader(csv_config)
        
        # Validate structure
        validation = loader.validate_csv_structure()
        
        if validation['valid']:
            console.print("[green]✓ CSV structure is valid![/green]")
            
            # Display column information
            table = Table(title="CSV Structure")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Total Rows", str(validation['row_count']))
            table.add_row("Columns Found", ", ".join(validation['columns']))
            
            if validation['missing_columns']:
                table.add_row(
                    "Missing Columns",
                    ", ".join(validation['missing_columns']),
                    style="red"
                )
            
            if validation['extra_columns']:
                table.add_row(
                    "Extra Columns",
                    ", ".join(validation['extra_columns']),
                    style="yellow"
                )
            
            console.print(table)
            
            # Load and display sample roles
            roles = loader.load_roles()
            console.print(f"\n[green]Successfully loaded {len(roles)} roles[/green]")
            
            # Show unique O*NET codes
            unique_codes = loader.get_unique_onet_codes(roles)
            console.print(f"[cyan]Unique O*NET codes:[/cyan] {len(unique_codes)}")
            
        else:
            console.print(f"[red]✗ CSV validation failed: {validation['error']}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error validating CSV: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True, path_type=Path))
@click.option('--limit', default=5, help='Number of roles to display')
@click.pass_context
def load(ctx, csv_path: Path, limit: int):
    """Load and display roles from CSV."""
    console.print(f"[cyan]Loading roles from:[/cyan] {csv_path}")
    
    try:
        settings = ctx.obj['settings']
        agent = PersonaBuilderAgent(settings)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading CSV...", total=None)
            roles = agent.load_roles_from_csv(csv_path)
            progress.update(task, completed=True)
        
        console.print(f"[green]Loaded {len(roles)} roles[/green]")
        
        # Display sample roles in a table
        table = Table(title=f"First {min(limit, len(roles))} Roles")
        table.add_column("Role Title", style="cyan")
        table.add_column("Setting", style="magenta")
        table.add_column("O*NET Code", style="yellow")
        table.add_column("O*NET Title", style="white")
        
        for role in roles[:limit]:
            table.add_row(
                role.role_title,
                role.setting,
                role.onet_code,
                role.onet_title
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error loading CSV: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True, path_type=Path))
@click.option('--force', is_flag=True, help='Force refresh of cached data')
@click.pass_context
def fetch(ctx, csv_path: Path, force: bool):
    """Fetch O*NET data for roles in CSV."""
    console.print(f"[cyan]Fetching O*NET data for roles in:[/cyan] {csv_path}")
    
    try:
        settings = ctx.obj['settings']
        agent = PersonaBuilderAgent(settings)
        
        # Load roles
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading CSV...", total=None)
            roles = agent.load_roles_from_csv(csv_path)
            progress.update(task, completed=True)
        
        console.print(f"[green]Loaded {len(roles)} roles[/green]")
        
        # Fetch O*NET data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching O*NET data...", total=None)
            results = agent.fetch_onet_data(force_refresh=force)
            progress.update(task, completed=True)
        
        # Display results
        table = Table(title="O*NET Data Fetch Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="white")
        
        table.add_row("Total Codes", str(results['total']))
        table.add_row("Successfully Fetched", str(results['success']), style="green")
        table.add_row("Cached", str(results['cached']), style="yellow")
        table.add_row("Failed", str(results['failed']), style="red")
        
        console.print(table)
        
        if results['errors']:
            console.print("\n[red]Errors encountered:[/red]")
            for error in results['errors'][:5]:  # Show first 5 errors
                console.print(f"  • {error['code']}: {error['error']}")
                
    except Exception as e:
        console.print(f"[red]Error fetching O*NET data: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-dir', type=click.Path(path_type=Path), default='output', help='Output directory (default: output)')
@click.option('--force', is_flag=True, help='Force refresh of cached data')
@click.option('--role', type=str, default=None, help='Only generate/update this one role (slug or exact title)')
@click.pass_context
def generate(ctx, csv_path: Path, output_dir: Path, force: bool, role: Optional[str]):
    """Generate persona markdown files (complete pipeline) with per-role progress."""
    settings = ctx.obj['settings']
    agent = PersonaBuilderAgent(settings)
    roles = agent.load_roles_from_csv(csv_path)

    # If a single role is specified, filter tasks to only that persona
    if role:
        slugs = [t.role.role_slug for t in agent.tasks]
        titles = [t.role.role_title for t in agent.tasks]
        match = next((t for t in agent.tasks if t.role.role_slug == role or t.role.role_title == role), None)
        if match:
            agent.tasks = [match]
        else:
            candidates = slugs + titles
            suggestions = get_close_matches(role, candidates, n=3, cutoff=0.6)
            if suggestions:
                console.print(f"[red]Role '{role}' not found. Did you mean: {', '.join(suggestions)}?[/red]")
            else:
                console.print(f"[red]Role '{role}' not found. Available roles: {', '.join(slugs)}[/red]")
            sys.exit(1)

    console.print("[bold cyan]Generating Personas[/bold cyan]\n")
    base_output = output_dir or settings.output_config.output_dir
    # Ensure occupational and user subdirectories
    occupational_dir = base_output / "occupational"
    user_dir = base_output / "user"
    occupational_dir.mkdir(parents=True, exist_ok=True)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Prompt user if existing persona files are present
    existing_occ = []
    existing_user = []
    for t in agent.tasks:
        occ_fn = settings.output_config.file_pattern.format(role_slug=t.role.role_slug)
        occ_path_check = occupational_dir / occ_fn
        if occ_path_check.exists():
            existing_occ.append(occ_path_check)
        user_fn = f"user_persona_{t.role.role_slug}.md"
        user_path_check = user_dir / user_fn
        if user_path_check.exists():
            existing_user.append(user_path_check)
    if existing_occ or existing_user:
        choice = click.prompt(
            "Existing persona files found. Choose Reprocess via O*NET, Update via OpenAI, or Abort",
            type=click.Choice(["Reprocess via O*NET", "Update via OpenAI", "Abort"], case_sensitive=False)
        )
        if choice.lower() == "abort":
            console.print("[yellow]Operation aborted by user.[/yellow]")
            sys.exit(0)
        # Map choice to internal mode
        c = choice.lower()
        if c.startswith("reprocess"):
            mode = "reprocess"
        elif c.startswith("update"):
            mode = "update"
        else:
            mode = "reprocess"
    else:
        mode = "reprocess"

    total_roles = len(agent.tasks)
    step_count = 2 if mode == "reprocess" else 1

    unprocessed_roles = []  # List to keep track of roles that couldn't be processed

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console
    ) as progress:
        overall = progress.add_task("Overall Progress", total=total_roles)
        for task in agent.tasks:
            role = task.role
            role_task = progress.add_task(f"[magenta]{role.role_title}", total=step_count)
            if mode == "reprocess":
                # Fetch step
                if not task.onet_data or force:
                    try:
                        data = agent.api_client.fetch_complete_occupation_data(role.onet_code)
                        agent._onet_cache[role.onet_code] = data
                        task.onet_data = data
                        task.status = "fetched"
                    except Exception as e:
                        task.status = "failed"
                        task.error = str(e)
                progress.update(role_task, description=f"[cyan]Fetching[/cyan] {role.role_title}", advance=1)
                # Render step
                if task.onet_data and task.status != "failed":
                    try:
                        content = agent.template_engine.render_persona(
                            role=role,
                            onet_data=task.onet_data,
                            openai_api_key=settings.openai_api_key
                        )
                        filename = settings.output_config.file_pattern.format(role_slug=role.role_slug)
                        occ_path = occupational_dir / filename
                        occ_path.write_text(content, encoding='utf-8')
                        task.output_path = occ_path
                    except Exception as e:
                        task.status = "failed"
                        task.error = str(e)
            else:
                # Update: reuse existing occupational persona
                occ_fn = settings.output_config.file_pattern.format(role_slug=role.role_slug)
                occ_path = occupational_dir / occ_fn

                # Check if the file exists, if not, log and skip
                if not occ_path.exists():
                    console.print(f"[yellow]Skipping {role.role_slug} as the file does not exist.[/yellow]")
                    unprocessed_roles.append(role.role_slug)
                    continue

                content = occ_path.read_text(encoding='utf-8')
                task.output_path = occ_path
            # Conversion step
            try:
                prompt_file = Path(__file__).parent / "prompts" / "conversion-prompt.md"
                prompt_content = prompt_file.read_text(encoding="utf-8")
                system_part, user_part = prompt_content.split("⇢ **INPUT**", 1)
                wrapped_input = "⇢ **INPUT**\n" + content + "\n**END INPUT**"
                messages = [
                    {"role": "system", "content": system_part.strip()},
                    {"role": "user", "content": user_part.replace("{{RAW_PERSONA_MD}}", wrapped_input)}
                ]
                openai.api_key = settings.openai_api_key
                response = ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=1500
                )
                content = response['choices'][0]['message']['content']
                filename = settings.output_config.file_pattern.format(role_slug=role.role_slug)
                occ_path = occupational_dir / filename
                occ_path.write_text(content, encoding='utf-8')
                task.status = "completed"
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
            progress.update(role_task, description=f"[green]Rendering[/green] {role.role_title}", advance=1)
            progress.update(overall, advance=1)
            progress.remove_task(role_task)

    # Summary
    summary = agent.get_task_summary()
    console.print("\n[bold]Pipeline Summary[/bold]")
    table = Table()
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="white")
    for status, count in summary['status_breakdown'].items():
        style = "green" if status == "completed" else "red" if status == "failed" else "yellow"
        table.add_row(status.capitalize(), str(count), style=style)
    console.print(table)
    console.print(f"\n[cyan]Output files saved to:[/cyan] {base_output}")
    if summary['failed_tasks']:
        console.print("\n[red]Failed tasks:[/red]")
        for ft in summary['failed_tasks'][:5]:
            console.print(f"  • {ft['role']}: {ft['error']}")
    if summary['status_breakdown'].get('completed', 0) > 0:
        console.print(f"\n[bold green]✓ Successfully generated {summary['status_breakdown'].get('completed')} persona files![/bold green]")

    # Log unprocessed roles
    if unprocessed_roles:
        with open('logs/unprocessed_roles.log', 'w') as log_file:
            log_file.write("Unprocessed Roles:\n")
            for role in unprocessed_roles:
                log_file.write(f"{role}\n")
        console.print("[red]Some roles were not processed. Check logs/unprocessed_roles.log for details.[/red]")


@cli.command()
@click.pass_context
def info(ctx):
    """Display configuration and system information."""
    console.print("[bold cyan]Diocesan Persona Builder - System Info[/bold cyan]\n")
    
    try:
        settings = ctx.obj['settings']
        
        # Configuration table
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("O*NET Username", settings.onet_username)
        table.add_row("O*NET API URL", settings.api_config.base_url)
        table.add_row("Output Directory", str(settings.output_config.output_dir))
        table.add_row("Template Directory", str(settings.output_config.template_dir))
        table.add_row("Log Level", settings.log_level)
        
        console.print(table)
        
        # Check directories
        console.print("\n[cyan]Directory Status:[/cyan]")
        
        dirs = {
            "Output": settings.output_config.output_dir,
            "Templates": settings.output_config.template_dir,
            "Data": Path("diocesan_persona_builder/data")
        }
        
        for name, path in dirs.items():
            status = "[green]✓ Exists[/green]" if path.exists() else "[red]✗ Missing[/red]"
            console.print(f"  {name}: {path} {status}")
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        console.print("[yellow]Check your .env file[/yellow]")


if __name__ == "__main__":
    cli()