def detect_union_layout(text: str) -> str:
    t = text.lower()

    if (
        "amount(rs.)" in t
        and "(dr)" in t
        and "(cr)" in t
    ):
        return "UNION_TABLE_V1"

    if (
        "withdrawal" in t
        and "deposit" in t
        and "balance" in t
    ):
        return "UNION_TABLE_V2"

    return "UNKNOWN"
