from django import template
from django.contrib.contenttypes.models import ContentType
from mainapp.models import Logger

register = template.Library()

@register.simple_tag
def get_logger_entries_for_order(order):
    """
    Retrieves all Logger entries related to a specific order.
    """
    if not order:
        return Logger.objects.none()

    order_content_type = ContentType.objects.get_for_model(order, for_concrete_model=False)
    return Logger.objects.filter(content_type=order_content_type, object_id=order.id).order_by('-timestamp')