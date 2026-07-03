from django.template import Library

register = Library()

@register.simple_tag
def add_values(value, arg):
    return value + arg
