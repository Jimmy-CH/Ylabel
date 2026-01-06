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

from django.conf.urls import include
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, re_path
from django.views.generic.base import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularYAMLAPIView,
)

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
    # Legacy swagger URLs redirect to new drf-spectacular URLs
    re_path(r'^swagger\.json$', lambda request: HttpResponseRedirect('/docs/api/schema/json/'), name='schema-json'),
    re_path(r'^swagger\.yaml$', lambda request: HttpResponseRedirect('/docs/api/schema/yaml/'), name='schema-yaml'),
    re_path(
        r'^swagger/$', lambda request: HttpResponseRedirect('/docs/api/schema/swagger-ui/'), name='schema-swagger-ui'
    ),
    # Again for legacy reasons, docs/api?format=openapi redirects to docs/api/schema/json/
    path(
        'docs/api/',
        lambda request: HttpResponseRedirect('/docs/api/schema/json/')
        if request.GET.get('format') == 'openapi'
        else HttpResponseRedirect('/docs/api/schema/redoc/'),
        name='docs-api',
    ),
    path(
        'docs/',
        RedirectView.as_view(url='/static/docs/public/guide/introduction.html', permanent=False),
        name='docs-redirect',
    ),
    path('admin/', admin.site.urls),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^', include('jwt_auth.urls')),
    re_path(r'^', include('session_policy.urls')),
    path('docs/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('docs/api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('docs/api/schema/json/', SpectacularJSONAPIView.as_view(), name='schema-json'),
    path('docs/api/schema/yaml/', SpectacularYAMLAPIView.as_view(), name='schema-yaml'),
]
