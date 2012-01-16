from .models import OpenKmFolderList, OpenKmDocument
from django.contrib import admin

class OpenKmDocumentAdmin(admin.ModelAdmin):
    readonly_fields = ['author', 'created', 'path', 'permissions', 'subscribed', 'uuid', 'filename']

admin.site.register(OpenKmFolderList)
admin.site.register(OpenKmDocument, OpenKmDocumentAdmin)