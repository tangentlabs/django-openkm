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


        if and_predicates:
            and_predicates_list = self._build_and_predicate_list(and_predicates)
            and_list = [Q(x) for x in and_predicates_list]
            and_list = reduce(operator.and_, and_list)
        else:
            return []

        if or_predicates:
            or_predicates_list = self._build_or_predicate_list(or_predicates)
            or_list = [Q(x) for x in or_predicates_list]
            or_list = reduce(operator.or_, or_list)
        else:
            return []

        query_set = super(OpenKmFolderListManager, self).get_query_set()

        try:
            if or_list:
                query_set = query_set.filter(or_list)
            if and_list:
                query_set = query_set.filter(and_list)

            return [resource.okm_uuid for resource in query_set]
        except TypeError, e:
            print e
        except AttributeError, e:
            print e

    def _build_and_predicate_list(self, arguments):
        args = []
        for argument in arguments:
            if 'categories' in argument:
                args.append(('okm_path__icontains', '/okm:%s/' % argument))
            else:
                args.append(('okm_path__icontains', '/%s/' % argument))
        return args

    def _build_or_predicate_list(self, arguments):
        return [('okm_path__icontains', '/%s' % argument) for argument in arguments]

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

    def okm_date_string(self, date):
        '''
        :param datetime.date object
        Returns an OpenKM standard date format string
        eg. 2013-04-20T17:38:42.356+01:00
        '''
        if not isinstance(date, datetime.date):
            raise Exception('Argument must be a datetime.date object')
        return date.strftime('%Y-%m-%dT00:00:00.356+01:00')

class TestOpenKmDocument(OpenKmDocument):
    pass






