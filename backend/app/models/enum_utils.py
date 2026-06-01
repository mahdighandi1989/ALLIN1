"""A read-tolerant SQLAlchemy Enum.

A single legacy/dirty row whose stored value is outside the Python enum (e.g. a
facility with ``facility_type='OD'`` from an old import) makes SQLAlchemy raise
``LookupError`` while *reading* — which 500s every endpoint that loads the table
(customer list, facility list, reports, exports), not just that one row.

``TolerantEnum`` overrides only the *result* (read) path: an unknown value is
logged and coerced to a configured fallback member instead of raising. Writes
still go through the normal validated Python enum, so no bad value is introduced
by the application. Combined with the one-off data normalisation in
``app.db_init.normalize_enum_data`` (which rewrites legacy codes to their proper
value), this makes the app robust to historical data drift.
"""
from __future__ import annotations

import logging

from sqlalchemy import Enum as _SAEnum

logger = logging.getLogger("app.models.enum")

# Per-enum-type fallback value used when the DB holds an unknown label. Keyed by
# the (lowercased) SQLAlchemy/PG type name. Values must be valid members.
_FALLBACKS = {
    "facilitytype": "other",
    "facilitystatus": "active",
    "accounttype": "retail",
    "customerstatus": "active",
}


class TolerantEnum(_SAEnum):
    """Enum that coerces unknown DB values to a fallback on read instead of 500ing.

    Intentionally adds no new constructor arguments so SQLAlchemy type adaptation
    (``adapt``/``constructor_copy``) keeps working unchanged.
    """

    def _object_value_for_elem(self, elem):
        try:
            return super()._object_value_for_elem(elem)
        except LookupError:
            fallback = _FALLBACKS.get((self.name or "").lower())
            if fallback is None and self.enums:
                fallback = self.enums[0]
            logger.warning(
                "enum %r: unknown DB value %r coerced to %r", self.name, elem, fallback
            )
            return super()._object_value_for_elem(fallback)
