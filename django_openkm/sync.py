import logging

from django.conf import settings

from suds import WebFault

from django_openkm import client, facades, utils


class SyncKeywords(object):

    def __init__(self):
        self.keyword = facades.Keyword()

    def get_tags_from_document(self, document):
        """
        Returns an object's tags as a list
        """
        return document.tag_set.split(',')

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

    def __init__(self):
        self.category = facades.Category()

    def create_top_level_categories(self, parent_path=False):
        """
        Creates the top level categories, as first level children of the parent_path
        :param parent_path: (string) defaults to category root
        """
        if not parent_path:
            parent_path = self.category.get_category_root().path
        logging.info("parent path: %s", parent_path)

        for category_name in self.MODEL_CATEGORY_MAP.values():
            path = self.category.construct_valid_path_string(parent_path, category_name)
            try:
                self.category.create(path)
                logging.info("%s created" % path)
            except:
                logging.info("%s creation failed" % path)

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
                logging.info("%s creation failed" % object.__unicode__().replace('/',''))

    def get_objects_from_m2m_model(self, document, related_model_class):
        """
        Accepts a Document and a single class object of a many-to-many field
        :returns queryset the related model objects associated with the given document
        """
        method_name = '%s_set' % related_model_class.__name__.lower()
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
        method_name = '%s_set' % related_model_name
        if hasattr(document, method_name):
            _member = getattr(document, method_name)
            return _member.all()
        else:
            logging.error("Object does not have method %s" % method_name)


