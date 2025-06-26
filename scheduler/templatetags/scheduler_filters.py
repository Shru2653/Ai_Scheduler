from django import template

register = template.Library()

@register.filter
def get_item(lst, i):
    try:
        return lst[i]
    except:
        return None

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except:
        return 0 