import re

with open('reports/views.py', 'r') as f:
    content = f.read()

search = """def update_summary_quantity(request):
    if not (request.user.is_authenticated and request.user.is_staff):"""

replace = """def update_summary_quantity(request):
    if not (request.user.is_authenticated and request.user.is_staff and request.user.is_active):"""

content = content.replace(search, replace)

with open('reports/views.py', 'w') as f:
    f.write(content)
