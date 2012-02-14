import sys, logging
from functools import wraps

from django.conf import settings

from suds import WebFault
from suds.client import Client

import exceptions

logging.getLogger('suds.client').setLevel(logging.INFO)

PATH = settings.OPENKM['configuration']['Path']

OPENKM_WSDLS = {
    'Auth': settings.OPENKM['configuration']['Host'] + '%s/OKMAuth?wsdl' % PATH,
    'Bookmark': settings.OPENKM['configuration']['Host'] + '%s/OKMBookmark?wsdl' % PATH,
    'Document': settings.OPENKM['configuration']['Host'] + '%s/OKMDocument?wsdl' % PATH,
    'Search': settings.OPENKM['configuration']['Host'] + '%s/OKMSearch?wsdl' % PATH,
    'Note': settings.OPENKM['configuration']['Host'] + '%s/OKMNote?wsdl' % PATH,
    'Folder': settings.OPENKM['configuration']['Host'] + '%s/OKMFolder?wsdl' % PATH,
    'Property': settings.OPENKM['configuration']['Host'] + '%s/OKMProperty?wsdl' % PATH,
    'PropertyGroup': settings.OPENKM['configuration']['Host'] + '%s/OKMPropertyGroup?wsdl' % PATH,
    'Repository': settings.OPENKM['configuration']['Host'] + '%s/OKMRepository?wsdl' % PATH,
    }

