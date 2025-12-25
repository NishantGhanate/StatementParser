def detect_union_layout(text: str) -> str:
    """
    Detect UNION Bank statement layout
    """

    t = text.lower()

    # Modern Vyom layout
    if "amount(rs.)" in t and "(dr)" in t and "(cr)" in t:
        return "UNION_TABLE_V1"

    # Classic tabular layout
    if "withdrawal" in t and "deposit" in t and "balance" in t:
        return "UNION_TABLE_V2"

    return "UNSUPPORTED"
