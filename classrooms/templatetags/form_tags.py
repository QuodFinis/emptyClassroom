from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """Add a CSS class to a form field."""
    return value.as_widget(attrs={'class': arg})

@register.filter(name='format_time')
def format_time(time_value):
    """Format time without seconds."""
    if time_value:
        return time_value.strftime('%I:%M %p')  # 12-hour format with AM/PM
    return ''
