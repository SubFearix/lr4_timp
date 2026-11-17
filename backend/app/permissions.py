from fastapi import Depends, HTTPException, status
from . import auth, models

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_USER = "user"

ALL_ROLES = (ROLE_ADMIN, ROLE_OPERATOR, ROLE_USER)
STAFF_MANAGEMENT_ROLES = (ROLE_ADMIN,)
REFERENCE_DATA_WRITE_ROLES = (ROLE_ADMIN,)
OPERATIONAL_WRITE_ROLES = (ROLE_ADMIN, ROLE_OPERATOR)
DELETE_ROLES = (ROLE_ADMIN,)

def require_roles(*roles: str):
    def dependency(current_user: models.Staff = Depends(auth.get_current_user)) -> models.Staff:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостаточно прав для выполнения этого действия",
            )
        return current_user
    return dependency
require_admin = require_roles(ROLE_ADMIN)
require_operational_write = require_roles(*OPERATIONAL_WRITE_ROLES)
