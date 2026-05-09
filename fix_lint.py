with open('core/views.py', 'r') as f:
    content = f.read()

content = content.replace('import io\n', '')
content = content.replace('from django.urls import reverse\n', '')
content = content.replace('if count == 1: return f"{count} rekord"', 'if count == 1:\n                    return f"{count} rekord"')
content = content.replace('elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20): return f"{count} rekordy"', 'elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):\n                    return f"{count} rekordy"')

with open('core/views.py', 'w') as f:
    f.write(content)
