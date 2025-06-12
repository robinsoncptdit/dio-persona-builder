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

from .core.config import load_settings, Settings
from .core.csv_loader import CSVLoader
from .agents.persona_builder_agent import PersonaBuilderAgent
from .core.exceptions import (
    PersonaBuilderError,
    ONetConnectionError,
    ONetAPIError,
    OpenAIConnectionError,
    OpenAIAPIError,
    TemplateError,
    PersonaFileError
)


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
    # Always 3 phases: fetch/load, render, convert
    total_phases = 3 if mode == "reprocess" else 2  # update mode skips fetch
    
    unprocessed_roles = []
    openai_client = None
    
    # Initialize OpenAI client if API key is available
    if settings.openai_api_key:
        try:
            openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize OpenAI client: {e}[/yellow]")
            console.print("[yellow]User persona conversion will be skipped.[/yellow]")

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console
    ) as progress:
        overall = progress.add_task("Overall Progress", total=total_roles * total_phases)
        
        # PHASE 1: Fetch O*NET data (reprocess mode only)
        if mode == "reprocess":
            for task in agent.tasks:
                role = task.role
                if not task.onet_data or force:
                    try:
                        data = agent.api_client.fetch_complete_occupation_data(role.onet_code)
                        agent._onet_cache[role.onet_code] = data
                        task.onet_data = data
                        task.status = "fetched"
                    except ONetConnectionError as e:
                        task.status = "fetch_failed"
                        task.error = f"Connection error: {e.message}"
                        logger.error(f"Connection failed for {role.onet_code}: {e}")
                    except ONetAPIError as e:
                        task.status = "fetch_failed"
                        task.error = f"API error: {e.message} (Status: {e.status_code})"
                        logger.error(f"API error for {role.onet_code}: {e}")
                    except Exception as e:
                        task.status = "fetch_failed"
                        task.error = f"Unexpected error: {e}"
                        logger.error(f"Unexpected error fetching {role.onet_code}: {e}")
                else:
                    task.status = "fetched"
                progress.update(overall, description=f"[cyan]Fetching O*NET data for {role.role_title}[/cyan]", advance=1)
        
        # PHASE 2: Render occupational personas
        for task in agent.tasks:
            role = task.role
            
            if mode == "reprocess":
                # Generate new occupational persona
                if task.status == "fetched" and task.onet_data:
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
                        task.status = "rendered"
                    except TemplateError as e:
                        task.status = "render_failed"
                        task.error = f"Template error: {e.message}"
                        logger.error(f"Template error for {role.role_title}: {e}")
                    except (OSError, IOError) as e:
                        task.status = "render_failed"
                        task.error = f"File system error: {e}"
                        logger.error(f"File write error for {role.role_title}: {e}")
                    except Exception as e:
                        task.status = "render_failed"
                        task.error = f"Unexpected error: {e}"
                        logger.error(f"Unexpected render error for {role.role_title}: {e}")
                elif task.status == "fetch_failed":
                    # Skip rendering if fetch failed
                    pass
            else:
                # Update mode: load existing occupational persona
                occ_fn = settings.output_config.file_pattern.format(role_slug=role.role_slug)
                occ_path = occupational_dir / occ_fn
                
                if occ_path.exists():
                    task.output_path = occ_path
                    task.status = "rendered"
                else:
                    task.status = "render_failed"
                    task.error = "Occupational persona file not found"
                    unprocessed_roles.append(role.role_slug)
            
            progress.update(overall, description=f"[green]Rendering occupational persona for {role.role_title}[/green]", advance=1)
        
        # PHASE 3: Convert to user personas
        if openai_client:
            prompt_file = Path(__file__).parent / "prompts" / "conversion-prompt.md"
            try:
                prompt_content = prompt_file.read_text(encoding="utf-8")
                system_part, user_part = prompt_content.split("⇢ **INPUT**", 1)
            except Exception as e:
                console.print(f"[red]Error reading conversion prompt: {e}[/red]")
                prompt_content = None
            
            for task in agent.tasks:
                role = task.role
                
                if task.status == "rendered" and task.output_path and prompt_content:
                    try:
                        # Read occupational persona content
                        occ_content = task.output_path.read_text(encoding='utf-8')
                        
                        # Prepare OpenAI messages
                        wrapped_input = "⇢ **INPUT**\n" + occ_content + "\n**END INPUT**"
                        messages = [
                            {"role": "system", "content": system_part.strip()},
                            {"role": "user", "content": user_part.replace("{{RAW_PERSONA_MD}}", wrapped_input)}
                        ]
                        
                        # Call OpenAI
                        response = openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                            max_tokens=1500
                        )
                        
                        # Write user persona
                        user_content = response.choices[0].message.content
                        user_filename = f"user_persona_{role.role_slug}.md"
                        user_path = user_dir / user_filename
                        user_path.write_text(user_content, encoding='utf-8')
                        
                        task.status = "completed"
                        
                    except openai.AuthenticationError as e:
                        task.status = "conversion_failed"
                        task.error = f"OpenAI authentication failed: Check API key in .env file"
                        logger.error(f"OpenAI auth error for {role.role_title}: {e}")
                    except openai.RateLimitError as e:
                        task.status = "conversion_failed"
                        task.error = f"OpenAI rate limit exceeded: {e}"
                        logger.error(f"OpenAI rate limit for {role.role_title}: {e}")
                    except openai.APIError as e:
                        task.status = "conversion_failed"
                        task.error = f"OpenAI API error: {e}"
                        logger.error(f"OpenAI API error for {role.role_title}: {e}")
                    except (OSError, IOError) as e:
                        task.status = "conversion_failed"
                        task.error = f"File system error writing user persona: {e}"
                        logger.error(f"File write error for user persona {role.role_title}: {e}")
                    except Exception as e:
                        task.status = "conversion_failed"
                        task.error = f"Unexpected conversion error: {e}"
                        logger.error(f"Unexpected conversion error for {role.role_title}: {e}")
                else:
                    # Skip conversion if rendering failed or no OpenAI
                    if task.status == "rendered":
                        task.status = "conversion_skipped"
                        task.error = "OpenAI conversion unavailable"
                
                progress.update(overall, description=f"[blue]Converting to user persona for {role.role_title}[/blue]", advance=1)
        else:
            # Skip conversion phase entirely
            for task in agent.tasks:
                if task.status == "rendered":
                    task.status = "conversion_skipped"
                    task.error = "OpenAI API key not provided"
                progress.update(overall, advance=1)

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