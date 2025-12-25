from uuid import UUID

from sqlalchemy.orm import Session

from app.models.permission_group_permission import PermissionGroupPermission
from app.models.permission import Permission
from app.models.user import User


class AddPermissionsToGroupOperation:
    
    def __init__(
        self,
        db: Session,
        current_user: User,
        permission_group_id: UUID,
        permission_codes: list[str],
    ):
        self.db = db
        self.current_user = current_user
        self.permission_group_id = permission_group_id
        self.permission_codes = permission_codes

    def execute(self) -> None:
        self._validate()
        
        if self.permissions:
            self._add_permissions()
        else:
            self._remove_all_permissions()

    def _validate(self) -> None:
        self.permissions = (
            self.db.query(Permission)
            .filter(Permission.code.in_(self.permission_codes))
            .all()
        )
        if len(self.permissions) != len(self.permission_codes):
            raise ValueError(f"Permissions with codes not found")
        
        # TODO: Validate subscription plan permissions when it's available

    def _add_permissions(self) -> None:
        # clean all existing permissions for this group
        self.db.query(PermissionGroupPermission).filter(
            PermissionGroupPermission.permission_group_id == self.permission_group_id
        ).delete()

        # add new permissions
        permission_group_permissions = []
        for permission in self.permissions:
            permission_group_permission = PermissionGroupPermission(
                permission_group_id=self.permission_group_id,
                permission_id=permission.id)
            permission_group_permissions.append(permission_group_permission)
        self.db.add_all(permission_group_permissions)

        self.db.commit()

    def _remove_all_permissions(self) -> None:
        self.db.query(PermissionGroupPermission).filter(
            PermissionGroupPermission.permission_group_id == self.permission_group_id
        ).delete()

        self.db.commit()
