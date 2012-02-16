import logging

from django.conf import settings

import client, utils


class Session(object):

    def __init__(self):
        self.auth = client.Auth()

    def open(self):
        self.auth.login()
        return self.auth.token

    def close(self):
        self.auth.logout()

class Category(object):

    def __init__(self):
        self.folder = client.Folder()
        self.repository = client.Repository()
        self.property = client.Property()

    def add_to_node(self, node_path, category_uuid):
        self.property.add_category(node_path, category_uuid)

    def remove_from_node(self, node_path, category_uuid):
        self.property.remove_category(node_path, category_uuid)

    def create(self, new_category_path):
        """ Creates a new category """
        new_category = self.folder.new()
        new_category.path = new_category_path
        return self.folder.create(new_category)

    def remove(self, path):
        """ Removes an existing category """
        return self.folder.delete(path)

    def get_category_root(self):
        """
        :return folder object
        """
        return self.repository.get_categories_folder()

    def get_child_categories(self, path):
        """ Returns the child categories for a given parent folder """
        return self.folder.get_children(path)

    def construct_valid_path_string(self, base_path, new_category_name):
        """
        Utility function to construct a category path from a path
        as returned by OpenKM and a string specifying a new category name
        :base_path string
        :new_category_name string
        :return string
        """
        return "%s/%s" % (base_path, new_category_name)


class Keyword(object):

    def __init__(self):
        self.property = client.Property()
        self.document = client.Document()

    def add(self, path, keyword):
        return self.property.add_keyword(path, keyword)

    def remove(self, path, keyword):
        return self.property.remove_keyword(path, keyword)

    def get_for_document(self, path):
        """
        Returns a list of keywords
        :param path: OpenKM node path of document
        """
        document = self.document.get_properties(path)
        return document.keywords


class FileSystem(object):
    """
    File system related functionality
    """
    DISALLOWED_CHAR_MAP = (
        ('/', '--'),
    )

    def get_node_from_path(self, path):
        """ Returns the file name or folder name from a given path """
        return path.split("/")[-1]

    def names_as_list(self, collection):
        """ Generic utility function """
        names = []
        for child in collection.item:
            category_name = self.get_node_from_path(child.path)
            names.append(category_name)

        return names

    def folder_names_as_list(self, collection_of_child_folders):
        return self.names_as_list(collection_of_child_folders)

    def file_names_as_list(self, collection_of_child_documents):
        return self.names_as_list(collection_of_child_documents)

    def get_file_name_from_path(self, path):
        return path.split('/').pop()

    def normalise_string_for_openkm(self, str):
        """
        Replaces non-allowed characters in path names with substitues so that they will be compatible with OpenKM
        """
        for map in self.DISALLOWED_CHAR_MAP:
            str = str.replace(map[0],map[1])
        return str

    def denormalise_openkm_string(self, path):
        """
        Replaces the substitute chars added to path names in self.normalise_django_path() so that they map back to
        Django fields
        """
        for map in self.DISALLOWED_CHAR_MAP:
            path = path.replace(map[1],map[0])
        return path

class FolderManager(client.Folder):

    def __init__(self):
        super(FolderManager, self).__init__(class_name='Folder')

    def create(self, folder_obj):
        folder_obj.path = utils.remove_trailing_slash(folder_obj.path)
        super(FolderManager, self).create(folder_obj)

class DirectoryListing(object):

    documents = []
    folders = []

    def __init__(self):
        self.doc = client.Document()
        self.folder = client.Folder()

    def get_root_path(self):
        return settings.OPENKM['configuration']['UploadRoot']

    def traverse(self, path=None):
        """
        Traverse files and folders
        Returns a list of document objects
        """

        if path is None:
            path = self.get_root_path()

        # get files and add them to the file list
        results = self.doc.get_children(path)

        try:
            for result in results[0]:
                self.documents.append(result)
        except:
            pass

        # get child folders of the path given as param
        folders = self.folder.get_children(path)

        # if there are child folders, traverse them recursively
        try:
            if isinstance(folders[0], list) and len(folders[0]) > 0:
                for folder in folders[0]:
                    self.traverse(path=folder.path)
        except:
            pass

        return self.documents

    def traverse_folders(self, path):
        folders_temp = self.folder.get_children(path)

        # if there are child folders, traverse them recursively
        try:
            if isinstance(folders_temp[0], list) and len(folders_temp[0]) > 0:
                for folder in folders_temp[0]:
                    self.folders.append(folder)
                    self.traverse_folders(path=folder.path)
        except:
            pass
        return self.folders

    def get_all_documents_in_folder(self, folder_path=settings.OPENKM['configuration']['UploadRoot']):
        return self.doc.get_children(folder_path)


