from config.supabase_client import supabase
from datetime import datetime


def _to_iso_date(date_str: str) -> str:
    """
    Normalise any date string the LLM returns to YYYY-MM-DD (ISO date),
    which is what PostgreSQL's DATE column type expects for gte/lte comparisons.

    Handles:
      - Already correct:  "2025-02-26"                 → "2025-02-26"
      - ISO datetime:     "2025-02-26T00:00:00"         → "2025-02-26"
      - ISO with µs:      "2025-02-26T15:44:15.123456"  → "2025-02-26"
    """
    date_str = date_str.strip()
    # Take only the date portion (first 10 chars of any ISO datetime)
    if len(date_str) >= 10:
        return date_str[:10]
    return date_str


# Maps extracted filter keys to exact Supabase column names
column_map = {
    "gender" : "Gender",
    "age"    : "Age",
    "name"   : "Name",
    "doctor" : "Doctor",
    "date"   : "Date of Admission",
}

def build_query(filters: dict):
    """
    Build a Supabase query from the extracted filters.

    Matching strategy:
    - name   : case-insensitive substring match on the Name column
                (matches first name, last name, or any part of the full name)
    - doctor : case-insensitive substring match on the Doctor column
                (same logic as name)
    - age    : exact integer match
    - gender : exact match ("male" / "female")
    - date   : range match applied as a hard AND filter on top of everything else

    All non-date filters are combined with OR so that a record is returned
    if it satisfies ANY of the provided criteria.  The date range is then
    applied as a strict AND on the result set.

    Args:
        filters (dict): Dictionary of filter keys/values from the NLP parser.

    Returns:
        A Supabase query object ready to call .execute() on.
    """
    query = supabase.table("healthcare_dataset").select("*", count="exact")

    if not filters:
        return query  # No filters → return everything

    # ── Build OR conditions for non-date fields ───────────────────────────────
    or_parts: list[str] = []

    if filters.get("name"):
        # Sanitise the value to prevent injection (remove % and ')
        name = filters["name"].replace("'", "''").strip()
        or_parts.append(f"Name.ilike.%{name}%")

    if filters.get("doctor"):
        doctor = filters["doctor"].replace("'", "''").strip()
        or_parts.append(f"Doctor.ilike.%{doctor}%")

    if filters.get("age") is not None:
        or_parts.append(f"Age.eq.{int(filters['age'])}")

    if filters.get("gender"):
        gender = filters["gender"].strip().lower()
        # Capitalise first letter to match typical DB values ("Male"/"Female")
        or_parts.append(f"Gender.eq.{gender.capitalize()}")

    # Apply all as a single OR filter (one record returned per match, no dups)
    if or_parts:
        query = query.or_(",".join(or_parts))

    # ── Apply date range as a strict AND on top of the OR results ─────────────
    if filters.get("date"):
        date_from = filters["date"].get("from")
        date_to   = filters["date"].get("to")
        if date_from:
            # Convert to DD-MM-YYYY to match the database's TEXT column format
            query = query.gte(column_map["date"], _to_iso_date(str(date_from)))
        if date_to:
            query = query.lte(column_map["date"], _to_iso_date(str(date_to)))

    return query
