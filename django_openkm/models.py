import datetime
import operator
import logging

from django.db import models
from django.conf import settings
from django.db.models import Q

import facades

class OpenKmMetadata(models.Model):
    """
    An abstract class which contains the template to store OpenKM metadata
    """
    okm_author = models.CharField(max_length=255, blank=True, null=True)
    okm_created = models.DateTimeField(auto_now_add=True)
    okm_path = models.CharField(max_length=255, blank=True, null=True)
    okm_permissions = models.CharField(max_length=255, blank=True, null=True)
    okm_subscribed = models.CharField(max_length=255, blank=True, null=True)
    okm_uuid = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

class OpenKmFolderListManager(models.Manager):

    def custom_path_query(self, and_predicates, or_predicates):
        """
        :param and_predicates: list of AND query arguments eg. ['category', 'Region']
        :param or_predicates: list of OR query arguments eg. ['Latin-America', 'EMEA']
        :returns a list of uuids
        """
        and_predicates_list = self._build_predicate_list(and_predicates)
        or_predicates_list = self._build_predicate_list(or_predicates)

        and_list = [Q(x) for x in and_predicates_list]
        or_list = [Q(x) for x in or_predicates_list]

        query_set = super(OpenKmFolderListManager, self).get_query_set()
        try:
            query_set = query_set.filter(reduce(operator.and_, and_list) and reduce(operator.or_, or_list))
            return [resource.okm_uuid for resource in query_set]
        except TypeError, e:
            logging.exception(e)
            return []
        except AttributeError, e:
            logging.exception(e)
            return []

    def _build_predicate_list(self, arguments):
        return [('okm_path__icontains', argument) for argument in arguments]

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

                if 'taxonomy' in kwargs:
                    openkm_document = self.upload_to_openkm(file_obj, taxonomy)
                else:
                    openkm_document = self.upload_to_openkm(file_obj)

                if openkm_document:
                    self.set_model_fields(openkm_document)
                    super(OpenKmDocument, self).save(*args, **kwargs)
                else:
                    raise Exception('None found when document object was expected')
                return
            except Exception,e:
                raise

        super(OpenKmDocument, self).save(*args, **kwargs)

    def upload_to_openkm(self, file_obj, taxonomy=[]):
        """Uploads the document to the OpenKM server """
        document_manager = facades.DocumentManager()
        return document_manager.create(file_obj, taxonomy=taxonomy)

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

        file_system = facades.FileSystem()
        self.okm_filename = file_system.get_file_name_from_path(openkm_document.path)

    def __unicode__(self):
        return self.okm_filename

    class Meta:
        abstract = True
        verbose_name = 'OpenKM Document'
        verbose_name_plural = 'OpenKM Documents'

class TestOpenKmDocument(OpenKmDocument):
    pass






