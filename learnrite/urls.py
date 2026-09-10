"""learnrite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import include, path, re_path
from django.conf    import settings
from django.views.static import serve



urlpatterns = [
    path('admin/', admin.site.urls),\
    path('accounts/', include('accounts.urls')),\
    path('auth/', include('allauth.urls')),\
    path('', include('store.urls')),\
]

# django.conf.urls.static.static() silently no-ops when DEBUG=False, so it
# never actually served media in production. No cloud storage configured
# yet, so route directly to django.views.static.serve instead, which has
# no such check. Move this to S3/Cloudinary if traffic grows.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]