from django.contrib import admin
from .models import Publisher, Category, SubCategory, Book, BookPrice, Contributor, BookContributor, Review


class BookPriceInline(admin.TabularInline):
    model = BookPrice
    extra = 0
    max_num = 4
    can_delete = False

    def get_extra(self, request, obj=None, **kwargs):
        return 4 if obj is None else max(0, 4 - obj.prices.count())


class BookAdmin(admin.ModelAdmin):
    search_fields = ('title','publisher__name')
    date_hierarchy = 'publication_date'
    list_display = ('title','category')
    list_filter = ('publisher', 'publication_date', 'category__name', 'subcategory__name')
    inlines = [BookPriceInline]

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