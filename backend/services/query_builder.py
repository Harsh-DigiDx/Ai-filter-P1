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

def build_query(parsed_data: dict, sort_by: str = None, sort_order: str = 'asc'):
    """
    Build a Supabase query from the parsed semantic data.

    Matching strategy:
    - exact_filters ("name", "doctor", "age", "gender") map directly to columns.
    - ambiguous_names check BOTH the "Name" (patient) and "Doctor" columns.
    - All of the above are OR'd together.
    - date range is applied as a strict AND on top of the OR results.

    Args:
        parsed_data (dict): Dictionary with "exact_filters" and "ambiguous_names"
        sort_by (str, optional): Key to sort by. Defaults to None.
        sort_order (str, optional): 'asc' or 'desc'. Defaults to 'asc'.

    Returns:
        A Supabase query object ready to call .execute() on.
    """
    query = supabase.table("healthcare_dataset").select("*", count="exact")



    # Fallback for backwards compatibility if the AI somehow returns the old flat structure
    if "exact_filters" not in parsed_data and "ambiguous_names" not in parsed_data:
        exact_filters = parsed_data
        ambiguous_names = []
    else:
        exact_filters = parsed_data.get("exact_filters", {})
        ambiguous_names = parsed_data.get("ambiguous_names", [])

    if not exact_filters and not ambiguous_names:
        # No search filters, but we still need to apply sorting if requested
        if sort_by and sort_by in column_map:
            db_column = column_map[sort_by]
            is_desc = (sort_order.lower() == 'desc')
            query = query.order(db_column, desc=is_desc)
        return query

    # ── Apply exact AND conditions for non-date fields ───────────────────────────────
    if exact_filters.get("name"):
        name = exact_filters["name"].replace("'", "''").strip()
        query = query.ilike("Name", f"%{name}%")

    if exact_filters.get("doctor"):
        doctor = exact_filters["doctor"].replace("'", "''").strip()
        query = query.ilike("Doctor", f"%{doctor}%")

    if exact_filters.get("age"):
        age_filter = exact_filters["age"]
        # Backwards compatibility if it's just an integer
        if isinstance(age_filter, int) or isinstance(age_filter, str):
            query = query.eq("Age", int(age_filter))
        elif isinstance(age_filter, dict):
            if "eq" in age_filter:  query = query.eq("Age",  int(age_filter["eq"]))
            if "lt" in age_filter:  query = query.lt("Age",  int(age_filter["lt"]))
            if "lte" in age_filter: query = query.lte("Age", int(age_filter["lte"]))
            if "gt" in age_filter:  query = query.gt("Age",  int(age_filter["gt"]))
            if "gte" in age_filter: query = query.gte("Age", int(age_filter["gte"]))

    if exact_filters.get("gender"):
        gender = exact_filters["gender"].strip().lower()
        query = query.eq("Gender", gender.capitalize())

    # ── Apply ambiguous names (each name searches patient OR doctor) ──────────
    # Note: In Supabase/PostgREST, successive .or_() calls are ANDed with the rest of the query.
    for amb_name in ambiguous_names:
        amb_name_sanitized = amb_name.replace("'", "''").strip()
        query = query.or_(f"Name.ilike.%{amb_name_sanitized}%,Doctor.ilike.%{amb_name_sanitized}%")

    # ── Apply date range as a strict AND on top of the OR results ─────────────
    if exact_filters.get("date"):
        date_from = exact_filters["date"].get("from")
        date_to   = exact_filters["date"].get("to")
        if date_from:
            # Convert to DD-MM-YYYY to match the database's TEXT column format (handled previously or ISO)
            query = query.gte(column_map["date"], _to_iso_date(str(date_from)))
        if date_to:
            query = query.lte(column_map["date"], _to_iso_date(str(date_to)))

    # ── Apply sorting ─────────────────────────────────────────────────────────
    if sort_by and sort_by in column_map:
        db_column = column_map[sort_by]
        is_desc = (sort_order.lower() == 'desc')
        query = query.order(db_column, desc=is_desc)

    return query

