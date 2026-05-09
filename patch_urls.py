import re

with open('core/urls.py', 'r') as f:
    content = f.read()

new_urls = """    path('admin-tasks/export-table-data/', views.export_table_data_view, name='export_table_data'),
    path('admin-tasks/import-table-data/', views.import_table_data_view, name='import_table_data'),"""

content = re.sub(r'(path\(\'admin-tasks/draft-email-coordinators/\', views.draft_email_coordinators_view, name=\'draft_email_coordinators\'\),)', r'\1\n' + new_urls, content)

with open('core/urls.py', 'w') as f:
    f.write(content)
