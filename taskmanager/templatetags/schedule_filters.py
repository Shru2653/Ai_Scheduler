from django import template

register = template.Library()

@register.filter
def filter_has_perfect_matches(recommendations):
    """Check if any recommendations have perfect matches"""
    return any(rec.get('is_perfect_match', False) for rec in recommendations) 