from django.contrib import admin

class LearnRiteAdminSite(admin.AdminSite):
    title_header = 'LearnRite Admin'
    site_header = 'LearnRite Administration'
    index_title = 'LearnRite Site Admin'
    logout_template = 'logged_out.html'

