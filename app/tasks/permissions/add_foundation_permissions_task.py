import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.logging import logger
from app.libs.database import get_db_session
from app.models.permission import Permission


@celery_app.task(name="app.tasks.permissions.add_foundation_permissions_task")
def add_foundation_permissions_task():
    logger.info("Adding foundation permissions")
    try:
        with get_db_session() as db:
            foundation_permissions = load_foundation_permissions()
            created_count, skipped_count = add_foundation_permissions(db, foundation_permissions)
        logger.info(f"Foundation permissions task completed: {created_count} created, {skipped_count} skipped")
    except Exception as e:
        logger.error(f"Error adding foundation permissions: {str(e)}", exc_info=True)
        raise e


def load_foundation_permissions():
    # Get the path to the JSON file relative to the project root
    project_root = Path(__file__).parent.parent.parent.parent
    json_file_path = project_root / "app" / "tasks" / "permissions" / "__data__" / "foundation_permissions.json"
    
    logger.info(f"Loading foundation permissions from {json_file_path}")
    
    with open(json_file_path, "r") as f:
        foundation_permissions = json.load(f)
    
    return foundation_permissions

def add_foundation_permissions(db: Session, foundation_permissions: list[dict]) -> tuple[int, int]:
    created_count = 0
    skipped_count = 0
    
    for group in foundation_permissions:
        group_name = group.get("group", "unknown")
        logger.info(f"Processing permissions for group: {group_name}")
        
        for permission_data in group.get("permissions", []):
            code = permission_data.get("code")
            name = permission_data.get("name")
            description = permission_data.get("description")
            
            if not code:
                logger.warning(f"Skipping permission with missing code: {permission_data}")
                continue
            
            # Check if permission already exists
            existing_permission = db.query(Permission).filter(Permission.code == code).first()
            
            if existing_permission:
                logger.debug(f"Permission with code '{code}' already exists, skipping")
                skipped_count += 1
                continue
            
            # Create new permission
            permission = Permission(
                code=code,
                name=name,
                description=description,
                is_enabled=True
            )
            db.add(permission)
            created_count += 1
            logger.info(f"Created permission: {code} - {name}")
    
    logger.info(f"Foundation permissions processing completed: {created_count} created, {skipped_count} skipped")
    return created_count, skipped_count


if __name__ == "__main__":
    add_foundation_permissions_task()

