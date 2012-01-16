from django.db import models

from .facades import Session, DocumentManager, FileSystem

class OpenKmMetadata(models.Model):
    """
    An abstract class which contains the template to store OpenKM metadata
    """
    author = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    permissions = models.CharField(max_length=255, blank=True, null=True)
    subscribed = models.CharField(max_length=255, blank=True, null=True)
    uuid = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

class OpenKmFolderList(OpenKmMetadata):
    """
    Stores category folder metadata from OpenKM in a local table
    """
    has_childs = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.path

    class Meta:
        verbose_name = 'OpenKM Folder List'
        verbose_name_plural = verbose_name

class OpenKmDocument(OpenKmMetadata):

    filename = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(max_length=255, upload_to='resources/%Y/%m/%d/', blank=True, null=True, help_text="Upload a file from your local machine")

    def save(self, *args, **kwargs):
        """
        Custom save functionality.
        (1) Upload document to OpenKM
        (2) Set the local model fields with the returned metadata from (1)
        *Note that locally stored files will be periodically deleted
        """
        if self.file and self.id is None:
            """ A new resource to be uploaded OpenKM """
            session = Session()
            session.open()
            file_obj = self.file._get_file()
            openkm_document = self.upload_to_openkm(file_obj)
            session.close()
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
        self.author = openkm_document.author
        self.created = openkm_document.created
        self.path = openkm_document.path
        self.permissions = openkm_document.permissions
        self.subscribed = openkm_document.subscribed
        self.uuid = openkm_document.uuid

        file_system = FileSystem()
        self.filename = file_system.get_filename_from_path(self.path)

    def __unicode__(self):
        return self.filename

    class Meta:
        verbose_name = 'OpenKM Document'
        verbose_name_plural = 'OpenKM Documents'



