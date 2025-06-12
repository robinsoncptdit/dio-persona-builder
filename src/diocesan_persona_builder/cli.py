"""CLI interface for diocesan persona builder."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from .core.config import load_settings, Settings
from .core.csv_loader import CSVLoader
from .agents.persona_builder_agent import PersonaBuilderAgent


# Load environment variables
load_dotenv()

# Initialize Rich console for beautiful output
console = Console()

# Configure logging
def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.pass_context
def cli(ctx, log_level):
    """Diocesan Persona Builder - Generate data-driven personas using O*NET."""
    setup_logging(log_level)
    ctx.ensure_object(dict)
    
    try:
        ctx.obj['settings'] = load_settings()
    except Exception as e:
        console.print(f"[red]Error loading settings: {e}[/red]")
        console.print("[yellow]Make sure you have a .env file with O*NET credentials[/yellow]")
        sys.exit(1)


@cli.command()
@click.argument('csv_path', type=click.Path(exists=True, path_type=Path))
def validate(csv_path: Path):
    """Validate a CSV file structure."""
    console.print(f"[cyan]Validating CSV file:[/cyan] {csv_path}")
    
    try:
        settings = load_settings()
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
def load(csv_path: Path, limit: int):
    """Load and display roles from CSV."""
    console.print(f"[cyan]Loading roles from:[/cyan] {csv_path}")
    
    try:
        settings = load_settings()
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
def fetch(csv_path: Path, force: bool):
    """Fetch O*NET data for roles in CSV."""
    console.print(f"[cyan]Fetching O*NET data for roles in:[/cyan] {csv_path}")
    
    try:
        settings = load_settings()
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
def generate(csv_path: Path, output_dir: Path, force: bool):
    """Generate persona markdown files (complete pipeline)."""
    console.print("[bold cyan]Diocesan Persona Builder[/bold cyan]")
    console.print(f"[cyan]Input CSV:[/cyan] {csv_path}")
    console.print(f"[cyan]Output directory:[/cyan] {output_dir}")
    
    try:
        settings = load_settings()
        agent = PersonaBuilderAgent(settings)
        
        # Run full pipeline with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Load CSV
            task1 = progress.add_task("Loading CSV...", total=None)
            roles = agent.load_roles_from_csv(csv_path)
            progress.update(task1, completed=True)
            console.print(f"[green]✓ Loaded {len(roles)} roles[/green]")
            
            # Fetch O*NET data
            task2 = progress.add_task("Fetching O*NET data...", total=None)
            fetch_results = agent.fetch_onet_data(force_refresh=force)
            progress.update(task2, completed=True)
            console.print(f"[green]✓ Fetched data for {fetch_results['success']} occupation codes[/green]")
            
            # Generate personas
            task3 = progress.add_task("Generating personas...", total=None)
            gen_results = agent.generate_personas(output_dir)
            progress.update(task3, completed=True)
            console.print(f"[green]✓ Generated {gen_results['success']} personas[/green]")
        
        # Display summary
        summary = agent.get_task_summary()
        
        console.print("\n[bold]Pipeline Summary[/bold]")
        
        # Summary table
        table = Table()
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="white")
        
        for status, count in summary['status_breakdown'].items():
            style = "green" if status == "completed" else "red" if status == "failed" else "yellow"
            table.add_row(status.capitalize(), str(count), style=style)
        
        console.print(table)
        
        # Show output location
        output_path = output_dir or settings.output_config.output_dir
        console.print(f"\n[cyan]Output files saved to:[/cyan] {output_path}")
        
        # Show any errors
        if summary['failed_tasks']:
            console.print("\n[red]Failed tasks:[/red]")
            for task in summary['failed_tasks'][:5]:
                console.print(f"  • {task['role']}: {task['error']}")
        
        # Success message
        if gen_results['success'] > 0:
            console.print(f"\n[bold green]✓ Successfully generated {gen_results['success']} persona files![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error in pipeline: {e}[/red]")
        logging.exception("Pipeline error")
        sys.exit(1)


@cli.command()
def info():
    """Display configuration and system information."""
    console.print("[bold cyan]Diocesan Persona Builder - System Info[/bold cyan]\n")
    
    try:
        settings = load_settings()
        
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