from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig

class StoreAdminConfig(AdminConfig):
    default_site = 'learnrite.admin.LearnRiteAdminSite'

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

