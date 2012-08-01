import logging
logger = logging.getLogger( __name__ )

from django.conf import settings
from django.db import transaction

from suds import WebFault

import client, facades, utils, sync


class SyncKeywords(object):

    def __init__(self):
        self.keyword = facades.Keyword()

    def get_tags_from_document(self, document):
        """
        Returns an object's tags as a list
        """
        return document.tags.split(',')

    def add_keyword_to_openkm_document(self, path, keyword):
        return self.keyword.add(path, keyword.strip())

    def write_keywords_to_openkm_document(self, path, keywords):
        """
        :param path: string  The document path on OpenKM
        :param keywords: list The keywords to be associated with a document
        """
        for keyword in keywords:
            self.add_keyword_to_openkm_document(path, keyword)

    def confirm_keywords_written_to_openkm(self, path, expected_keywords):
        """
        Query OpenKM to make sure tags have been set
        :param path: OpenKM node path of document
        :param expected_keywords: list
        """
        openkm_keywords = self.keyword.get_for_document(path)
        diff = set(expected_keywords).difference(set(openkm_keywords))

        if diff == 0:
            return True
        else:
            return False

    def single_document_django_to_helix(self, document, openkm_document):
        """
        Writes the tags from a GSA document to a Helix document as keywords
        Assumes that the document exists on OpenKM
        :param document: Document model object
        :param openkm_document: OpenKM document object
        """
        tags = self.get_tags_from_document(document)
        self.write_keywords_to_openkm_document(openkm_document.path, tags)

    def single_document_helix_to_django(self, document, openkm_document):
        """
        Updates the tags on a Django model from the keywords on OpenKM
        :param document: document model object
        :param openkm_document: OpenKM document object
        """
        keywords = self.keyword.get_for_document(openkm_document.path)
        tags = ','.join(keywords)
        document.update_tags(tags)


class SyncCategories(object):
    """
    Syncronises categories from Django to OpenKM.
    """
    # Django Model Class -> OpenKM Category
    MODEL_CATEGORY_MAP = {}

    map = {
        'Industry': 'Industries',
        'Region': 'Region',
        'Role': 'Roles',
        'Solution': 'Solutions',
        'Task': 'Tasks',
        'Product': 'Products'
    }

    def __init__(self):
        self.category = facades.Category()

    def create_top_level_categories(self, parent_path=False):
        """
        Creates the top level categories, as first level children of the parent_path
        :param parent_path: (string) defaults to category root
        """
        if not parent_path:
            parent_path = self.category.get_category_root().path
        logger.info("parent path: %s", parent_path)

        for category_name in self.MODEL_CATEGORY_MAP.values():
            path = self.category.construct_valid_path_string(parent_path, category_name)
            try:
                self.category.create(path)
                logger.info("%s created" % path)
            except:
                logger.info("%s creation failed" % path)

    def get_child_categories(self, parent_path):
        """
        :param parent_path: string node path
        :return object
        """
        if not parent_path:
            parent_path = self.category.get_category_root().path

        return self.category.folder.get_children(parent_path)

    def django_to_openkm(self):
        for django_model_class, openkm_model_name in self.MODEL_CATEGORY_MAP.items():
            self.create_categories_from_django_model(django_model_class, openkm_model_name)

    def create_categories_from_django_model(self, model_class, category_name):
        """
        Creates child sub-categories on OpenKM in a parent folder.
        The parent category should already exist.
        :param model_class: model class object
        :param category_name: string (name of the Category on OpenKM)
        @todo confirm the replace char
        """
        objects = model_class.objects.all()

        for object in objects:
            try:
                self.category.create('/okm:categories/%s/%s' % (category_name,\
                                                                object.__unicode__().replace('/','--')))
            except:
                logger.info("%s creation failed" % object.__unicode__().replace('/',''))

    def get_objects_from_m2m_model(self, document, related_model_class):
        """
        Accepts a Document and a single class object of a many-to-many field
        :returns queryset the related model objects associated with the given document
        """
        method_name = '%s' % related_model_class.__name__.lower()
        _set = getattr(document, method_name)

        return _set.all()

    def get_related_objects_from_model(self, document, related_model_name):
        """
        :param document: object instance of Document
        :param related_model_name: string relate model name
        :returns a list of related model objects
        Assumes that the related model is:
        - many-to-many
        - is accessible from the document via modelname_set()
        For example if called with a document and the string region
        it will return the regions associated with this document
        """
        method_name = '%s' % related_model_name
        if hasattr(document, method_name):
            _member = getattr(document, method_name)
            return _member.all()
        else:
            logger.error("Object does not have method %s" % method_name)


