from suds import WebFault
from django.conf import settings

from .client import Auth, Document, Property, PropertyGroup, Repository
from .facades import Category, Keyword, DirectoryListing
from .models import OpenKmFolderList
from .utils import find_key

class SyncPropertiesException(Exception):
    pass

class SyncProperties(object):

    PROPERTY_GROUP = 'okg:customProperties'

    # django model attributes -> openkm properties
    MODEL_PROPERTY_MAP = {
        'name': 'Title',
        'description': 'Description',
        }

    def __init__(self):
        auth = Auth()
        auth.login()
        self.property_group = PropertyGroup()

    def document_has_property_group(self, document, group_name):
        return self.property_group.has_group(document.path, group_name)

    def update_properties(self, resource, properties):
        for property in properties.item:
            if property.label in self.MODEL_PROPERTY_MAP.values():
                django_attr = find_key(self.MODEL_PROPERTY_MAP, property.label)
                property.value = resource.__getattribute__(django_attr)
        return properties

    def update_django_model_attributes(self, model, properties):
        for property in properties.item:
            if property.label in self.MODEL_PROPERTY_MAP.values():
                model_attribute_name = find_key(self.MODEL_PROPERTY_MAP, property.label)
                setattr(model, model_attribute_name, property.value)
        return model.save()

    def django_to_openkm(self, resource, document):
        # if document has the group, then grab the properties and remove it, as
        # we need to re-add it if we want to modify it
        if self.document_has_property_group(document, self.PROPERTY_GROUP):
            properties = self.property_group.get_properties(document.path, self.PROPERTY_GROUP)
            self.property_group.remove_group(document.path, self.PROPERTY_GROUP)

        self.property_group.add_group(document.path, self.PROPERTY_GROUP)

        if not properties:
            properties = self.property_group.get_properties(document.path, self.PROPERTY_GROUP)

        updated_properties = self.update_properties(resource, properties)
        self.property_group.set_properties(document.path, self.PROPERTY_GROUP, updated_properties)

    def openkm_to_django(self, resource, document):
        if not self.document_has_property_group(document, self.PROPERTY_GROUP):
            raise SyncPropertiesException('OpenKM document does not have %s' % self.PROPERTY_GROUP)
        properties = self.property_group.get_properties(document.path, self.PROPERTY_GROUP)



class SyncKeywords(object):

    def __init__(self):
        self.keyword = Keyword()

    def get_tags_from_resource(self, resource):
        """
        Returns an object's tags as a list
        """
        return resource.tag_set.split(',')

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
        Writes the tags from a GSA resource to a Helix document as keywords
        Assumes that the document exists on OpenKM
        :param document: Document model object
        :param openkm_document: OpenKM document object
        """
        tags = self.get_tags_from_resource(document)
        self.write_keywords_to_openkm_document(openkm_document.path, tags)

    def single_document_helix_to_django(self, document, openkm_document):
        """
        Updates the tags on a Django model from the keywords on OpenKM
        :param document: Resource model object
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
        self.category = Category()

    def create_top_level_categories(self, parent_path=False):
        """
        Creates the top level categories, as first level children of the parent_path
        :param parent_path: (string) defaults to category root
        """
        if not parent_path:
            parent_path = self.category.get_category_root().path

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
        """
        objects = model_class.objects.all()

        for object in objects:
            try:
                self.category.create('/okm:categories/%s/%s' % (category_name,\
                                                                object.__unicode__().replace('/','')))
            except:
                logger.info("%s creation failed" % object.__unicode__().replace('/',''))

    def openkm_to_django(self):
        pass

    def get_many_to_many_fields_from_model(self, document, related_model_class):
        """
        Accepts a Document and a single class object of a many-to-many field
        :returns queryset the related model objects associated with the given resource
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
        - is accessible from the resource via modelname_set()
        For example if called with a resource and the string region
        it will return the regions associated with this resource
        """
        method_name = '%s_set' % related_model_name
        if hasattr(document, method_name):
            _member = getattr(document, method_name)
            return _member.all()
        else:
            logger.error("Object does not have method region_set")


class SyncResourceException(Exception):
    pass

class SyncResource(object):
    """
    Syncs a Resource object to OpenKM
    """
    def __init__(self, document):
        if not isinstance(document, Document):
            raise SyncResourceException('Must pass a Resource instance to be synced')
        self.auth = Auth()
        self.auth.login()
        self.document = Document()
        self.repository = Repository()
        self.document = document
        self.sync_keywords = SyncKeywords()
        self.sync_categories = SyncCategories()

    def new_openkm_document_object(self):
        """ Returns a local object instance """
        return self.document.new()

    def document_exists_on_openkm(self, path):
        return self.repository.has_node(path)

    def build_openkm_path(self, base_path, file_name):
        return "%s%s" % (base_path, file_name)

    def upload_to_openkm(self, file):
        """
        Uploads the document to the OpenKM server
        :param file: a file object
        """
        path = self.build_openkm_path(settings.OPENKM['UploadRoot'], file.name)
        openkm_document = self.new_openkm_document_object()
        openkm_document.path = settings.OPENKM['UploadRoot'] + file.name
        content = utils.make_file_java_byte_array_compatible(file)

        try:
            return self.document.create(openkm_document, content)
        except Exception, e:
            logger.error("There was a problem uploading the document: %s" % file.name)

    def keywords(self):
        """
        TAGS -> KEYWORDS
        Writes the tags to OpenKM as keywords and confirms that they have been added
        :returns boolean:  True on success, False on fail
        """
        tags = self.sync_keywords.get_tags_from_resource(self.document)
        self.sync_keywords.write_keywords_to_openkm_document(self.path, tags)
        return self.sync_keywords.confirm_keywords_written_to_openkm(self.path, tags)

    def categories(self):
        for related_model_class in self.sync_categories.MODEL_CATEGORY_MAP.keys():
            self.sync_categories.get_many_to_many_fields_from_model(self.document, related_model_class)

    def properties(self):
        pass

    def file(self):
        pass


class SyncFolderList(object):
    """
    Local storage of OpenKM folder metadata
    @todo make this generic to pickup all the folders across OpenKM, not just
    categories
    """
    def __init__(self):
        self.category = Category()
        self.dir = DirectoryListing()
        self.repository = Repository()

    def execute(self):
        paths = self.get_list_of_root_paths()
        folders = self.traverse_folders(paths)
        self.save(folders)

    def get_list_of_root_paths(self):
        return [self.category.get_category_root().path, self.repository.get_root_folder().path]

    def traverse_folders(self, paths):
        folders = []
        for path in paths:
            folders.extend(self.dir.traverse_folders(path))

        return folders

    def save(self, folders):
        for folder in folders:
            try:
                cl, created = OpenKmFolderList.objects.get_or_create(uuid=folder.uuid)
                cl.author = folder.author
                cl.created = folder.created
                cl.has_childs = folder.hasChilds
                cl.path = folder.path
                cl.permissions = folder.permissions
                cl.subscribed = folder.subscribed
                cl.save()
            except Exception, e:
                logger.error(e)
