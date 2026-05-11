from django.contrib import admin
from content.models import CompanyInfo, CompanyHistory, News, Review, PromoCode, FAQ, Vacancy


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(CompanyHistory)
class CompanyHistoryAdmin(admin.ModelAdmin):
    list_display = ('year', 'description')
    ordering = ('year',)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'pub_date')
    list_filter = ('pub_date',)
    search_fields = ('title', 'full_content')
    ordering = ('-pub_date',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'date_added')
    search_fields = ('question', 'answer')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'rating', 'date')
    list_filter = ('rating', 'date')
    search_fields = ('client__user__username', 'text')
    ordering = ('-date',)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_archived')
    list_filter = ('is_archived',)
    search_fields = ('code',)
