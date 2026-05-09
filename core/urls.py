from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('admin-tasks/', views.admin_tasks_view, name='admin_tasks'),
    path('admin-tasks/import-collection-data/', views.import_collection_data_view, name='import_collection_data'),
    path('admin-tasks/draft-email-unconfirmed/', views.draft_email_unconfirmed_view, name='draft_email_unconfirmed'),
    path('admin-tasks/draft-email-all-users/', views.draft_email_all_users_view, name='draft_email_all_users'),
    path('admin-tasks/draft-email-coordinators/', views.draft_email_coordinators_view, name='draft_email_coordinators'),
]
