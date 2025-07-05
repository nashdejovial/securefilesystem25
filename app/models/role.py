"""
Role definitions for user authorization.
"""

from enum import Enum

class RoleEnum(str, Enum):
    """User role definitions with associated permissions."""
    
    ADMIN = "admin"     # Full system access
    MANAGER = "manager" # Can manage users and content
    USER = "user"       # Basic user access
    GUEST = "guest"     # Limited read-only access

    def __str__(self):
        return self.value

    @property
    def permissions(self):
        """Get permissions associated with each role."""
        return ROLE_PERMISSIONS.get(self, set())

# Define permissions for each role
ROLE_PERMISSIONS = {
    RoleEnum.ADMIN: {
        'manage_users',
        'manage_roles',
        'manage_files',
        'upload_files',
        'download_files',
        'share_files',
        'delete_files',
        'view_analytics'
    },
    RoleEnum.MANAGER: {
        'manage_files',
        'upload_files',
        'download_files',
        'share_files',
        'delete_files',
        'view_analytics'
    },
    RoleEnum.USER: {
        'upload_files',
        'download_files',
        'share_files',
        'delete_own_files'
    },
    RoleEnum.GUEST: {
        'download_files'
    }
}

def has_permission(user, permission):
    """Check if a user has a specific permission."""
    if not user or not user.role:
        return False
    return permission in user.role.permissions
