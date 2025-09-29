#!/usr/bin/env python3
"""
Database management CLI script
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.init_db import init_database, migrate_database, reset_database
from core.database import init_db, close_db


async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Database management CLI")
    parser.add_argument(
        "command",
        choices=["init", "migrate", "reset"],
        help="Database command to execute"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize database connections
        await init_db()
        
        if args.command == "init":
            await init_database()
        elif args.command == "migrate":
            await migrate_database()
        elif args.command == "reset":
            confirm = input("Are you sure you want to reset the database? This will delete ALL data! (yes/no): ")
            if confirm.lower() == "yes":
                await reset_database()
            else:
                print("Database reset cancelled")
        
    except Exception as e:
        print(f"Command failed: {e}")
        sys.exit(1)
    finally:
        # Close database connections
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())