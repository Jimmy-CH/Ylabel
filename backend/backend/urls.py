"""
URL configuration for backend project.

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

from django.urls import path, re_path
from django.conf.urls import include

urlpatterns = [
    re_path(r'^', include('organizations.urls')),
    re_path(r'^', include('projects.urls')),
    re_path(r'^', include('data_import.urls')),
    re_path(r'^', include('data_manager.urls')),
    re_path(r'^', include('data_export.urls')),
    re_path(r'^', include('users.urls')),
    re_path(r'^', include('tasks.urls')),
    re_path(r'^', include('io_storages.urls')),
    re_path(r'^', include('ml.urls')),
    re_path(r'^', include('webhooks.urls')),
    re_path(r'^', include('labels_manager.urls')),
    re_path(r'^', include('fsm.urls')),
]