class SyncProperties(object):

    def __init__(self):
        self.property = facades.Property()
        self.property_group = client.PropertyGroup()

    def prepare_properties_dict(self, map, document):
        """
        @todo pass getter functions in to get the values
        :param document: Django model object instance
        :returns dict
        """
        map['okg:customProperties']['okp:customProperties.title'] = [document.name]
        map['okg:customProperties']['okp:customProperties.description'] = [document.description]
        map['okg:customProperties']['okp:customProperties.languages'] = [self.get_language(document)]

        map['okg:salesProperties']['okp:salesProperties.assetType'] = [self.get_asset_type(document)]

        map['okg:gsaProperties']['okp:gsaProperties.gsaPublishedStatus'] = [self.get_published_status(document)]
        map['okg:gsaProperties']['okp:gsaProperties.startDate'] = [document.okm_date_string(document.publish)]
        map['okg:gsaProperties']['okp:gsaProperties.expirationDate'] = [document.okm_date_string(document.expire)]
        return map

    def get_language(self, document):
        if not hasattr(document, 'language') or not hasattr(document.language, 'language') or document.language.language in ('ro', 'hr') or not document.language:
            return 'en'
        else:
            return document.language.language

    def get_asset_type(self, document):
        if document.type:
            parts = document.type.name.split()
            parts[0] = parts[0].lower()
            return ''.join(parts)
        else:
            return ''

    def get_published_status(self, document):
        published_status = 'Not Published'
        if document.is_published:
            published_status = 'Published'
        return published_status

    def populate_property_group(self, properties_dict):
        """
        :param properties_dict dict
        A dict with property group names as keys, the value for each property group
        should be a dict containing its properties and values
        {'property group name':
            { property name : values, ... }
        :returns a list groupProperties objects each populated with property names and values
        """
        property_groups = []
        for property_group in properties_dict:
            document = client.Document()
            property_group_obj = document.create_group_properties_object()
            property_group_obj.groupName = property_group
            for property_name, value in properties_dict[property_group].items():
                property_obj = document.create_group_property_object()
                property_obj.name = property_name
                property_obj.values = [value]
                property_group_obj.properties.append(property_obj)
            property_groups.append(property_group_obj)

        return property_groups

    def django_to_openkm_improved(self, document):
        map = settings.OPENKM['properties']
        properties_dict = self.prepare_properties_dict(map, document)
        return self.populate_property_group(properties_dict)

    def openkm_to_django(self, document):
        self.PROPERTY_GROUP_MAP = settings.OPENKM['properties']
        document_property_groups = self.property.get_property_groups_for_document(document.okm_path)

        if document_property_groups:
            for property_group in document_property_groups[0]:
                if hasattr(property_group, 'name') and property_group.name != 'okg:gsaProperties':
                    document_properties = self.property.get_document_properties_for_group(document.okm_path, property_group.name)
                    try:
                        property_map = self.PROPERTY_GROUP_MAP[property_group.name]
                        document = self.set_attributes(property_map, document_properties[0], document)
                    except KeyError, e:
                        print e
            document.save()

    def set_attributes(self, property_map, document_properties, document):
        for document_property in document_properties:
            if hasattr(document_property, 'name') and 'okp:gsaProperties' not in document_property.name:
                if property_map.get(document_property.name, None):
                    meta = property_map.get(document_property.name, None)
                    if 'choices' in meta:
                        option = self.get_option(document_property.options)
                        if option and meta['choices']:
                            value = utils.find_key(dict(meta['choices']), option.label)
                            setattr(document, meta['attribute'], value)
                        elif option and not meta['choices']:
                            if meta['attribute'] == 'type':
                                setattr(document.type, 'name', option.value)
                            else:
                                # sorry this is a horrible special case
                                # will come back and refactor this out soon
                                if meta['attribute'] == 'languages':
                                    try:
                                        self.set_language(document, option)
                                    except Exception, e:
                                        print e
                                else:
                                    setattr(document, meta['attribute'], option.value)
                    else:
                        setattr(document, meta['attribute'], document_property.value)
        return document

    def set_language(self, document, option):
        language_model_class = document.get_related_model()
        document.language = language_model_class.objects.get(language=option.value)

    def get_option(self, options):
        for option in options:
            if option.selected:
                return option

    def populate_property_group_map(self, map, document):
        """
        Updates the settings dict with values.
        @todo this restricts the settings. abstract to more generic
        """
        map['okg:customProperties']['okp:customProperties.title'].update({'value': document.name})
        map['okg:customProperties']['okp:customProperties.description'].update({'value': document.description})

        # must set to english languages not supported in OpenKM
        if document.language.language in ('ro', 'hr') or not document.language:
            language = 'en'
        else:
            language = document.language.language
        map['okg:customProperties']['okp:customProperties.languages'].update({'value': language})


        parts = document.type.name.split()
        parts[0] = parts[0].lower()
        asset_type = ''.join(parts)
        map['okg:salesProperties']['okp:salesProperties.assetType'].update({'value': asset_type})

        # published status has two values that GSA should set
        gsaPublishedStatus = 'Not Published'
        if document.is_published:
            gsaPublishedStatus = 'Published'
        map['okg:gsaProperties']['okp:gsaProperties.gsaPublishedStatus'].update({'value': gsaPublishedStatus})
        map['okg:gsaProperties']['okp:gsaProperties.startDate'].update({'value': document.okm_date_string(document.publish)})
        map['okg:gsaProperties']['okp:gsaProperties.expirationDate'].update({'value': document.okm_date_string(document.expire)})
        return map


