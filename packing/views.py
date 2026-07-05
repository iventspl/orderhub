import io
import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from tracking.models import Tracking
from users.models import Membership

from .models import PackingOrder, PackingOrderItem, PackingScanEvent
from sales.models import SalesOrder, SalesOrderItem


@login_required
def packing_list(request):
    user_company = get_object_or_404(Membership, user=request.user).company

    # Zamówienia czekające w kolejce – jeszcze nie zaczęte
    queue_list = PackingOrder.objects.filter(
        company_id=user_company.id,
        status=PackingOrder.PackingStatus.PENDING,
    ).order_by('-created_on')

    # Zamówienia aktualnie pakowane – będą widoczne z paskiem postępu
    in_progress_list = PackingOrder.objects.filter(
        company_id=user_company.id,
        status=PackingOrder.PackingStatus.IN_PROGRESS,
    ).order_by('-created_on')

    # Zamówienia spakowane – czekają na wysyłkę
    packed_list = PackingOrder.objects.filter(
        company_id=user_company.id,
        status=PackingOrder.PackingStatus.PACKED,
    ).order_by('-packed_on')

    # Historia – wysłane
    history_list = PackingOrder.objects.filter(
        company_id=user_company.id,
        status=PackingOrder.PackingStatus.SHIPPED,
    ).select_related('order', 'packed_by').order_by('-packed_on')

    context = {
        'page': 'packing',
        'queue_list': queue_list,
        'in_progress_list': in_progress_list,
        'packed_list': packed_list,
        'history_list': history_list,
    }
    return render(request, 'packing/packing_list.html', context)


@login_required
@require_POST
def start_packing(request):
    """
    Batch endpoint – przyjmuje listę ID PackingOrder i zmienia ich status
    z PENDING na IN_PROGRESS. Wywoływany gdy użytkownik zaznaczy checkboxy
    w kolejce i kliknie "Start packing".

    Przyjmuje JSON: {"order_ids": [1, 2, 3]}
    Zwraca JSON:    {"ok": true, "started": <liczba_zaktualizowanych>}
    """
    user_company = get_object_or_404(Membership, user=request.user).company

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    order_ids = payload.get('order_ids', [])
    if not isinstance(order_ids, list) or not order_ids:
        return JsonResponse({'ok': False, 'error': 'order_ids are required.'}, status=400)

    # Filtrujemy po company_id – ochrona przed zmianą cudzych zamówień
    updated = PackingOrder.objects.filter(
        pk__in=order_ids,
        company_id=user_company.id,
        status=PackingOrder.PackingStatus.PENDING,
    ).update(status=PackingOrder.PackingStatus.IN_PROGRESS)

    return JsonResponse({'ok': True, 'started': updated})


