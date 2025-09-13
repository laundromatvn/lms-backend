"""
Main CLI entry point for the application.
"""
import typer
from app.cmd.migrate import app as migrate_app

app = typer.Typer(help="LMS Backend CLI")
app.add_typer(migrate_app, name="migrate", help="Database migration commands")

if __name__ == "__main__":
    app()
