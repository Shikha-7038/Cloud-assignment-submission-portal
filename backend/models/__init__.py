"""
This project keeps its schema and row-mapping functions inside
cloud/database_service.py rather than a separate ORM models layer, since
the "cloud database" abstraction (switching between SQLite locally and
PostgreSQL/Supabase in production) lives there and duplicating table
definitions in two places would risk them drifting out of sync.

This package is kept as an extension point: if the project grows to the
point where a full ORM (e.g. SQLAlchemy) is worth the added dependency
weight, model classes belong here, with cloud/database_service.py updated
to use them instead of raw SQL.
"""