class SyncFolderList(object):
    """
    Local storage of OpenKM folder metadata
    @todo make this generic to pickup all the folders across OpenKM, not just
    categories
    """
    DIRECTORY_SEPARATOR = "/"

    def __init__(self):
        self.category = facades.Category()
        self.dir = facades.DirectoryListing()
        self.repository = client.Repository()

    def execute(self, klass):
        """
        :param klass: OpenKMFolderlist class object
        """
        klass.objects.all().delete()
        xpath_query = '/jcr:root/okm:categories//element(*)'
        search = facades.SearchManager()
        type = 'xpath'
        folders = search.by_statement(xpath_query, type)
        print('%s folders returned for query: %s' % (len(folders.item), xpath_query))
        self.save(folders, klass)
        print('%s folders now in local folder list' % klass.objects.count())

    def get_list_of_root_paths(self):
        return [self.category.get_category_root().path]

    def traverse_folders(self, paths):
        folders = []
        for path in paths:
            folders.extend(self.dir.traverse_folders(path))

        return folders

    def save(self, folders, klass):
        """
        Iterate over the returned
        """
        if hasattr(folders, 'item') and isinstance(folders.item, list):
            for folder in folders.item:
                if hasattr(folder, 'folder'):
                    folder = folder.folder
                    try:
                        cl = klass.objects.create(okm_uuid=folder.uuid)
                        cl.okm_author = folder.author
                        cl.okm_created = folder.created
                        cl.okm_has_childs = folder.hasChilds
                        cl.okm_path = folder.path
                        cl.okm_permissions = folder.permissions
                        cl.okm_subscribed = folder.subscribed
                        cl.save()
                    except UnicodeEncodeError, e:
                        logging.exception(e)
                    except Exception, e:
                        logging.exception(e)
                elif hasattr(folder, 'document'):
                    logging.error('This is a document, not a folder')


