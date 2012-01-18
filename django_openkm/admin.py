from django.contrib import admin

from .models import OpenKmFolderList, OpenKmDocument

class OpenKmDocumentAdmin(admin.ModelAdmin):
    readonly_fields = ['author', 'created', 'path', 'permissions', 'subscribed', 'uuid', 'filename']

admin.site.register(OpenKmFolderList)
admin.site.register(OpenKmDocument, OpenKmDocumentAdmin)