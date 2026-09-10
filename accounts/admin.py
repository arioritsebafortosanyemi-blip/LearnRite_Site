from django.contrib import admin

from accounts.models import Address, Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_type', 'location')
    list_filter = ('account_type', 'location')
    search_fields = ('user__username', 'user__email')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Address)
