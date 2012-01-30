import datetime
import operator

from django.db import models
from django.conf import settings
from django.db.models import Q

from .facades import DocumentManager, FileSystem

class OpenKmMetadata(models.Model):
    """
    An abstract class which contains the template to store OpenKM metadata
    """
    okm_author = models.CharField(max_length=255, blank=True, null=True)
    okm_created = models.DateTimeField(default=datetime.datetime.now, blank=True, null=True)
    okm_path = models.CharField(max_length=255, blank=True, null=True)
    okm_permissions = models.CharField(max_length=255, blank=True, null=True)
    okm_subscribed = models.CharField(max_length=255, blank=True, null=True)
    okm_uuid = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

class OpenKmFolderListManager(models.Manager):

    def get_uuids_from_custom_list(self, and_predicates, or_predicates):
        """
        Given the parameter format below, dynamically builds a query of AND and OR arguments and
        returns the uuids as a value_list. This allows you to be flexible with the required path
        structure
        and_predicates = [('okm_path__icontains','categories'), ('okm_path__icontains','Region')]
        or_predicates = [('okm_path__icontains', 'North America'), ('okm_path__icontains','EMEA')]
        """
        and_list = [Q(x) for x in and_predicates]
        or_list = [Q(x) for x in or_predicates]

        query_set = super(OpenKmFolderListManager, self).get_query_set()
        query_set.filter(reduce(operator.and_, and_list))
        query_set.filter(reduce(operator.or_, or_list))
        return query_set.values_list('okm_uuids')

class OpenKmFolderList(OpenKmMetadata):
    okm_has_childs = models.CharField(max_length=255, blank=True, null=True)

    objects = OpenKmFolderListManager()

    def __unicode__(self):
        return self.okm_path

    class Meta:
        abstract = True
        verbose_name = 'OpenKM Folder List'
        verbose_name_plural = verbose_name


class OpenKmDocument(OpenKmMetadata):

    okm_filename = models.CharField(max_length=255, blank=True, null=True)
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
            try:
                file_obj = self.file._get_file()
                openkm_document = self.upload_to_openkm(file_obj)
                import pdb; pdb.set_trace()

                if openkm_document:
                    self.set_model_fields(openkm_document)
                    super(OpenKmDocument, self).save(*args, **kwargs)
                else:
                    raise Exception('None found when document object was expected')
                return
            except Exception,e:
                raise

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






