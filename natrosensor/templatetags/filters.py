from django import template

register = template.Library()

@register.filter(name='addClass')
def addClass(value, arg):
    return value.as_widget(attrs={'class': arg})

@register.filter
def compute_height(value, max_count):
    return int(value / max_count * 0.8 * 100) if max_count != 0 else 0