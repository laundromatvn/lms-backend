#!/bin/bash

# Database Migration Script
# Usage: ./scripts/migrate.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🗄️  LMS Backend Database Migration Tool${NC}"
echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Function to show help
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  upgrade [--dry-run]    Run database migrations (use --dry-run to check status)"
    echo "  create <message>       Create a new migration file"
    echo "  status                 Show current migration status"
    echo "  init                   Initialize Alembic for the first time"
    echo "  help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 upgrade                    # Run all pending migrations"
    echo "  $0 upgrade --dry-run          # Check migration status without applying"
    echo "  $0 create \"Add user table\"    # Create a new migration"
    echo "  $0 status                     # Show current migration status"
    echo "  $0 init                       # Initialize Alembic"
}

# Function to run Python CLI
run_cli() {
    if [ -f "venv/bin/activate" ]; then
        echo -e "${YELLOW}🐍 Activating virtual environment...${NC}"
        source venv/bin/activate
    fi
    
    python -m app.cmd.main migrate "$@"
}

# Main script logic
case "${1:-help}" in
    "upgrade")
        echo -e "${GREEN}🚀 Running database migrations...${NC}"
        if [ "$2" = "--dry-run" ]; then
            echo -e "${YELLOW}📋 Dry run mode - checking status only${NC}"
            run_cli upgrade --dry-run
        else
            run_cli upgrade
        fi
        ;;
    "create")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Error: Migration message is required${NC}"
            echo "Usage: $0 create \"Your migration message\""
            exit 1
        fi
        echo -e "${GREEN}📝 Creating new migration: $2${NC}"
        run_cli create "$2"
        ;;
    "status")
        echo -e "${BLUE}📊 Checking migration status...${NC}"
        run_cli status
        ;;
    "init")
        echo -e "${GREEN}🔧 Initializing Alembic...${NC}"
        run_cli init
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Migration command completed${NC}"