def try_except(fn):
    """
        A decorator to catch suds exceptions and rethrow custom excpetions to mirror the actual exceptions raised by OpenKM
        @todo allow each function to define the expected exceptions raised
       """
    def wrapped(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception, e:
            et, ei, tb = sys.exc_info()
            parser = exceptions.ExceptionParser()
            raised_exception = parser.get_raised_exception_class_name(e)
            exception = getattr(exceptions, raised_exception)
            raise exception, exception(e), tb
    return wraps(fn)(wrapped)

def get_service(class_name):
    return Client(OPENKM_WSDLS[class_name]).service

def get_client(class_name):
    return Client(OPENKM_WSDLS[class_name])

def get_token():
    auth = Auth()
    auth.login()
    return auth.token


class BaseService(object):

    def __init__(self, start_session=True, class_name=None):
        if not class_name:
            class_name = self.__class__.__name__
        self.service = get_service(class_name)
        self.client = get_client(class_name)
        if start_session:
            self.token = get_token()


class Auth(BaseService):
    """ Methods related to authentication, granting and revoking privileges. """

    def __init__(self):
        super(Auth, self).__init__(start_session=False)

    def login(self, user=settings.OPENKM['configuration']['User'], password=settings.OPENKM['configuration']['Password']):
        self.token = self.service.login(user=user, password=password)

    def logout(self):
        return self.service.logout(token=self.token)

    def get_users(self):
        return self.service.getUsers(token=self.token)

    def get_roles(self):
        return self.service.getRoles(token=self.token)

    def grant_user(self):
        pass

    def revoke_user(self):
        pass

    def get_granted_users(self, node_path=None):
        return self.service.getGrantedUsers(token=self.token, nodePath=node_path)

    def grant_role(self, node_path, role, permissions, recursive):
        return self.service.grantRole(token=self.token, nodePath=node_path, role=role,
            permissions=permissions, recursive=recursive)

    def revoke_role(self):
        pass

    def get_granted_roles(self):
        pass



#from .utils import try_except

class Document(BaseService):
    """Methods related to document management. """

    def new(self):
        """
        Returns a document object
        """
        return self.client.factory.create('document')

    def create(self, doc, content):
        """
            Create a new document in the repository.
            :param Document object (use self.new())
            :param content Java byte[] compatible (use make_file_java_byte_array_compatible())
            :return A document object with the properties of the new created document.
            """
        return self.service.create(token=self.token, doc=doc, content=content)

    def delete(self, doc_path):
        """
        Removes a document from the repository and move it to the user trash.
        :param doc_path string
        :return none
        """
        return self.service.delete(token=self.token, docPath=doc_path)


    def lock(self, doc_path):
        """
        Lock a document, so only is editable by the locker.
        :param doc_path: string
        :return A Collection of Versions with every document version.
        """
        return self.service.lock(token=self.token, docPath=doc_path)


    def unlock(self, doc_path):
        """
        Unlock a document, so will be editable for other users.
        :param doc_path: string
        :return none
        """
        return self.service.unlock(token=self.token, docPath=doc_path)


    def rename(self, doc_path, new_name):
        """
        Rename a document in the repository.
        :param doc_path string
        :param new_name string
        :return A document object with the new document properties.
        """
        return self.service.rename(token=self.token, docPath=doc_path, newName=new_name)


    def move(self, doc_path, new_name):
        """
        Move a document to another location in the repository.
        :param doc_path string
        :param new_name string
        :return none
        """
        return self.service.move(token=self.token, docPath=doc_path, newName=new_name)


    def get_properties(self, doc_path):
        """
        Obtain document properties from the repository.
        :param doc_path string
        :return The document properties.
        """
        return self.service.getProperties(token=self.token, docPath=doc_path)


    def set_properties(self, doc):
        """
        Set the properties of a repository document
        :param doc Document object
        :return none
        """
        return self.service.setProperties(token=self.token, doc=doc)


    def set_content(self, doc_path, content):
        """
        Set document content in the repository.
        :param doc_path string
        :param content byte array (Java)
        :return none
        """
        return self.service.setContent(token=self.token, docPath=doc_path, content=content)


    def get_content(self, doc_path, checkout):
        """Obtain document content from the repository.
        :param doc_path string
        :param checkout boolean
        """
        return self.service.getContent(token=self.token, docPath=doc_path, checkout=checkout)


    def get_content_by_version(self, doc_path, version_id):
        """
        Obtain document content from the repository.
        :param doc_path
        :param version_id
        """
        return self.service.getContentByVersion(token=self.token, docPath=doc_path, versionId=version_id)


    def checkout(self, doc_path):
        """
        Checkout the document to edit it. The document can't be edited by another user until it is checked in o the checkout is cancelled.
        :param doc_path string
        :return A Collection with the child documents
        """
        return self.service.checkout(token=self.token, docPath=doc_path)


    def cancel_checkout(self, doc_path):
        """
        Cancel a previous checked out state in a document.
        :param doc_path string The path that identifies an unique document.
        :return A Collection with the child documents.
        """
        return self.service.cancelCheckout(token=self.token, docPath=doc_path)


    def checkin(self, doc_path):
        """
        Check in the document to create a new version.
        :param doc_path string
        :return A version object with the properties of the new generated version.
        """
        return self.service.checkin(token=self.token, docPath=doc_path)


    def get_version_history(self, doc_path):
        """
        Get the document version history.
        :param doc_path string
        :return A Collection of Versions with every document version.
        """
        return self.service.getVersionHistory(token=self.token, docPath=doc_path)


    def restore_version(self, doc_path, version_id):
        """
        Revert the document to an specific previous version.
        :param doc_path string
        :param version_id string
        """
        return self.service.restoreVersion(token=self.token, docPath=doc_path, versionId=version_id)

    def get_children(self, folder_path):
        """
        Retrieve a list of child documents from an existing folder.
        :param folder_path string
        :return A Collection with the child documents.
        """
        return self.service.getChilds(token=self.token, fldPath=folder_path)

    def is_valid(self, doc_path):
        """
        Test if a document path is valid.
        :param doc_path
        :return boolean True if the path denotes a document, otherwise false.
        """
        return self.service.isValid(token=self.token, docPath=doc_path)


    def get_path(self, uuid):
        """
        The the document path from a UUID.
        :param uuid string
        :return The document path or null if this UUID does not correspond to a document node.
        """
        return self.service.getPath(token=self.token, uuid=uuid)

class Search(BaseService):
    """Methods related to repository search. """

    def by_content(self, words):
        """Search for documents using it indexed content.  """
        return self.service.findByContent(self.token, words)

    def by_name(self, words):
        """Search for documents by document name. """
        return self.service.findByName(token=self.token, name=words)

    def by_keyword(self, keywords):
        """Search for documents using it associated keywords. """
        return self.service.findByKeywords(token=self.token, keywords=keywords)

    def by_statement(self, statement, type):
        """
        Example (returns all published documents):
        statement = "/jcr:root/okm:root//element(*,okm:document)[okp:published.status='published']"
        """
        return self.service.findByStatement(token=self.token, statement=statement, type=type)

    def find(self, params):
        """ Performs a complex search by content, name and keywords (between others). """
        return self.service.find(token=self.token, params=params)

    def get_keyword_map(self, filter):
        """ Return a Keyword map. This is a hash with the keywords and the occurrence.  """
        return self.service.getKeywordMap(token=self.token, filter=filter)

    def get_categorised_documents(self, category_id):
        """ Get the documents within a category """
        return self.service.getCategorizedDocuments(token=self.token, categoryId=category_id)


class Bookmark(BaseService):
    """Methods related to bookmark management """

    def add(self, node_path, bookmark_name):
        """Add a new bookmark which points to this document """
        return self.service.add(self.token, node_path, bookmark_name)

    def get(self, bookmark_id):
        """Get info from a previously created bookmark. """
        return self.service.get(token=self.token, bmId=bookmark_id)

    def remove(self, bookmark_id):
        """Remove a bookmark. """
        return self.service.remove(token=self.token, bmId=bookmark_id)

    def rename(self, bookmark_id, new_name):
        """Rename a previous stored bookmark. """
        return self.service.rename(token=self.token, bmId=bookmark_id, newName=new_name)

    def get_all(self):
        """Retrieve a users bookmark collection. """
        return self.service.getAll(token=self.token)


class Note(BaseService):
    """Methods related to document notes management. """

    def add(self, node_path, text):
        """Add a note to a document. """
        return self.service.add(token=self.token, nodePath=node_path, text=text)

    def get(self, note_path):
        """Get note from document """
        return self.service.get(token=self.token, notePath=note_path)

    def remove(self, note_path):
        """Remove a note from a document. """
        return self.service.remove(token=self.token, notePath=note_path)

    def set(self, note_path, text):
        """Set a new text to document note. """
        return self.service.set(token=self.token, notePath=note_path, text=text)

    def list(self, node_path):
        """Retrieve a list of notes from a document. """
        return self.service.list(token=self.token, nodePath=node_path)


class Folder(BaseService):

    def new(self):
        return self.client.factory.create('folder')

    def create(self, folder_obj):
        return self.service.create(token=self.token, fld=folder_obj)

    def get_properties(self, folder_path):
        return self.service.getProperties(token=self.token, fldPath=folder_path)

    def delete(self, folder_path):
        return self.service.delete(token=self.token, fldPath=folder_path)

    def delete_children(self, folder_path):
        children = self.get_children(folder_path)
        for child in children.item:
            self.delete(child.path)

    def rename(self, folder_path, new_folder_path):
        return self.service.rename(token=self.token, fldPath=folder_path, newName=new_folder_path)

    def move(self, current_folder_path, destination_path):
        return self.service.move(token=self.token, fldPath=current_folder_path, dstPath=destination_path)

    def get_children(self, folder_path):
        """Remove a note from a document. """
        return self.service.getChilds(token=self.token, fldPath=folder_path)

    def is_valid(self, folder_path):
        return self.service.isValid(token=self.token, fldPath=folder_path)

    def get_path(self, uuid):
        return self.service.getPath(token=self.token, uuid=uuid)


class Property(BaseService):

    def add_category(self, node_path, category_uuid):
        return self.service.addCategory(self.token, nodePath=node_path, catId=category_uuid)

    def remove_category(self, node_path, category_uuid):
        return self.service.removeCategory(token=self.token, nodePath=node_path, catId=category_uuid)

    def add_keyword(self, node_path, keyword):
        return self.service.addKeyword(token=self.token, nodePath=node_path, keyword=keyword)

    def remove_keyword(self, node_path, keyword):
        ''' Add a keyword to a document.  '''
        return self.service.removeKeyword(token=self.token, nodePath=node_path, keyword=keyword)


class PropertyGroup(BaseService):
    '''
    Methods related to Property Groups.
    '''

    def add_group(self, node_path, group_name):
        ''' Add a property group to a document. '''
        return self.service.addGroup(token=self.token, nodePath=node_path, grpName=group_name)

    def remove_group(self, node_path, group_name):
        return self.service.removeGroup(token=self.token, nodePath=node_path, grpName=group_name)

    def get_groups(self, node_path):
        ''' Get groups assigned to a document. '''
        return self.service.getGroups(token=self.token, nodePath=node_path)

    def get_all_groups(self):
        ''' Get all groups defined in the system. '''
        return self.service.getAllGroups(token=self.token)

    def get_properties(self, node_path, group_name):
        return self.service.getProperties(token=self.token, nodePath=node_path, grpName=group_name)

    def set_properties(self, node_path, group_name, properties):
        return self.service.setProperties(token=self.token, nodePath=node_path, grpName=group_name, properties=properties)

    def has_group(self, node_path, group_name):
        return self.service.hasGroup(token=self.token, nodePath=node_path, grpName=group_name)


class Repository(BaseService):

    def get_root_folder(self):
        return self.service.getRootFolder(self.token)

    def get_trash_folder(self):
        return self.service.getTrashFolder(token=self.token)

    def get_templates_folder(self):
        return self.service.getTemplatesFolder(token=self.token)

    def get_personal_folder(self):
        return self.service.getPersonalFolder(token=self.token)

    def get_mail_folder(self):
        return self.service.getMailFolder(token=self.token)

    def get_thesaurus_folder(self):
        return self.service.getThesaurusFolder(token=self.token)

    def get_categories_folder(self):
        return self.service.getCategoriesFolder(token=self.token)

    def purge_trash(self):
        return self.service.purgeTrash(token=self.token)

    def has_node(self, path):
        """ Test if a node path exists """
        return self.service.hasNode(token=self.token, path=path)

    def get_path(self, uuid):
        """ Obtain the node path with a given uuid. """
        return self.service.getPath(token=self.token, uuid=uuid)