@login_required
@require_POST
def complete_packing(request, packing_order_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    packing_order = get_object_or_404(PackingOrder, pk=packing_order_id, company_id=user_company.id)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)

    scanned_items = payload.get('items', [])
    if not isinstance(scanned_items, list):
        return JsonResponse({'ok': False, 'error': 'Invalid items payload.'}, status=400)

    with transaction.atomic():
        # product FK jest nullable, więc przy FOR UPDATE nie łączymy przez select_related('product').
        # Kluczem mapy jest snapshot/fallback SKU (resolved_sku), nie bezpośredni item.product.sku.
        items_by_sku = {
            item.resolved_sku: item
            for item in PackingOrderItem.objects.select_for_update().filter(
                packing_order=packing_order
            )
        }

        for row in scanned_items:
            if not isinstance(row, dict):
                continue

            sku = row.get('sku')
            quantity_scanned = row.get('quantity_scanned')
            packing_item = items_by_sku.get(sku)
            if not packing_item:
                continue

            try:
                quantity_scanned = int(quantity_scanned)
            except (TypeError, ValueError):
                continue

            if quantity_scanned < 0:
                quantity_scanned = 0

            final_qty = min(quantity_scanned, packing_item.quantity_required)
            packing_item.quantity_scanned = final_qty
            packing_item.save(update_fields=['quantity_scanned'])

            # Loguj zdarzenie skanowania jeśli cokolwiek zostało zeskanowane
            if final_qty > 0:
                PackingScanEvent.objects.create(
                    packing_order=packing_order,
                    packing_item=packing_item,
                    user=request.user if request.user.is_authenticated else None,
                    quantity=final_qty,
                    company_id=packing_order.company_id,
                )

        shortage = [
            {
                'sku': i.resolved_sku,
                'name': i.resolved_name,
                'required': i.quantity_required,
                'scanned': i.quantity_scanned,
            }
            for i in PackingOrderItem.objects.filter(packing_order=packing_order)
            if i.quantity_scanned < i.quantity_required
        ]

        if shortage:
            return JsonResponse({'ok': True, 'partial': True, 'shortage': shortage})

        packing_order.status = PackingOrder.PackingStatus.PACKED
        if request.user.is_authenticated:
            packing_order.packed_by = request.user

        try:
            packing_order.save(update_fields=['status', 'packed_by'])
        except ValidationError as exc:
            message = exc.messages[0] if getattr(exc, 'messages', None) else str(exc)
            return JsonResponse({'ok': False, 'error': message}, status=400)

        SalesOrder.objects.filter(pk=packing_order.order_id).update(
            status=SalesOrder.SalesOrderStatus.PACKED
        )

    return JsonResponse({'ok': True})


@login_required
@require_POST
def complete_partial(request, packing_order_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    packing_order = get_object_or_404(PackingOrder, pk=packing_order_id, company_id=user_company.id)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)

    action = payload.get('action')
    if action not in ('ship_partial', 'create_backorder'):
        return JsonResponse({'ok': False, 'error': 'action must be ship_partial or create_backorder.'}, status=400)

    backorder_created = False
    backorder_reason = None

    with transaction.atomic():
        items = list(PackingOrderItem.objects.select_for_update().filter(
            packing_order=packing_order,
            company_id=user_company.id,
        ))

        shortage_items = [(item, item.quantity_required - item.quantity_scanned) for item in items if item.quantity_scanned < item.quantity_required]

        for item, shortage_qty in shortage_items:
            SalesOrderItem.objects.filter(pk=item.sales_order_item_id).update(
                reserved_from_main=Greatest(F('reserved_from_main') - shortage_qty, 0)
            )
            if item.product_id:
                from inventory.models import Product
                Product.objects.filter(pk=item.product_id).update(
                    reserved_quantity=Greatest(F('reserved_quantity') - shortage_qty, 0)
                )
            item.quantity_required = item.quantity_scanned
            item.save(update_fields=['quantity_required'])

        packing_order.is_partial = True
        packing_order.status = PackingOrder.PackingStatus.PACKED
        if request.user.is_authenticated:
            packing_order.packed_by = request.user
        packing_order.save(update_fields=['is_partial', 'status', 'packed_by'])

        SalesOrder.objects.filter(pk=packing_order.order_id).update(
            status=SalesOrder.SalesOrderStatus.PACKED
        )

        if action == 'create_backorder':
            try:
                with transaction.atomic():
                    original_order = packing_order.order
                    backorder = SalesOrder.objects.create(
                        customer=original_order.customer,
                        status=SalesOrder.SalesOrderStatus.IN_WAREHOUSE,
                        notes=f'Backorder for {original_order.order_number}',
                        company=user_company,
                        created_by=original_order.created_by,
                        ship_address=original_order.ship_address,
                    )
                    backorder.generate_order_number()
                    for item, shortage_qty in shortage_items:
                        SalesOrderItem.objects.create(
                            order=backorder,
                            product=item.product,
                            quantity=shortage_qty,
                            company=user_company,
                        )
                    backorder.calculate_value()
                    backorder_created = True
            except (ValidationError, Exception) as exc:
                messages = getattr(exc, 'messages', None)
                backorder_reason = messages[0] if messages else str(exc)
                backorder_created = False

    if action == 'create_backorder':
        if backorder_created:
            msg = 'Partial shipment completed. Backorder created for shortage quantities.'
        else:
            msg = f'Partial shipment completed. Backorder could not be created: {backorder_reason}'
        return JsonResponse({'ok': True, 'backorder_created': backorder_created, 'message': msg})

    return JsonResponse({'ok': True, 'message': 'Partial shipment completed.'})


