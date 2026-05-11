from django.contrib import admin
from cleaning.models import ServiceType, Service, OrderItem, Order


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'price')
    list_filter = ('service_type',)
    search_fields = ('name', 'note')
    ordering = ('service_type', 'name')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'employee', 'status', 'date_execution', 'display_total_cost')

    list_filter = ('status', 'client', 'employee')

    search_fields = ('id', 'client__user__username', 'client__user__last_name', 'address')

    ordering = ('client', 'date_execution')

    date_hierarchy = 'date_execution'

    inlines = [OrderItemInline]

    def display_total_cost(self, obj):
        return f"{obj.get_total_cost()} BYN"

    display_total_cost.short_description = 'Cost of services'

    def get_queryset(self, request):
        """
        Superuser sees everything.
        Employee sees ONLY their own orders.
        """
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(employee__user=request.user)
