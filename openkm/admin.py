from django.contrib import admin

import openkm


class OpenKMEventAdmin(admin.ModelAdmin):
    pass
admin.site.register(openkm.models.OpenKMEvent, OpenKMEventAdmin)