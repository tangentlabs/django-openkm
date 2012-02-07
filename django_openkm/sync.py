import logging

from suds import WebFault
from django.conf import settings

from django_openkm import utils
from .client import PropertyGroup, Repository
from .facades import Category, Keyword, DirectoryListing, Property
from .utils import find_key

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
                                                                object.__unicode__().replace('/','')))
            except:
                logging.info("%s creation failed" % object.__unicode__().replace('/',''))

    def openkm_to_django(self, resource):
        from django_openkm import facades
        #facades.Category
        pass

    def get_objects_from_m2m_model(self, document, related_model_class):
        """
        Accepts a Document and a single class object of a many-to-many field
        :returns queryset the related model objects associated with the given resource
        """
        method_name = '%s_set' % related_model_class.__name__.lower()
        _set = getattr(document, method_name)

#        import ipdb; ipdb.set_trace()

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
            logging.error("Object does not have method %s" % method_name)


class SyncProperties(object):

    def __init__(self):
        self.property = Property()
        self.property_group = PropertyGroup()

    def django_to_openkm(self, resource):
        self.PROPERTY_GROUP_MAP = self.populate_property_group_map(resource)
        logging.info(self.PROPERTY_GROUP_MAP)

        for property_group in self.PROPERTY_GROUP_MAP:
            logging.debug("property_group: %s", property_group)
            if not self.property_group.has_group(resource.okm_path, property_group):
                self.property_group.add_group(resource.okm_path, property_group)

            properties = self.property_group.get_properties(resource.okm_path, property_group)

            # update the properties values and set them on OpenKM
            updated_properties = self.property.update_document_properties(properties, self.PROPERTY_GROUP_MAP[property_group])
            self.property_group.add_group(resource.okm_path, property_group)
            self.property_group.set_properties(resource.okm_path, property_group, updated_properties)

    def openkm_to_django(self, resource):
        self.PROPERTY_GROUP_MAP = settings.OPENKM['properties']

        document_property_groups = self.property.get_property_groups_for_document(resource.okm_path)

        for property_group in document_property_groups[0]:
            document_properties = self.property.get_document_properties_for_group(resource.okm_path, property_group.name)
            property_map = self.PROPERTY_GROUP_MAP[property_group.name]
            self.set_attributes(property_map, document_properties[0], resource)

    def set_attributes(self, property_map, document_properties, resource):
        for document_property in document_properties:
            if property_map.get(document_property.name, None):
                logging.info('Found property: %s', document_property.name)
                meta = property_map.get(document_property.name, None)
                if 'choices' in meta:
                    option = self.get_option(document_property.options)
                    if option and meta['choices']:
                        value = utils.find_key(dict(meta['choices']), option.label)
                        setattr(resource, meta['attribute'], value)
                        logging.info('Updated %s : %s' % (meta['attribute'], option.label))
                    elif option and not meta['choices']:
                        setattr(resource, meta['attribute'], option.value)
                        logging.info('Updated %s : %s' % (meta['attribute'], option.value))
                else:
                    setattr(resource, meta['attribute'], document_property.value)
                    logging.info('Updated %s : %s' % (meta['attribute'], document_property.value))

        resource.save()

    def get_option(self, options):
        for option in options:
            if option.selected:
                return option

    """
    @todo The two functions below violate the DRY principle and need to be merged into a single dictionary
    """
    def populate_property_group_map(self, resource):
        return {
            "okg:customProperties": {
                "okp:customProperties.title": resource.name,
                'okp:customProperties.description': resource.description,
                'okp:customProperties.languages': resource.language,
                },
            "okg:salesProperties": {
                'okp:salesProperties.assetType': resource.get_type_display(),
                }
        }

    def reverse_mapping(self):
        return {
            "okg:customProperties": {
                "okp:customProperties.title": 'name',
                'okp:customProperties.description': 'description',
                'okp:customProperties.languages': ('language', None)
                },
            "okg:salesProperties": {
                'okp:salesProperties.assetType': ('type', RESOURCE_TYPES),
                }
        }


class SyncFolderList(object):
    """
    Local storage of OpenKM folder metadata
    @todo make this generic to pickup all the folders across OpenKM, not just
    categories
    """
    DIRECTORY_SEPARATOR = "/"

    def __init__(self):
        self.category = Category()
        self.dir = DirectoryListing()
        self.repository = Repository()

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

