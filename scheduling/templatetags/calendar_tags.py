from django import template
import calendar

register = template.Library()

MONTH_NAMES_PL = [
    '', 'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec',
    'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień'
]

@register.filter
def month_name_pl(month_number):
    try:
        return MONTH_NAMES_PL[int(month_number)]
    except (IndexError, ValueError):
        return ''

@register.filter
def fraction_color(fraction_name):
    if not fraction_name:
        return '#6c757d'
    name = fraction_name.lower()
    if 'zmieszane' in name:
        return '#343a40' # dark grey
    elif 'papier' in name:
        return '#0d6efd' # blue
    elif 'plastik' in name or 'metal' in name or 'tworzywa' in name:
        return '#ffc107' # yellow
    elif 'szkło' in name or 'szklo' in name:
        return '#198754' # green
    elif 'bio' in name:
        return '#8B4513' # saddlebrown
    else:
        return '#6c757d' # secondary grey
