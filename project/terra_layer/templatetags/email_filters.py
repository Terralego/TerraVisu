from django import template

register = template.Library()


@register.simple_tag
def nbsp(count=1):
    """Output non-breaking spaces"""
    return "\u00a0" * count
