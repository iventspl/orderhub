# REST API

Built with Django REST Framework. Base path: `/api/`. Both endpoints require an authenticated session (`request.user.is_authenticated`) and are scoped to the caller's `Company` via `Membership` — there is no cross-tenant access.

## `GET /api/sales-orders/`

Returns every `SalesOrder` for the authenticated user's company, newest first, with customer, line items, and tracking nested inline (`SalesOrderSerializer` in `api/serializers.py`) — built for a single round-trip render of an order list/detail UI.

**Auth:** required (session). Returns `401` if unauthenticated, `403` if the user has no `Membership`.

**Response `200`:**

```json
[
  {
    "id": 42,
    "order_number": "SO-20260706-0042",
    "value": "129.99",
    "status": "SHIPPED",
    "payment_method": "PREPAID",
    "payment_method_display": "Prepaid",
    "notes": "Leave at front desk",
    "ship_address": "12 Market St, Warsaw",
    "created_on": "2026-07-06 14:32",
    "customer": {
      "id": 7,
      "full_name": "Anna Kowalska",
      "first_name": "Anna",
      "last_name": "Kowalska",
      "email": "anna@example.com",
      "city": "Warsaw",
      "address": "12 Market St",
      "zip_code": "00-001",
      "country": "Poland",
      "phone_number": "+48 600 000 000"
    },
    "salesorderitem_set": [
      {
        "id": 101,
        "resolved_sku": "SKU-1234",
        "resolved_name": "Wireless Mouse",
        "quantity": 2,
        "reserved_from_assigned": 2,
        "reserved_from_main": 0
      }
    ],
    "tracking": {
      "tracking_number": "1Z999AA10123456784",
      "carrier": "UPS",
      "status": "SHIPPED"
    }
  }
]
```

`resolved_sku` / `resolved_name` fall back to a snapshot taken at order time if the underlying `Product` was later deleted, so historical orders stay readable. `tracking` is `null` until the order ships.

## `GET /api/products/search/?q=<query>`

Typeahead product search for order-entry forms. Matches on product name or SKU (case-insensitive `icontains`), scoped to the caller's **assigned warehouse + the company's MAIN warehouse only**, deduplicated by SKU, capped at 10 results.

**Query params:**

| Param | Required | Description |
|---|---|---|
| `q` | yes | Search term matched against product name and SKU |

**Auth:** required. Returns `401` unauthenticated, `403` with no `Membership`, `400` if `q` is missing/empty.

**Response `200`:**

```json
[
  {
    "id": 88,
    "name": "Wireless Mouse",
    "sku": "SKU-1234",
    "get_total_quantity": 17
  }
]
```

`get_total_quantity` is **available** stock (`stock_quantity - reserved_quantity`, summed across the caller's valid warehouses), not raw stock on hand — so a fully-reserved item shows as unavailable even if physical units remain on the shelf.
