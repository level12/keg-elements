"""Common SQLAlchemy column types."""

import sqlalchemy as sa


class TimeZoneType(sa.Unicode):
    """A column type for time zones, stored as a unicode string."""

    def __init__(self, length=None, **kwargs):  # Override any given length.
        super(TimeZoneType, self).__init__(length=255, **kwargs)
