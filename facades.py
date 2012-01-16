from django.conf import settings

from .client import Auth, Document, Folder, Repository, Property
from .utils import make_file_java_byte_array_compatible

class Session(object):

    def __init__(self):
        self.auth = Auth()

    def open(self):
        self.auth.login()
        return self.auth.token

    def close(self):
        self.auth.logout()

class Category(object):

    def __init__(self):
        self.folder = Folder()
        self.repository = Repository()
        self.property = Property()

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
        self.property = Property()
        self.document = Document()

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

    def get_filename_from_path(self, path):
        """
        Split a file path on the separator and return the file name
        :return string file name
        """
        return path.split("/")[-1]


class DirectoryListing(object):

    documents = []
    folders = []

    def __init__(self):
        self.doc = Document()
        self.folder = Folder()

    def get_root_path(self):
        return settings.OPENKM['UploadRoot']

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

class DocumentManager(object):

    def __init__(self):
        self.document = Document()

    def create(self, file_obj):
        document = self.document.new()
        document.path = self.create_path_from_filename(file_obj)
        content = self.convert_file_content_to_binary_for_transport(file_obj)
        return self.create_document_on_openkm(document, content)

    def create_path_from_filename(self, file_obj):
        """
        Constructs a path name of the format:

            upload_root + filename

        :returns string:  path name
        """
        return settings.OPENKM['UploadRoot'] + file_obj.__str__()

    def convert_file_content_to_binary_for_transport(self, file_obj):
        return make_file_java_byte_array_compatible(file_obj)

    def create_document_on_openkm(self, document, content):
        return self.document.create(document, content)

