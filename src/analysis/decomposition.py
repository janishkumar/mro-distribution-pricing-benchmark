def decompose_growth(
    nominal_start: float,
    nominal_end: float,
    price_index_start: float,
    price_index_end: float,
) -> dict[str, float]:
    """Split nominal growth into price-driven and volume-driven components.

    Deflates the ending nominal value to starting-period dollars using the
    price index ratio, then compares that real value to the nominal start.
    """
    nominal_growth = nominal_end / nominal_start - 1
    price_growth = price_index_end / price_index_start - 1

    real_end = nominal_end / (price_index_end / price_index_start)
    volume_growth = real_end / nominal_start - 1

    return {
        "nominal_growth_pct": round(nominal_growth * 100, 4),
        "price_growth_pct": round(price_growth * 100, 4),
        "volume_growth_pct": round(volume_growth * 100, 4),
    }


def inventory_to_sales_ratio(inventories: float, sales: float) -> float | None:
    if sales == 0:
        return None
    return round(inventories / sales, 4)
