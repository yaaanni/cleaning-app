from django.contrib import admin
from users.models import Client, Employee, Specialization


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'client_type', 'phone', 'company_name', 'birth_date')
    list_filter = ('client_type',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'company_name')
    ordering = ('user__last_name',)

    def get_full_name(self, obj):
        return str(obj)

    get_full_name.short_description = 'Full Name'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'email')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'email')
    filter_horizontal = ('specializations',)

    def get_full_name(self, obj):
        return str(obj)

    get_full_name.short_description = 'Full Name'
