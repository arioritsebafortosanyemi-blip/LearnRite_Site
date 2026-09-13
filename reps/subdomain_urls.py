"""The root urlconf used for the reps.<domain> subdomain (see
reps/middleware.py) - wraps reps/urls.py at the root path so it keeps its
"reps:" namespace (that only exists via include(), not by pointing
request.urlconf straight at a module with app_name set) while every URL is
now relative to the subdomain's own root instead of /reps/."""
from django.urls import include, path

urlpatterns = [
    path('', include('reps.urls')),
]
