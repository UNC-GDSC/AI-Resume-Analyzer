"""Role and permission models for RBAC."""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

# Association table for user roles
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

# Association table for role permissions
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)


class Role(BaseModel):
    """Role model for RBAC."""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)

    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )


class Permission(BaseModel):
    """Permission model for RBAC."""

    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)  # e.g., "jobs", "resumes"
    action = Column(String(50), nullable=False)  # e.g., "create", "read", "update", "delete"
    description = Column(String(255))

    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