class SyncDocumentException(Exception):
    pass


class SyncDocument(object):
    """
    Syncs a document object to OpenKM
    @todo refactor this to strip out any functionality which should be elsewhere
    """
    def __init__(self):
        self.document = client.Document()
        self.document_manager = facades.DocumentManager()
        self.repository_manager = facades.RepositoryManager()
        self.sync_keywords = SyncKeywords()
        self.keyword = facades.Keyword()
        self.sync_categories = SyncCategories()
        self.category = facades.Category()
        self.upload_root = self.get_upload_root()
        self.property = facades.Property()

    def get_upload_root(self):
        return settings.OPENKM['configuration']['UploadRoot']


class DjangoToOpenKm(SyncDocument):

    def execute(self, document, folderlist_document_class, taxonomy=False):
        """
        Uploads a document to OpenKm
        :param document: a document object
        :param document_class: a class object.  This should be your Django model which extends the OpenKmDocument
        abstract base class
        """
        try:
            logger.debug(document)
            if not document.okm_uuid and document.file:
                if taxonomy:
                    taxonomy = self.build_taxonomy(document)
                okm_document = self.document_manager.create(document.file, taxonomy)
                document.set_model_fields(okm_document)
                document.save()
            self.keywords(document)
            self.categories(document, folderlist_document_class)
            self.properties(document)
        except Exception, e:
            logger.exception(e)

    def improved_execute(self, document, openkm_folderlist_class, taxonomy=False):
        CustomDjangoToOpenKM(asset=document).execute(openkm_folderlist_class, taxonomy=False)

    def _get_file_name(self, document):
        if not document.file:
            raise Exception('File is empty')
        return document.file.name.split('/')[-1:][0]

    def update_properties(self, document, document_class):
        """
        Uploads a document to OpenKm
        :param document: a document object
        :param document_class: a class object.  This should be your Django model which extends the OpenKmDocument
        abstract base class
        """
        sync_properties = SyncProperties()
        sync_properties.django_to_openkm(document)

    def build_taxonomy(self, document):
        """
        Dynamically builds a taxonomy for a document.
        Of the format:
        /region/year/team/
        """
        if not document.owner:
            region = 'Global'
            team = 'Default'
        else:
            try:
                user_profile = document.owner.get_profile()
                region = user_profile.region.name
                team = user_profile.team.name
            except Exception, e:
                print 'Team not found, assuming default', e
                region = 'Global'
                team = 'Default'
        year = str(document.created.year)
        taxonomy = [region, year, team]
        return taxonomy

    def keywords(self, document):
        """
        TAGS -> KEYWORDS
        Writes the tags to OpenKM as keywords and confirms that they have been added
        :returns boolean:  True on success, False on fail
        """
        tags = self.sync_keywords.get_tags_from_document(document)
