"""Idempotent local demo administrator bootstrap."""
import os
from superset.app import create_app
from superset import security_manager
app = create_app()
with app.app_context():
    username = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
    if not security_manager.find_user(username=username):
        security_manager.add_user(username=username, first_name="Tourism", last_name="Admin",
            email=os.environ.get("SUPERSET_ADMIN_EMAIL", "admin@example.invalid"),
            role=security_manager.find_role("Admin"),
            password=os.environ["SUPERSET_ADMIN_PASSWORD"])
