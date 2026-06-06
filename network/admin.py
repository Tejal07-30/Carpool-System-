from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import path
from .models import Node, Edge, ServiceConfig


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'fromnode', 'tonode')
    search_fields = ('fromnode__name', 'tonode__name')


@admin.register(ServiceConfig)
class ServiceConfigAdmin(admin.ModelAdmin):
    list_display = ('service_status', 'updated_at', 'toggle_button')
    readonly_fields = ('updated_at', 'toggle_button')

    def service_status(self, obj):
        if obj.service_enabled:
            return format_html('<span style="color:green;font-weight:bold;">● ENABLED</span>')
        return format_html('<span style="color:red;font-weight:bold;">● SUSPENDED</span>')
    service_status.short_description = "Service Status"

    def toggle_button(self, obj):
        if obj.service_enabled:
            return format_html(
                '<a class="button" href="{}suspend/" style="background:#e74c3c;color:white;padding:4px 10px;border-radius:4px;text-decoration:none;">Suspend Service</a>',
                obj.pk
            )
        return format_html(
            '<a class="button" href="{}enable/" style="background:#27ae60;color:white;padding:4px 10px;border-radius:4px;text-decoration:none;">Enable Service</a>',
            obj.pk
        )
    toggle_button.short_description = "Action"
    toggle_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/suspend/', self.admin_site.admin_view(self.suspend_view), name='serviceconfig_suspend'),
            path('<int:pk>/enable/',  self.admin_site.admin_view(self.enable_view),  name='serviceconfig_enable'),
        ]
        return custom + urls

    def suspend_view(self, request, pk):
        cfg = ServiceConfig.get()
        cfg.service_enabled = False
        cfg.save()
        self.message_user(request, "Carpooling service has been SUSPENDED.")
        return redirect('/admin/network/serviceconfig/')

    def enable_view(self, request, pk):
        cfg = ServiceConfig.get()
        cfg.service_enabled = True
        cfg.save()
        self.message_user(request, "Carpooling service has been ENABLED.")
        return redirect('/admin/network/serviceconfig/')

    def has_add_permission(self, request):
        return not ServiceConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