@login_required
@require_POST
def ship_packing(request, packing_order_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    packing_order = get_object_or_404(PackingOrder, pk=packing_order_id, company_id=user_company.id)
    if packing_order.status != PackingOrder.PackingStatus.PACKED:
        return JsonResponse({'ok': False, 'error': 'Only PACKED orders can be shipped.'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)

    carrier = payload.get('carrier')
    tracking_number = payload.get('tracking_number')
    packed_order = payload.get('order_id')
    packing_order = get_object_or_404(PackingOrder, pk=packed_order, company_id=user_company.id)
    if not carrier or not tracking_number:
        return JsonResponse({'ok': False, 'error': 'carrier and tracking_number are required.'}, status=400)

    tracking_status = Tracking.TrackingStatus.SHIPPED
    tracking_defaults = {
        'carrier': carrier,
        'status': tracking_status,
        'created_by': request.user if request.user.is_authenticated else packing_order.order.created_by,
    }

    with transaction.atomic():
        tracking, _ = Tracking.objects.update_or_create(
            tracking_number=tracking_number,
            defaults=tracking_defaults,
            order=packing_order.order,
            packed_order=packing_order,
            company=user_company
        )

        SalesOrder.objects.filter(pk=packing_order.order_id).update(
            status=SalesOrder.SalesOrderStatus.SHIPPED,
            tracking=tracking,
        )
        # Używamy .save() zamiast .update(), żeby odpalić sygnał post_save
        # → deduct_main_stock_when_shipped zdejmie stock i reserved_quantity
        packing_order.status = PackingOrder.PackingStatus.SHIPPED
        packing_order.save(update_fields=['status'])

    return JsonResponse({'ok': True})


@login_required
# @require_POST
def packing_started_cancel(request, packing_order_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    packing_order = get_object_or_404(PackingOrder, pk=packing_order_id, company_id=user_company.id)
    packing_items = PackingOrderItem.objects.filter(packing_order=packing_order)
    if packing_order.status != PackingOrder.PackingStatus.IN_PROGRESS:
        return JsonResponse({'ok': False, 'error': 'Only IN_PROGRESS orders can be cancelled.'}, status=400)

    with transaction.atomic():
        packing_order.status = PackingOrder.PackingStatus.PENDING
        for item in packing_items:
            item.quantity_scanned = 0
            item.save(update_fields=['quantity_scanned'])
        packing_order.save(update_fields=['status'])

    return redirect('packing:packing_list')


@login_required
@require_POST
def deliver_packing(request, packing_order_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    packing_order = get_object_or_404(PackingOrder, pk=packing_order_id, company_id=user_company.id)
    if packing_order.status != PackingOrder.PackingStatus.SHIPPED:
        return JsonResponse({'ok': False, 'error': 'Only SHIPPED orders can be delivered.'}, status=400)

    with transaction.atomic():
        order = packing_order.order
        if order.tracking_id:
            Tracking.objects.filter(pk=order.tracking_id, company_id=user_company.id).update(status=Tracking.TrackingStatus.DELIVERED)

        SalesOrder.objects.filter(pk=order.pk, company_id=user_company.id).update(status=SalesOrder.SalesOrderStatus.DELIVERED)

    return JsonResponse({'ok': True})


@login_required
def packing_list_pdf(request, packing_order_id):
    """
    Generuje PDF z listą pozycji do spakowania dla danego PackingOrder.

    Jak to działa:
      1. Pobieramy PackingOrder + pozycje z bazy (filtr company_id dla bezpieczeństwa).
      2. Tworzymy pusty bufor w pamięci (io.BytesIO) zamiast zapisywać na dysk.
      3. Budujemy PDF przez reportlab: nagłówek, tabela, stopka.
      4. Zwracamy HttpResponse z Content-Type=application/pdf
         i nagłówkiem Content-Disposition → przeglądarka proponuje zapis pliku.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from django.conf import settings
    import os

    # Rejestracja czcionki TTF z pełnym wsparciem Unicode (polskie znaki).
    # DejaVuSans.ttf jest dołączona do projektu w packing/static/fonts/
    # dzięki czemu działa zarówno lokalnie jak i na serwerze produkcyjnym.
    font_path = os.path.join(settings.BASE_DIR, 'packing', 'static', 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVu', font_path))
    FONT = 'DejaVu'

    user_company = get_object_or_404(Membership, user=request.user).company
    packing_order = get_object_or_404(
        PackingOrder.objects.select_related('order__customer'),
        pk=packing_order_id,
        company_id=user_company.id,
    )
    items = (
        PackingOrderItem.objects
        .filter(packing_order=packing_order)
        .select_related('product__product_location')
        .order_by('product_sku')
    )

    #  Bufor w pamięci 
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', parent=styles['Heading1'], fontName=FONT, fontSize=14, alignment=TA_CENTER)
    sub_style   = ParagraphStyle('sub',   parent=styles['Normal'],   fontName=FONT, fontSize=9,  alignment=TA_CENTER, textColor=colors.gray)

    order_number = packing_order.order.order_number or f'#{packing_order.id}'
    customer = str(packing_order.order.customer.customer_code) if packing_order.order.customer.customer_code else str(packing_order.order.customer)

    # ── Treść dokumentu ────────────────────────────────────────────
    story = [
        Paragraph(f'Packing List — {order_number}', title_style),
        Paragraph(f'Customer: {customer} &nbsp;&nbsp; Company: {user_company.name}', sub_style),
        Spacer(1, 0.5 * cm),
    ]

    # Nagłówek tabeli
    table_data = [['', 'SKU', 'Product', 'Location', 'Bin', 'Required']]

    for item in items:
        location = ''
        bin_location = ''
        if item.product and item.product.product_location:
            location = item.product.product_location.name
        if item.product and item.product.bin_location:
            bin_location = item.product.bin_location
        table_data.append([
            '☐',               # pusty kwadrat do ręcznego zaznaczenia
            item.resolved_sku,
            item.resolved_name,
            location,
            bin_location,
            str(item.quantity_required),
        ])

    if not table_data[1:]:
        table_data.append(['☐', '—', 'No items', '', ''])

    # Szerokości kolumn: checkbox | SKU | Product | Location | Required
    col_widths = [1 * cm, 3 * cm, 6 * cm, 4 * cm, 2 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Nagłówek
        ('BACKGROUND',   (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
        ('FONTNAME',     (0, 0), (-1, 0), FONT),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('ALIGN',        (0, 0), (-1, 0), 'CENTER'),
        # Wiersze danych
        ('FONTNAME',     (0, 1), (-1, -1), FONT),
        ('FONTSIZE',     (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        # Kolumna checkboxa – wyśrodkowana, rozmiar dopasowany do reszty wiersza
        ('FONTSIZE',     (0, 1), (0, -1), 10),
        ('ALIGN',        (0, 0), (0, -1), 'CENTER'),
        # Wyrównanie pionowe do środka dla całej tabeli
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        # Kolumny ilości wyrównane do środka
        ('ALIGN',        (4, 1), (4, -1), 'CENTER'),
        # Obramowanie
        ('GRID',         (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(table)

    doc.build(story)

    # ── Odpowiedź HTTP z PDF ─────────────────────────────────────
    buffer.seek(0)
    filename = f'packing-list-{order_number}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
