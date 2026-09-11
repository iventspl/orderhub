# Feature Deep-Dives

## Barcode-Scanning Packing Workflow

**Problem:** warehouse staff packing an order need a fast way to confirm the right item and quantity went into the box, from a phone, without typing anything.

**How it works:** the packing screen (`packing/static/js/packing.js`, a self-contained `PackingApp` class) opens the device camera via the [`html5-qrcode`](https://github.com/mebjas/html5-qrcode) library and matches scanned barcodes against the order's SKUs. Each item shows required vs. scanned quantity with a color-coded progress bar (`PackingOrder.progress_color_class`: red under 50%, yellow 50–89%, blue 90–99%, green at 100%). A manual **+/-** control is available as a fallback when a barcode won't scan or an item has no barcode.

When packing is submitted, `complete_packing` (`packing/views.py`) locks the order's items with `select_for_update()`, clamps each scanned quantity to what was actually required (so a bad scan can't over-report), and — critically — **logs every scan as a `PackingScanEvent`** (who, what, how much, when). That gives a full audit trail per employee, useful for spotting anomalies (repeated re-scans, zero-quantity scans) later.

If every item reached its required quantity, the `PackingOrder` moves to `PACKED` (guarded by a `pre_save` validator, see below) and the linked `SalesOrder` status updates to `PACKED` in the same transaction.

## Multi-Warehouse Stock Reservation Engine

**Problem:** an order might need stock that's split across the employee's local shop warehouse and the company's central (MAIN) warehouse — reservations need to happen atomically, without double-booking stock when multiple orders come in at once.

**How it works:** a `post_save` signal on `SalesOrderItem` (`packing/signals.py::reserve_items_and_prepare_packing`) runs inside `transaction.atomic()`:

1. Look up the order-creator's `UserProfile.assigned_warehouse`.
2. Lock and reserve as much as possible from that warehouse first (`select_for_update()` + `reserved_quantity` increment).
3. Reserve whatever's still missing from the company's MAIN warehouse — and **only for that remainder** — create/update a `PackingOrder` + `PackingOrderItem`.
4. If stock still can't cover the full request, roll the whole transaction back with a `ValidationError`.
5. Record exactly how much came from each source on the `SalesOrderItem` (`reserved_from_assigned` / `reserved_from_main`) for later reconciliation.

Row locking (`select_for_update`) plus atomic `F()`-expression updates (see [ENGINEERING_HIGHLIGHTS.md](ENGINEERING_HIGHLIGHTS.md)) mean two orders reserving the same SKU concurrently can't both succeed against stock that only exists once.

When a `PackingOrder` ships, a second signal (`deduct_main_stock_when_shipped`) deducts `stock_quantity` and releases `reserved_quantity` for the MAIN-warehouse portion, guarded by a `stock_deducted` flag so it can never run twice for the same order.

## Partial Shipment / Backorder Flow

**Problem:** sometimes not everything gets scanned (an item is missing, damaged, or short-stocked) but the customer still wants what *is* ready shipped now.

**How it works:** `complete_partial` (`packing/views.py`) lets staff either ship exactly what was scanned, or ship-and-create-a-backorder. For every short item, it:

- Releases the unused reservation back to stock (`Greatest(F('reserved_quantity') - shortage, 0)` — never lets a release push the count negative)
- Shrinks the `PackingOrderItem.quantity_required` down to what was actually scanned, so the *current* order is considered complete
- Marks the `PackingOrder` as `is_partial=True`

If a backorder is requested, a brand-new `SalesOrder` is created for just the shortfall (same customer, same ship address, status `IN_WAREHOUSE`), which re-enters the normal reservation → packing pipeline on its own.

## PDF Packing Lists

`packing_list_pdf` (`packing/views.py`) generates a printable pick list on demand using ReportLab, entirely in memory (`io.BytesIO`, no temp files). It registers a bundled `DejaVuSans.ttf` font so Polish characters (product names, addresses) render correctly — the default ReportLab fonts don't cover Unicode. Output includes SKU, product name, warehouse location, bin location, and a checkbox column for physical ticking-off while picking.

## Multi-Tenant Company Scoping

Every list/detail view resolves the requesting user's `Company` through `Membership` and filters by `company_id` — there's no cross-company data leakage by default, and switching active company (`UserProfile.active_company`) changes what a user sees without needing separate logins. See [ARCHITECTURE.md](ARCHITECTURE.md#multi-tenancy-model) for the full model.

## REST API: Typeahead Product Search

`GET /api/products/search/?q=` (`api/views.py`) powers a live product picker in order-creation forms. It's scoped to the searching user's assigned warehouse + the company's MAIN warehouse only (not every warehouse in the company), deduplicates results by SKU (preferring the MAIN-warehouse row so the ID returned always resolves consistently), and returns real-time available stock (`stock_quantity - reserved_quantity`, summed across the valid warehouses) rather than raw stock — so staff never see an item as available when it's already fully reserved. Full request/response details in [API.md](API.md).
