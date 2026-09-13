from src.analysis.decomposition import decompose_growth, inventory_to_sales_ratio


def test_decompose_growth_all_price_no_volume():
    # Nominal doubled, price doubled -> all price, zero real growth.
    result = decompose_growth(
        nominal_start=100.0, nominal_end=200.0,
        price_index_start=100.0, price_index_end=200.0,
    )
    assert result["nominal_growth_pct"] == 100.0
    assert result["price_growth_pct"] == 100.0
    assert abs(result["volume_growth_pct"]) < 1e-9


def test_decompose_growth_mixed():
    # Nominal +21%, price +10% -> real (volume) growth = 1.21/1.10 - 1 = 10%.
    result = decompose_growth(
        nominal_start=100.0, nominal_end=121.0,
        price_index_start=100.0, price_index_end=110.0,
    )
    assert result["nominal_growth_pct"] == 21.0
    assert result["price_growth_pct"] == 10.0
    assert abs(result["volume_growth_pct"] - 10.0) < 1e-9


def test_inventory_to_sales_ratio():
    assert inventory_to_sales_ratio(inventories=300.0, sales=150.0) == 2.0


def test_inventory_to_sales_ratio_zero_sales_returns_none():
    assert inventory_to_sales_ratio(inventories=300.0, sales=0.0) is None
