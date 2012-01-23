from django.db import models
from django.conf import settings

from .facades import DocumentManager, FileSystem

class OpenKmMetadata(models.Model):
    """
    An abstract class which contains the template to store OpenKM metadata
    """
    okm_author = models.CharField(max_length=255, blank=True, null=True)
    okm_created = models.DateTimeField(blank=True, null=True)
    okm_path = models.CharField(max_length=255, blank=True, null=True)
    okm_permissions = models.CharField(max_length=255, blank=True, null=True)
    okm_subscribed = models.CharField(max_length=255, blank=True, null=True)
    okm_uuid = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

class OpenKmFolderList(OpenKmMetadata):
    """
    Stores category folder metadata from OpenKM in a local table
    """
    okm_has_childs = models.CharField(max_length=255, blank=True, null=True)
    okm_root_folder = models.CharField(max_length=255, blank=True, null=True)
    okm_first_child_of_root = models.CharField(max_length=255, blank=True, null=True)

    def get_root_folder(self):
        return self.okm_path.split("/")[1:][0]

    def get_first_child_of_root(self):
        return self.okm_path.split("/")[1:][1]

    def __unicode__(self):
        return self.okm_path

    class Meta:
        abstract = True
        verbose_name = 'OpenKM Folder List'
        verbose_name_plural = verbose_name


class OpenKmDocument(OpenKmMetadata):

    okm_filename = models.CharField(max_length=255, blank=True, null=True)
    okm_file = models.FileField(max_length=255, upload_to='resources/%Y/%m/%d/', blank=True, null=True, help_text="Upload a file from your local machine")

    def save(self, *args, **kwargs):
        """
        Custom save functionality.
        (1) Upload document to OpenKM
        (2) Set the local model fields with the returned metadata from (1)
        *Note that locally stored files will be periodically deleted
        """
        if self.file and self.id is None:
            """ A new resource to be uploaded OpenKM """
            file_obj = self.file._get_file()
            openkm_document = self.upload_to_openkm(file_obj)
            self.set_model_fields(openkm_document)
            super(OpenKmDocument, self).save(*args, **kwargs)
            return

        super(OpenKmDocument, self).save(*args, **kwargs)

    def upload_to_openkm(self, file_obj):
        """Uploads the document to the OpenKM server """
        document_manager = DocumentManager()
        return document_manager.create(file_obj)

    def set_model_fields(self, openkm_document):
        """
        Set the model's fields values with the meta data returned
        by OpenKM to identify the resource
        """
        self.okm_author = openkm_document.author
        self.okm_created = openkm_document.created
        self.okm_path = openkm_document.path
        self.okm_permissions = openkm_document.permissions
        self.okm_subscribed = openkm_document.subscribed
        self.okm_uuid = openkm_document.uuid

        file_system = FileSystem()
        self.okm_filename = file_system.get_file_name_from_path(openkm_document.path)

    def __unicode__(self):
        return self.okm_filename

    class Meta:
        abstract = True
        verbose_name = 'OpenKM Document'
        verbose_name_plural = 'OpenKM Documents'






