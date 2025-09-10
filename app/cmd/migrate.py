#!/usr/bin/env python3
"""
Database migration CLI commands.
"""
import typer
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import migrate, create_migration, get_migration_status, downgrade
from app.core.logging import get_logger

logger = get_logger()
app = typer.Typer(help="Database migration commands")


@app.command()
def upgrade(
    dry_run: bool = typer.Option(False, "--dry-run", help="Check migration status without applying")
):
    """Run database migrations to upgrade to the latest version."""
    try:
        if dry_run:
            logger.info("Checking migration status (dry run)")
            success = migrate(auto_migrate=False)
        else:
            logger.info("Running database migrations")
            success = migrate(auto_migrate=True)
        
        if success:
            typer.echo("✅ Migrations completed successfully")
            sys.exit(0)
        else:
            typer.echo("❌ Migration failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Migration command failed", error=str(e))
        typer.echo(f"❌ Migration command failed: {e}")
        sys.exit(1)


@app.command()
def downgrade_cmd(
    revision: str = typer.Argument("base", help="Target revision to downgrade to (default: 'base' for complete rollback)")
):
    """Downgrade database migrations to a specific revision."""
    try:
        logger.info("Downgrading database migrations", target_revision=revision)
        success = downgrade(revision)
        
        if success:
            typer.echo(f"✅ Database downgraded successfully to: {revision}")
            sys.exit(0)
        else:
            typer.echo("❌ Failed to downgrade database")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Downgrade command failed", error=str(e))
        typer.echo(f"❌ Downgrade command failed: {e}")
        sys.exit(1)


@app.command()
def create(
    message: str = typer.Argument(..., help="Description of the migration")
):
    """Create a new migration file."""
    try:
        logger.info("Creating new migration", message=message)
        success = create_migration(message)
        
        if success:
            typer.echo(f"✅ Migration file created successfully: {message}")
            sys.exit(0)
        else:
            typer.echo("❌ Failed to create migration file")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Create migration command failed", error=str(e))
        typer.echo(f"❌ Create migration command failed: {e}")
        sys.exit(1)


@app.command()
def status():
    """Show current migration status."""
    try:
        logger.info("Getting migration status")
        status_info = get_migration_status()
        
        if status_info.get("status") == "success":
            typer.echo("📊 Migration Status:")
            typer.echo(f"Current: {status_info.get('current', 'Unknown')}")
            typer.echo(f"Heads: {status_info.get('heads', 'Unknown')}")
            typer.echo("\n📜 Migration History:")
            typer.echo(status_info.get('history', 'No history available'))
        else:
            typer.echo("❌ Failed to get migration status")
            if "error" in status_info:
                typer.echo(f"Error: {status_info['error']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Status command failed", error=str(e))
        typer.echo(f"❌ Status command failed: {e}")
        sys.exit(1)


@app.command()
def init():
    """Initialize Alembic for the first time."""
    try:
        import subprocess
        import os
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            
            # Check if alembic is already initialized
            if os.path.exists("alembic.ini"):
                typer.echo("⚠️  Alembic is already initialized")
                return
            
            # Initialize alembic
            logger.info("Initializing Alembic")
            result = subprocess.run(
                ["alembic", "init", "migrations"],
                capture_output=True,
                text=True,
                check=True
            )
            
            typer.echo("✅ Alembic initialized successfully")
            typer.echo("📝 Please update alembic.ini with your database configuration")
            
        finally:
            os.chdir(original_cwd)
            
    except subprocess.CalledProcessError as e:
        logger.error("Failed to initialize Alembic", error=e.stderr)
        typer.echo(f"❌ Failed to initialize Alembic: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        logger.error("Init command failed", error=str(e))
        typer.echo(f"❌ Init command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
