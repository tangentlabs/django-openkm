import datetime
import operator
import logging
import pickle

from django.db import models
from django.conf import settings
from django.db.models import Q
from django.template.defaultfilters import filesizeformat
from django.forms import forms

import openkm


class OpenKmMetadata(models.Model):
    """
    An abstract class which contains the template to store OpenKM metadata
    """
    okm_author = models.CharField(max_length=255, blank=True, null=True)
    okm_created = models.DateTimeField(auto_now_add=True)
    okm_path = models.CharField(max_length=1000, blank=True, null=True)
    okm_permissions = models.CharField(max_length=255, blank=True, null=True)
    okm_subscribed = models.CharField(max_length=255, blank=True, null=True)
    okm_uuid = models.CharField(max_length=255, blank=True, null=True)
    okm_latest_version = models.CharField(max_length=255, default='None')

    class Meta:
        abstract = True


class OpenKmFolderListManager(models.Manager):

    def custom_path_query(self, and_predicates, or_predicates):
        """
        :param and_predicates: list of AND query arguments eg. ['category', 'Region']
        :param or_predicates: list of OR query arguments eg. ['Latin-America', 'EMEA']
        :returns a list of uuids
        """
        try:
            query_set = self.get_custom_queryset(and_predicates, or_predicates)
            if not query_set:
                return []
            return [resource.okm_uuid for resource in query_set]
        except TypeError, e:
            logging.debug(e)
        except AttributeError, e:
            logging.debug(e)
        except Exception, e:
            logging.debug(e)


    def get_custom_queryset(self, and_predicates, or_predicates):
        """
        :param and_predicates: list of AND query arguments eg. ['category', 'Region']
        :param or_predicates: list of OR query arguments eg. ['Latin-America', 'EMEA']
        :returns queryset
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

            return query_set
        except TypeError, e:
            logging.debug(e)
        except AttributeError, e:
            logging.debug(e)
        except Exception, e:
            logging.debug(e)

    def _build_and_predicate_list(self, arguments):
        args = []
        for argument in arguments:
            if 'categories' in argument:
                args.append(('okm_path__icontains', '/okm:%s/' % argument))
            else:
                args.append(('okm_path__icontains', '/%s/' % argument))
        return args

    def _build_or_predicate_list(self, arguments):
        return [('okm_path__icontains', '%s' % argument) for argument in arguments]


class OpenKmFolderList(OpenKmMetadata):
    okm_has_childs = models.CharField(max_length=255, blank=True, null=True)

    objects = OpenKmFolderListManager()

    def __unicode__(self):
        return "%s" % self.okm_path

    class Meta:
        abstract = True
        verbose_name = 'OpenKM Folder List'
        verbose_name_plural = verbose_name


class OpenKmFileField(models.FileField):
    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size")

        super(OpenKmFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(OpenKmFileField, self).clean(*args, **kwargs)

        file = data.file
        try:
            if file._size > self.max_upload_size:
                raise forms.ValidationError('Please keep filesize under %s. Current filesize %s' % (filesizeformat(self.max_upload_size), filesizeformat(file._size)))
        except AttributeError:
            pass

        return data


class OpenKmDocument(OpenKmMetadata):

    okm_filename = models.CharField(max_length=255, blank=True, null=True)
    # file = OpenKmFileField(max_length=255, max_upload_size=104857600, upload_to='resources/%Y/%m/%d/', blank=True, null=True, help_text="Upload a file from your local machine")

    def upload_to_openkm(self, file_obj, taxonomy=[]):
        """Uploads the document to the OpenKM server """
        document_manager = openkm.facades.DocumentManager()
        return document_manager.create(file_obj, taxonomy=taxonomy)

    def set_model_fields(self, openkm_document):
        """
        Set the model's fields values with the meta data returned
        by OpenKM to identify the resource
        """
        self.okm_author = openkm_document.author if openkm_document.author else ''
        # self.okm_created = openkm_document.created
        self.okm_created = datetime.datetime.now()
        self.okm_path = openkm_document.path
        self.okm_permissions = openkm_document.permissions
        self.okm_subscribed = openkm_document.subscribed
        self.okm_uuid = openkm_document.uuid
        self.okm_latest_version = openkm_document.actualVersion.name
        if hasattr(self, 'mime_type'):
            self.mime_type = openkm_document.mimeType

        file_system = openkm.facades.FileSystem()
        self.okm_filename = file_system.get_file_name_from_path(openkm_document.path)

    def __unicode__(self):
        return "%s" % self.okm_filename

    class Meta:
        abstract = True
        verbose_name = 'OpenKM Document'
        verbose_name_plural = 'OpenKM Documents'

    def okm_date_string(self, date):
        """
        :param datetime.date object
        Returns an OpenKM standard date format string
        eg. 2013-04-20T17:38:42.356+01:00
        """
        if not isinstance(date, datetime.date):
            raise Exception('Argument must be a datetime.date object')
        # return date.strftime('%Y-%m-%dT00:00:00.356+01:00')
        return date.strftime('%Y%m%d%H%M%S')


class OpenKMEvent(models.Model):
    occured = models.DateTimeField()
    recorded = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    extra = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # import ipdb; ipdb.set_trace()
        if self.content:
            self.content = pickle.dumps(self.content)
        super(OpenKMEvent, self).save(*args, **kwargs)