class SyncProperties(object):

    def __init__(self):
        self.property = facades.Property()
        self.property_group = client.PropertyGroup()

    def django_to_openkm(self, document):
        self.PROPERTY_GROUP_MAP = self.populate_property_group_map(settings.OPENKM['properties'], document)

        for property_group in self.PROPERTY_GROUP_MAP:
            logging.debug("property_group: %s", property_group)
            if not self.property_group.has_group(document.okm_path, property_group):
                self.property_group.add_group(document.okm_path, property_group)

            properties = self.property_group.get_properties(document.okm_path, property_group)

            # update the properties values and set them on OpenKM
            updated_properties = self.property.update_document_properties(properties, self.PROPERTY_GROUP_MAP[property_group])
            self.property_group.add_group(document.okm_path, property_group)
            self.property_group.set_properties(document.okm_path, property_group, updated_properties)

    def openkm_to_django(self, document):
        self.PROPERTY_GROUP_MAP = settings.OPENKM['properties']
        document_property_groups = self.property.get_property_groups_for_document(document.okm_path)

        for property_group in document_property_groups[0]:
            document_properties = self.property.get_document_properties_for_group(document.okm_path, property_group.name)
            try:
                property_map = self.PROPERTY_GROUP_MAP[property_group.name]
                self.set_attributes(property_map, document_properties[0], document)
            except KeyError, e:
                logging.error('Property group not found: %s', property_group.name)

    def set_attributes(self, property_map, document_properties, document):
        for document_property in document_properties:
            if property_map.get(document_property.name, None):
                logging.info('Found property: %s', document_property.name)
                meta = property_map.get(document_property.name, None)
                if 'choices' in meta:
                    option = self.get_option(document_property.options)
                    if option and meta['choices']:
                        value = utils.find_key(dict(meta['choices']), option.label)
                        setattr(document, meta['attribute'], value)
                        logging.info('Updated %s : %s' % (meta['attribute'], option.label))
                    elif option and not meta['choices']:
                        setattr(document, meta['attribute'], option.value)
                        logging.info('Updated %s : %s' % (meta['attribute'], option.value))
                else:
                    setattr(document, meta['attribute'], document_property.value)
                    logging.info('Updated %s : %s' % (meta['attribute'], document_property.value))

        document.save()

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
        map['okg:customProperties']['okp:customProperties.languages'].update({'value': document.language})
        map['okg:salesProperties']['okp:salesProperties.assetType'].update({'value': document.get_type_display()})
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
        :param klass your django model class storing the OpenKM folder list
        """
        logging.info('Class: %s', klass)

        paths = self.get_list_of_root_paths()
        logging.info(paths)

        folders = self.traverse_folders(paths)
        logging.info(folders)

        self.save(folders, klass)

    def get_list_of_root_paths(self):
        return [self.category.get_category_root().path, self.repository.get_root_folder().path]

    def traverse_folders(self, paths):
        folders = []
        for path in paths:
            folders.extend(self.dir.traverse_folders(path))

        return folders

    def save(self, folders, klass):
        for folder in folders:
            logging.info(folder)
            try:
                cl, created = klass.objects.get_or_create(okm_uuid=folder.uuid)
                cl.okm_author = folder.author
                cl.okm_created = folder.created
                cl.okm_has_childs = folder.hasChilds
                cl.okm_path = folder.path
                cl.okm_permissions = folder.permissions
                cl.okm_subscribed = folder.subscribed
                cl.save()
            except Exception, e:
                print e

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

    def execute(self, document, document_class):
        """
        Uploads a document to OpenKm
        :param document: a document object
        :param document_class: a class object.  This should be your Django model which extends the OpenKmDocument
        abstract base class
        """
        try:
            if not document.okm_uuid and document.file:
                taxonomy = self.build_taxonomy(document)
                self.document_manager.create(document.file, taxonomy)
            self.keywords(document)
            self.categories(document, document_class)
            self.properties(document)
        except Exception, e:
            logging.exception(e)

    def build_taxonomy(self, document):
        user_profile = document.owner.get_profile()
        region = user_profile.region.name
        year = str(document.created.year)
        team = document.owner.team_member.all()[0].name
        taxonomy = [region, year, team]
        return taxonomy

    def keywords(self, document):
        """
        TAGS -> KEYWORDS
        Writes the tags to OpenKM as keywords and confirms that they have been added
        :returns boolean:  True on success, False on fail
        """
        tags = self.sync_keywords.get_tags_from_document(document)
        logging.info("[GSA] Tags: %s", tags)
        self.sync_keywords.write_keywords_to_openkm_document(document.okm_path, tags)
        return self.sync_keywords.confirm_keywords_written_to_openkm(document.okm_path, tags)

    def categories(self, document, openkm_folderlist_class):
        """
        Using the MODEL_CATEGORY_MAP gets all the associated objects for each m2m relationship and adds
        them as categories to the given document on OpenKM
        :param document_class: a class object.  This should be your Django model which extends the OpenKmDocument
        abstract base class
        """
        for related_model_class in settings.OPENKM['categories'].keys():

            # prepare the lists of AND and OR predicates for the query
            and_predicates = ['categories', related_model_class.__name__]
            fields = self.sync_categories.get_objects_from_m2m_model(document, related_model_class)
            or_predicates = [field.__unicode__() for field in fields]

            # @todo convert '/' chars to '--' in and_predicates and or_predicate lists

            logging.info("and_predicates: %s", and_predicates)
            logging.info("or_predicates: %s", or_predicates)

            # get the category UUIDs
            category_uuids = openkm_folderlist_class.objects.custom_path_query(and_predicates, or_predicates)
            logging.info("category_uuids: %s", category_uuids)

            # add the categories to the document
            for category_uuid in category_uuids:
                logging.info("Adding category [%s] to %s" % (category_uuid, document.okm_path))
                self.category.add_to_node(document.okm_path, category_uuid)

    def properties(self, document):
        sync_properties = SyncProperties()
        sync_properties.django_to_openkm(document)



class OpenKmToDjango(SyncDocument):

    def execute(self, document):
        self.keywords(document)
        self.properties(document)
        self.categories(document)

    def keywords(self, document):
        keywords = self.keyword.get_for_document(document.okm_path)
        logging.info('[%s] OpenKM keywords: %s' % (document, keywords))
        document.update_tags(','.join(keywords))
        logging.info('[%s] document tags updated.  Now: %s' % (document, keywords))

    def categories(self, document):
        category_bin = {}
        okm_document_properties = self.document.get_properties(document.okm_path)

        # add the categories from OpenKM to the dict
        for category in okm_document_properties.categories:
            category_name, object_name = utils.get_category_from_path(category.path) # find the category
            category_bin = self.add_category_to_dict(category_name, object_name, category_bin)

        for related_class, values in category_bin.items():
            try:
                # get the related manager for the class
                _set = getattr(document, "%s_set" % related_class.__name__.lower()) # get the m2m manager
                _set.clear() # remove the current objects

                # special case for Tasks. this would be better as one to one, but need to maps to the unicode val
                if related_class.__name__ == 'Task':
                    values = [self.sanitize_task_description(value) for value in values]

                # get the objects and add them to the model
                objects = [related_class.objects.get(name__icontains=value) for value in values]
                logging.info('Adding the following categories: %s', objects)
                [_set.add(object) for object in objects]
            except AttributeError, e:
                logging.exception(e)


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
            logging.error('%s not found in OPENKM[\'categories\']', category_name)
            return category_bin

        if related_class not in category_bin:
            category_bin.update({related_class: [object_name]})
        else:
            category_bin[related_class].append(object_name)
        return category_bin

    def properties(self, document):
        sync_properties = SyncProperties()
        sync_properties.openkm_to_django(document)