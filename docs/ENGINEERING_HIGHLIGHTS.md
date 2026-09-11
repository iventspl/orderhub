# Engineering Highlights

The stock-reservation engine in `packing/signals.py` runs inside Django signals triggered by concurrent, real-world usage — multiple staff packing orders against shared warehouse stock at the same time. That surfaced a handful of concurrency and Django-internals bugs worth writing up on their own, because the fixes generalize well beyond this project.

## 1. Lost updates from read-then-write stock counts

**Symptom:** under concurrent load, two orders reserving the same low-stock SKU could both succeed even though only enough stock existed for one.

**Root cause:** the naive approach reads a value into Python, mutates it, and writes it back:

```python
# ❌ race condition
product = Product.objects.get(pk=item.product_id)   # SELECT: reserved = 10
product.reserved_quantity -= 3                        # Python: 10 - 3 = 7
product.save()
```

If two requests both read `10` before either writes, both compute `7` and the last write wins — one reservation is silently lost.

**Fix:** use Django's `F()` expressions, which compile to a single atomic SQL statement instead of a Python read/write round-trip:

```python
# ✅ atomic — one SQL statement, computed by the database
Product.objects.filter(pk=item.product_id).update(
    reserved_quantity=F('reserved_quantity') - item.quantity_required
)
```

The database performs the read-and-subtract as one operation, so concurrent updates can't overwrite each other. Combined with `select_for_update()` for the row lock, this is what makes the reservation engine safe under concurrent packing (`packing/signals.py`).

## 2. `get_object_or_404` inside a Django signal fails silently

**Symptom:** a stock cleanup that should have run on order cancellation just... didn't, with no visible error in the request/response cycle.

**Root cause:** `get_object_or_404` raises `Http404` — a view-layer exception that Django's URL dispatcher knows how to catch and turn into a 404 response. A signal handler isn't a view. Raising `Http404` there is an *unhandled* exception: the signal aborts, but the surrounding view keeps executing as if nothing happened, because Django doesn't propagate signal failures back to the caller in an obvious way.

```python
# ❌ Http404 has no handler outside a view — fails silently from the caller's perspective
user_company = get_object_or_404(Membership, user=instance.order.created_by).company
```

```python
# ✅ defensive lookup with an explicit early return
membership = Membership.objects.filter(user=instance.created_by).first()
if not membership:
    return
```

## 3. Redundant indirection through `Membership` when a direct relation already exists

**Symptom:** occasional crashes when `created_by` was `None` or had no `Membership` row, even though the object being updated already knew its own company.

**Root cause:** copy-pasted lookup logic went through `Membership` to resolve a company, when the model already carried a direct foreign key or one-to-one relation to what was actually needed:

```python
# ❌ unnecessary indirection — and a crash point if created_by has no Membership
membership = Membership.objects.filter(user=instance.created_by).select_related('company').first()
packing_order = PackingOrder.objects.filter(order=instance, company_id=membership.company_id).first()
```

```python
# ✅ PackingOrder.order is a OneToOneField — no company lookup needed at all
packing_order = PackingOrder.objects.filter(order=instance).first()
```

The rule that came out of this: before reaching for `Membership` as a bridge to `company_id`, check whether the model already has that field or relation directly.

## 4. Negative quantities violating a database check constraint

**Symptom:** on PostgreSQL, releasing a reservation could throw `new row violates check constraint "inventory_product_reserved_quantity_check"`.

**Root cause:** `reserved_quantity` is a `PositiveIntegerField`, and Postgres enforces that with a `CHECK (reserved_quantity >= 0)` constraint. An `F()` update that subtracts more than what's currently reserved computes a negative value entirely inside the database — there's no Python value to clamp beforehand:

```python
# ❌ can compute a negative value if quantity_required > current reserved_quantity
Product.objects.filter(pk=item.product_id).update(
    reserved_quantity=F('reserved_quantity') - item.quantity_required
)
```

```python
# ✅ Greatest(...) clamps the result to a floor of 0, still in one atomic SQL statement
from django.db.models.functions import Greatest

Product.objects.filter(pk=item.product_id).update(
    reserved_quantity=Greatest(F('reserved_quantity') - item.quantity_required, 0)
)
```

This pattern is used throughout the reservation-release paths (order cancellation, partial-shipment shortage handling) so a release can never push a count below zero, regardless of how reservations drifted.

## 5. A `post_save` signal deleting an object the view doesn't know is gone

**Symptom:** a delivered order would occasionally reappear in the packing queue — as if it needed to be packed again.

**Root cause:** a view called `order.save()`, which triggered a `post_save` signal that deleted the associated `PackingOrder` (cleanup for a terminal status). Execution then returned to the view, which — unaware the signal had just deleted that object — ran its own "sync" logic, saw no `PackingOrder` for an order that still had unfulfilled main-warehouse items, and **recreated one**:

```python
# ❌ the view doesn't know the signal already deleted this
if not stock_already_deducted:
    if items_requiring_main and not packing_order:
        packing_order = PackingOrder.objects.create(...)  # brings a "closed" order back to life
```

```python
# ✅ skip the sync path entirely for statuses the signal already handles as terminal
terminal_status = new_status in (SalesOrder.SalesOrderStatus.DELIVERED, SalesOrder.SalesOrderStatus.CANCELLED)
if not stock_already_deducted and not terminal_status:
    # ... sync PackingOrder only for in-progress statuses ...
```

**Takeaway:** when a `save()` call triggers a signal that mutates or deletes related objects, any code running *after* that `save()` needs to know which side effects the signal already owns — otherwise it risks "fixing" something that was correctly torn down.
