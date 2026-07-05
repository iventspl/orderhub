from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, render

from mainapp.models import Logger
from sales.models import SalesOrder
from users.models import Membership
from .models import Tracking

_ORDER_STATUS_RANK = {
    'DRAFT':        0,
    'IN WAREHOUSE': 1,
    'PACKED':       2,
    'SHIPPED':      3,
    'DELIVERED':    4,
}

# (key, display label, order-status rank required to be active, log action keywords)
_STEP_DEFS = [
    ('in_warehouse', 'In Warehouse', 1, ('In Warehouse', 'approved')),
    ('packed',       'Packed',       2, ('Packed',)),
    ('shipped',      'In Transit',   3, ('shipped',)),
    ('delivered',    'Delivered',    4, ('Delivered',)),
]


@login_required
def tracking_list(request):
    user_company = get_object_or_404(Membership, user=request.user).company
    trackings = list(
        Tracking.objects
        .filter(company_id=user_company.id)
        .select_related('order__customer', 'order__created_by')
        .order_by('-created_on')
    )

    # Batch-fetch all Logger entries for these orders in one query.
    order_ids = [t.order_id for t in trackings if t.order_id]
    if order_ids:
        sales_ct = ContentType.objects.get_for_model(SalesOrder)
        all_logs = (
            Logger.objects
            .filter(content_type=sales_ct, object_id__in=order_ids)
            .select_related('user')
            .order_by('timestamp')
        )
        logs_by_order = defaultdict(list)
        for log in all_logs:
            logs_by_order[log.object_id].append(log)
    else:
        logs_by_order = {}

    for tracking in trackings:
        order        = tracking.order
        order_logs   = logs_by_order.get(order.id, [])
        current_rank = _ORDER_STATUS_RANK.get(order.status or '', 0)

        def _find_log(keywords, logs=order_logs):
            for log in logs:
                if any(kw.lower() in log.action.lower() for kw in keywords):
                    return log
            return None

        steps = []

        # "Created" is always a completed step.
        steps.append({
            'label':     'Created',
            'state':     'completed',
            'timestamp': order.created_on,
            'by':        order.created_by.get_full_name() if order.created_by else '',
        })

        for _key, label, rank, keywords in _STEP_DEFS:
            if rank < current_rank:
                state = 'completed'
            elif rank == current_rank:
                state = 'active'
            else:
                state = 'pending'

            log = _find_log(keywords) if state != 'pending' else None
            steps.append({
                'label':     label,
                'state':     state,
                'timestamp': log.timestamp if log else None,
                'by':        log.user.get_full_name() if log and log.user else '',
            })

        tracking.steps = steps

    context = {
        'page':      'tracking',
        'trackings': trackings,
    }
    return render(request, 'tracking/tracking_list.html', context)
