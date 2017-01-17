from django.contrib import admin

from main.models import MaintenanceObject, MaintenanceType, MaintenanceLink, MaintenanceEvent


class MaintenanceObjectAdmin(admin.ModelAdmin):
    pass


class MaintenanceTypeAdmin(admin.ModelAdmin):
    pass


class MaintenanceEventAdmin(admin.ModelAdmin):
    pass


class MaintenanceLinkAdmin(admin.ModelAdmin):
    pass


admin.site.register(MaintenanceObject, MaintenanceObjectAdmin)
admin.site.register(MaintenanceType, MaintenanceTypeAdmin)
admin.site.register(MaintenanceLink, MaintenanceEventAdmin)
admin.site.register(MaintenanceEvent, MaintenanceLinkAdmin)

admin.site.site_header = 'MJournal admin'
