import os
import sys
from alembic import command
from alembic.config import Config
from app.core.config import get_settings

def run_migrations():
    # Ensure we are in the project root
    if not os.path.exists("alembic.ini"):
        print("Error: alembic.ini not found. Please run this script from the project root.")
        sys.exit(1)

    # Create Alembic configuration object
    alembic_cfg = Config("alembic.ini")
    
    # Override the database URL in the config with the one from our settings
    # This ensures we use the same DB as the app, even if alembic.ini has a placeholder
    settings = get_settings()
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    print(f"Using Database URL: {settings.DATABASE_URL}")

    try:
        # Generate a new migration revision
        print("Detecting changes and generating migration...")
        # We use a generic message, or we could ask for input
        command.revision(alembic_cfg, autogenerate=True, message="Auto-generated migration")
        
        # Apply the migration
        print("Applying migrations...")
        command.upgrade(alembic_cfg, "head")
        
        print("Migrations applied successfully!")
        
    except Exception as e:
        print(f"An error occurred during migration: {e}")
        # If revision is empty (no changes), it might throw an error or just create an empty file.
        # In a real script we might want to catch "Target database is not up to date" etc.

if __name__ == "__main__":
    run_migrations()