#        logger.info("[GSA] Tags: %s", tags)
        self.sync_keywords.write_keywords_to_openkm_document(document.okm_path, tags)
        print("[GSA] Tags: %s", tags)
        return self.sync_keywords.confirm_keywords_written_to_openkm(document.okm_path, tags)

    def get_category_uuids(self, document, openkm_folderlist_class):
        category_uuids = []
        for related_model_class in settings.OPENKM['categories'].keys():
            # prepare the lists of AND and OR predicates for the query
            mapped_category_name = self.category_map(related_model_class.__name__)
            if not mapped_category_name:
                print 'Category not found'
                continue
            and_predicates = ['categories', mapped_category_name]
            fields = self.sync_categories.get_objects_from_m2m_model(document, related_model_class)
            or_predicates = [field.__unicode__() for field in fields]

            # @todo convert '/' chars to '--' in and_predicates and or_predicate lists

            # get the category UUIDs
            category_uuids += openkm_folderlist_class.objects.custom_path_query(and_predicates, or_predicates)
        return category_uuids

    def get_categories(self, document, openkm_folderlist_class):
        """
        Returns a queryset of the OpenKMFolderlist objects that match the categories of the document,
        where the mapping comes from OPENKM settings dict
        """
        categories = []
        for related_model_class in settings.OPENKM['categories'].keys():
            # prepare the lists of AND and OR predicates for the query
            mapped_category_name = self.category_map(related_model_class.__name__)
            if not mapped_category_name:
                print 'Category not found'
                continue
            and_predicates = ['categories', mapped_category_name]
            fields = self.sync_categories.get_objects_from_m2m_model(document, related_model_class)
            or_predicates = [field.__unicode__() for field in fields]

            # @todo convert '/' chars to '--' in and_predicates and or_predicate lists

            # get the category UUIDs
            categories += openkm_folderlist_class.objects.get_custom_queryset(and_predicates, or_predicates)
        return categories

    def categories(self, document, openkm_folderlist_class, update_individually=True):
        """
        Using the MODEL_CATEGORY_MAP gets all the associated objects for each m2m relationship and adds
        them as categories to the given document on OpenKM
        :param document_class: a class object.  This should be your Django model which extends the OpenKmDocument
        abstract base class
        """
        category_uuids = self.get_category_uuids(document, openkm_folderlist_class)

        if update_individually:
            # add the categories to the document
            for category_uuid in category_uuids:
                logger.info("Adding category [%s] to %s" % (category_uuid, document.okm_path))
                self.category.add_to_node(document.okm_path, category_uuid)


    def properties(self, document):
        sync_properties = SyncProperties()
        sync_properties.django_to_openkm(document)

    map = {
        'Industry': 'Industries',
        'Region': 'Region',
        'Role': 'Roles',
        'Solution': 'Solutions',
        'Task': 'Tasks',
        'Product': 'Products'
    }

    def category_map(self, model_class_name):
        try:
            return self.map[model_class_name]
        except KeyError:
            print model_class_name, ' not found'
            return False


class CustomDjangoToOpenKM(DjangoToOpenKm):
    """
    Calls methods from a customised non-standard version of OpenKM
    DO NOT USE these methods if you are using a standard OpenKM instance
    """
    def __init__(self, asset, *args, **kwargs):
        """
        :param asset: Django model object instance that inherits from OpenKMDocument
        """
        self.asset = asset
        self.document_client = client.Document()
        super(CustomDjangoToOpenKM, self).__init__(*args, **kwargs)

    def get_data(self):
        return self.document_client.create_document_data_object()

    def build_path(self, taxonomy=None):
        """Returns a string of the path for the given asset"""
        filename = self._get_file_name(self.asset)
        base_path = settings.OPENKM['configuration']['UploadRoot']
        if taxonomy:
            base_path += self._get_taxonomy(taxonomy)
        return self._get_path(base_path, filename)

    def _get_path(self, base_path, filename):
        return '%s%s' % (base_path, filename)

    def _get_taxonomy(self, taxonomy):
        """This simple builds the path string.  To Dynamically build the folder on OpenKM then
        see openkm.facades.Taxonomy
        :param taxonomy: a list of strings eg. ['one', 'two'] returns 'one/two/'
        """
        return '/'.join(taxonomy) + '/'


    def add_categories(self, openkm_folderlist_class):
        categories = []
        categories = self.get_categories(self.asset, openkm_folderlist_class)
        if self.asset.is_linked_asset():
            source_path = self.asset.get_dms_source_path()
            categories += openkm_folderlist_class.objects.filter(okm_path=source_path)
        return [self.document_client.create_category_folder_object(c.okm_path) for c in categories]

    def add_properties(self):
        sync_properties = SyncProperties()
        return sync_properties.django_to_openkm_improved(self.asset)

    def create(self, data):
        content = facades.DocumentManager().convert_file_content_to_binary_for_transport(self.asset.file)
        okm_document = self.document_client.create_document(content, data)
        return okm_document

    def update(self, data):
        return self.document_client.update_document(data)

    def get_or_create(self, data):
        okm_document = self.update(data) if self.asset.okm_uuid else self.create(data)
        if okm_document:
            self.asset.set_model_fields(okm_document)
            self.asset.save()

    def execute(self, folderlist_document_class, taxonomy=None):
        """
        Uploads a document in a single web service call.
        Important -- This relies on a modified OpenKM instance, use
        execute() if you are using standard OpenKM
        """
        data = self.get_data()
        data.document.path = self.build_path(taxonomy=taxonomy)
        print data.document.path
        data.document.keywords = self.asset.tags.split(',')
        data.document.categories = self.add_categories(folderlist_document_class)
        data.properties = self.add_properties()
        self.get_or_create(data)


