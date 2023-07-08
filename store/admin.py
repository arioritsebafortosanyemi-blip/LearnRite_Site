from django.contrib import admin
from .models import Publisher, Category, SubCategory, Book, Contributor, BookContributor, Review


class BookAdmin(admin.ModelAdmin):
    search_fields = ('title','publisher__name')
    date_hierarchy = 'publication_date'
    list_display = ('title','category')
    list_filter = ('publisher', 'publication_date', 'category__name', 'subcategory__name')

class ContributorAdmin(admin.ModelAdmin):
    list_display = ('last_names', 'first_names')
    search_fields = ('last_names__startswith','first_names')
    list_filter = ('last_names',)



admin.site.register(Publisher)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Book, BookAdmin)
admin.site.register(Contributor, ContributorAdmin)
admin.site.register(BookContributor)
admin.site.register(Review)