"""Names and invariants for built-in RBAC roles."""

SUPER_ADMIN_ROLE_NAME = "super_admin"

# This role is provisioned only through trusted bootstrap or migration flows.
PROTECTED_ROLE_NAMES = frozenset({SUPER_ADMIN_ROLE_NAME})