class OpenKmToDjango(SyncDocument):

    def execute(self, document, okm_document):
        '''
        :param document: A Django model object instance of your Document object
        :param okm_document: An OKM Document object as returned by a webservice
        '''
        self.keywords(document, okm_document)
        self.properties(document)
        self.categories(document, okm_document)

    def keywords(self, document, okm_document):
        '''
        :param document: a Django model instance for your document
        :param okm_document: an OpenKM Document instance
        '''
        if hasattr(okm_document, 'keywords') and okm_document.keywords:
            print 'DMS Keywords: %s' % okm_document.keywords
            keywords = utils.remove_none_elements_from_list(okm_document.keywords)
            document.tags = ', '.join(keywords)
        else:
            document.tags = ''
        document.save()
        print 'GSA tags: %s' % document.tags


    def categories(self, document, okm_document):
        '''
        :param document: a Django model instance for your document
        :param okm_document: an OpenKM Document instance
        '''
        category_bin = {}

        # add the categories from OpenKM to the dict
        if hasattr(okm_document, 'categories'):
            for category in okm_document.categories:
                try:
                    category_name, object_name = utils.get_category_from_path(category.path) # find the category

                    # use the map to translate the OKM category name to the Django model name
                    sync_categories = SyncCategories()
                    model_name = utils.find_key(sync_categories.map, category_name)

                    category_bin = self.add_category_to_dict(model_name, object_name, category_bin)
                except ValueError, e:
                    logger.exception(e)

            print 'Category bin: ', category_bin

            for related_class, values in category_bin.items():
                try:
                    # get the related manager for the class
                    _set = getattr(document, "%s" % related_class.__name__.lower()) # get the m2m manager
                    _set.clear() # remove the current objects

                    # special case for Tasks. this would be better as one to one, but need to maps to the unicode val
                    if related_class.__name__ == 'Task':
                        values = [self.sanitize_task_description(value) for value in values]

                    # get the objects and add them to the model
                    objects = [related_class.objects.get(name__contains=value) for value in values]
                    [_set.add(object) for object in objects]
                except AttributeError, e:
                    print e
                    logger.exception(e)
                except Exception, e:
                    print e
                    logger.exception(e)


    def sanitize_task_description(self, task):
        p = re.compile('\[\w{0,4}\] [\d.: ]{0,9}')
        return p.sub('',task)

    def add_category_to_dict(self, category_name, object_name, category_bin):
        """
        { related class to the document : list of values }
        e.g. { Region: ['EMEA', 'Latin America'] }
        :category_name string
        :object_name string
        :param category_bin: dict
        :return dict
        """
        related_class = utils.find_key(settings.OPENKM['categories'], category_name) # get the related class to document

        if not related_class:
            logger.error('%s not found in OPENKM[\'categories\']', category_name)
            return category_bin

        if related_class not in category_bin:
            category_bin.update({related_class: [object_name]})
        else:
            category_bin[related_class].append(object_name)
        return category_bin

    def properties(self, document):
        sync_properties = SyncProperties()
        sync_properties.openkm_to_django(document)
