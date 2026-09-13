# MRO Distribution Pricing & Margin Benchmark — Executive Summary

**Category:** NAICS 4237 (Hardware, and Plumbing and Heating Equipment and Supplies Merchant Wholesalers)
**Period:** 2019–2025 (price/volume decomposition), through mid-2026 (inventory and peer margins)
**Sources:** FRED PPI & Sectoral Output (NAICS 4237), Census Monthly Wholesale Trade Survey (NAICS 4237), SEC EDGAR XBRL (FAST, GWW, WCC, MSM, CNM)

## Findings

1. **Category-wide nominal output grew 44.7% from 2019 to 2025 — but more than half of that was price, not demand.** The NAICS 4237 sectoral-output series rose from $149.5B to $216.3B (+44.7%), while the category PPI rose 25.0% over the same span. Deflating output by the price index puts real (volume-driven) growth at just 15.8%. In other words, roughly 56% of the category's nominal top-line growth since 2019 came from price increases, not from more product moving.

2. **Public MRO distributor margins did not track that price inflation — if anything, the highest-margin peers compressed.** Against 25.0% category-level price growth since 2019, gross margins for the five public comps moved far less and in mixed directions: Fastenal (FAST) fell from 47.7% to 44.6% (-3.1pp), MSC Industrial (MSM) fell from 42.75% to 41.1% (-1.6pp), W.W. Grainger (GWW) was roughly flat (39.1% → 39.5%), while WESCO (WCC) rose from 19.5% to 21.25% (+1.75pp) and Core & Main (CNM) rose from 24.1% to 26.7% (+2.6pp). The two peers with the *highest* baseline margins (FAST, MSM) are the ones that compressed — consistent with input-cost inflation outpacing their price realization even as the category as a whole raised prices.

3. **No inventory-driven pricing pressure right now.** NAICS 4237's inventory-to-sales ratio is currently 1.87 (July 2026), below its 2023 peak of 2.14 and near the middle of its 2019–2026 range (1.69–2.26). The category isn't sitting on excess inventory that would force discounting.

## Recommendations

1. **Review HD Supply's own price realization against category input-cost inflation, using FAST and MSM's margin compression as a warning signal.** If two of the best-run, highest-margin public distributors in this exact category are losing margin despite a 25% rise in category-wide prices, the likely mechanism is that their own cost inputs are rising faster than what they're able to pass through. HD Supply should check whether the same gap exists in its own P&L before assuming category price increases alone are protecting margin.

2. **This is a reasonable window to hold price rather than discount.** With inventory-to-sales near its historical median and well off 2023's peak, there's no category-wide oversupply pressure pushing toward markdowns — a materially different signal than if the ratio were at a multi-year high.

3. **Get below the NAICS 4237 aggregate for sub-category pricing decisions.** FRED does not publish a hardware-vs-plumbing/heating price split within NAICS 4237 — the only available sub-component splits "primary wholesaler services" from "all other goods," a different cut. If HD Supply wants pricing precision at the plumbing/heating vs. hardware level, it needs to track its own SKU-level input costs (copper, PVC, steel) directly rather than relying on this aggregate index — a genuine limitation of this data source, not a solvable gap.

## Known Limitations

- NAICS 4237 is a national aggregate, not HD Supply-specific — a proxy, not a direct measurement.
- Public comps sell a broader product mix than HD Supply's multifamily/hospitality focus — their margins are directional, not exact.
- PPI and Census MWTS use different collection methodologies and may not perfectly reconcile month to month.
- FRED's NAICS 4237 series family does not support a hardware-vs-plumbing/heating price split (see Recommendation 3).
- Company margin figures merge multiple XBRL tags per company (documented per-row in `comp_margins_quarterly.revenue_tag`/`cost_tag`) because companies change tagging conventions over time (e.g. post-ASC-606 adoption); this is standard practice for cross-company XBRL analysis but introduces some tagging-convention noise into direct comparisons.
