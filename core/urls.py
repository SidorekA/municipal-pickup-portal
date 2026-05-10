from django.urls import path
from . import views
from reports.views import ExportCostReportView

app_name = 'core'

urlpatterns = [
    path('admin-tasks/export-cost-report/', ExportCostReportView.as_view(), name='admin_task_cost_report'),
    path('admin-tasks/', views.admin_tasks_view, name='admin_tasks'),
    path('admin-tasks/create-global-announcement/', views.create_global_announcement_view, name='create_global_announcement'),
    path('admin-tasks/disable-global-announcement/', views.disable_global_announcement_view, name='disable_global_announcement'),

    path('admin-tasks/import-collection-data/', views.import_collection_data_view, name='import_collection_data'),
    path('admin-tasks/draft-email-unconfirmed/', views.draft_email_unconfirmed_view, name='draft_email_unconfirmed'),
    path('admin-tasks/draft-email-all-users/', views.draft_email_all_users_view, name='draft_email_all_users'),
    path('admin-tasks/draft-email-coordinators/', views.draft_email_coordinators_view, name='draft_email_coordinators'),
    path('admin-tasks/export-table-data/', views.export_table_data_view, name='export_table_data'),
    path('admin-tasks/import-table-data/', views.import_table_data_view, name='import_table_data'),
    path('admin-tasks/export-auditlog/', views.export_auditlog_view, name='admin_task_auditlog_export'),
]
