"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from core.views import home_view

admin.site.site_header = "System Zarządzania Odpadami Komunalnymi"
admin.site.site_title = "Odpady – panel administracyjny"
admin.site.index_title = "Administracja systemu"

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home_view, name='home'),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="auth/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("zgloszenia/", include("pickups.urls")),
    path('raporty/', include('reports.urls')),
]