class DocumentManager(object):

    def __init__(self):
        self.document = client.Document()

    def create(self, file_obj, taxonomy=[]):
        document = self.document.new()

        if taxonomy:
            # build the taxonomy
            tax = Taxonomy(taxonomy)
            document.path = tax.generate_path(taxonomy) + file_obj.name.split('/')[-1]
        else:
            # just create the path
            document.path = self.create_path_from_filename(file_obj)

        content = self.convert_file_content_to_binary_for_transport(file_obj)
        return self.create_document_on_openkm(document, content)

    def create_path_from_filename(self, file_obj):
        file_system = FileSystem()
        filename = file_system.get_file_name_from_path(file_obj.__str__())
        logging.debug("Derived filename: %s", filename)
        return "%s%s" % (settings.OPENKM['configuration']['UploadRoot'], filename)

    def convert_file_content_to_binary_for_transport(self, file_obj):
        return utils.make_file_java_byte_array_compatible(file_obj)

    def create_document_on_openkm(self, document, content):
        return self.document.create(document, content)

    def get_path(self, uuid):
        return self.document.get_path(uuid)

    def get_properties(self, doc_path):
        return self.document.get_properties(doc_path)

class RepositoryManager(client.Repository):

    def __init__(self):
        super(RepositoryManager, self).__init__(class_name='Repository')

class Property(object):

    def __init__(self):
        self.property_group = client.PropertyGroup()

    def get_property_groups_for_document(self, doc_path):
        return self.property_group.get_groups(doc_path)

    def get_document_properties_for_group(self, doc_path, group_name):
        return self.property_group.get_properties(doc_path, group_name)

    def update_document_properties(self, properties, new_values):
        """
        :param properties: formElementComplexArray as returned by SUDs
        :new_values: dictionary of the form { label : value }
        """
        for property in properties[0]:
            if hasattr(property, 'label') and property.name in new_values.keys():
                logging.info('Found %s to %s' % (property.name, new_values[property.name]))
                if hasattr(property, 'options'):
                    try:
                        property.options = self.update_options_list(property.options, new_values[property.name]['value'])
                    except KeyError, e:
                        logging.exception(e)
                else:
                    logging.info('Updating %s to %s' % (property.name, new_values[property.name]))
                    property.value = new_values[property.name]['value']

        return properties

    def update_options_list(self, options, new_value):
       for option in options:
           if option.label == new_value:
               option.selected = True
               logging.info('Updating option[%s].selected to True', option.label)
           else:
               option.selected = False

       return options

    def update_document_on_openkm(self, node_path, group_name, properties):
        self.property_group.remove_group(node_path, group_name)
        return self.property_group.set_properties(node_path, group_name, properties)



class SearchManager(client.Search):
    def __init__(self):
        super(SearchManager, self).__init__(class_name='Search')


class Taxonomy(object):
    """
    Creates a directory structure for the given Taxonomy

        /okm:root/Uploads/[region]/[year]/Team/

    """
    def __init__(self, folders=[]):
        # Remove the leading forward slash if present
        self.root_path = utils.remove_trailing_slash(settings.OPENKM['configuration']['UploadRoot'])
        self.repository = RepositoryManager()
        self.folder = FolderManager()
        if folders:
            dependencies = self.generate_path_dependencies(folders)
            self.build_path(dependencies)

    def generate_path(self, folders=None):
        """
        Builds string representing a folder path using the UploadRoot as the base path
        Example:
        folders =  ['EMEA', '2012', 'Team']
        returns '/okm:root/Uploads/EMEA/2012/Team/'
        :param folders: a list or tuple of strings, each element being a subfolder of upload root
        :returns path: string
        """
        path = [self.root_path]

        if isinstance(folders, list):
            for folder in folders:
                path.append(folder)
            return '/'.join(path) + '/'
        else:
            return self.root_path + '/' + folders + '/'


    def generate_path_dependencies(self, folders):
        """
        :returns a list of strings.  each string being a dependency for a path

            ['/okm:root/Uploads',
             '/okm:root/Uploads/EMEA',
             '/okm:root/Uploads/EMEA/2012',
             '/okm:root/Uploads/EMEA/2012/General']
        """
        if not isinstance(folders, list):
            raise Exception('folders param must be a list')

        dependencies = []

        i = 0
        while i <= len(folders):
            if i == 0:
                # first iteration so generate the full path
                dependencies.append(self.generate_path(folders))
            else:
                # generate path[n - 1] each iteration
                dependencies.append(self.generate_path(folders[:-i]))
            i = i + 1

        return dependencies

    def build_path(self, dependencies):
        """
        :param dependencies: list. a list of folder paths which must exist.  If the folders do not
        exist, they will be created
        :returns boolean: True when path has been created
        """
        if self.repository.has_node(dependencies[0]):
            return True

        folders_to_create = [dependency for dependency in dependencies if not self.repository.has_node(dependency)]
        folders_to_create.reverse()

        for path in folders_to_create:
            okm_folder = self.folder.new()
            okm_folder.path = path
            self.folder.create(okm_folder)
            logging.info('Created folder path: %s', path)