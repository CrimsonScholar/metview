"""Any simple Python type to re-use in other modules."""

import datetime


DatetimeRange = tuple[datetime.datetime | None, datetime.datetime | None]
