from django.test import TestCase
from django.conf import settings

from .client import Auth, Document, Folder, Note, OPENKM_WSDLS, Repository, PropertyGroup
from .facades import Keyword, Category, DirectoryListing
from .sync import SyncKeywords, SyncCategories, SyncFolderList
from .models import OpenKmDocument, OpenKmFolderList

class ClientTest(TestCase):
    """ Tests of functions and settings """
    
    def setUp(self):
        pass
    
    def test_settings(self):
        """ Check that the config values are set in the settings file """
        keys = ('Logging', 'UploadRoot', 'Host', 'User', 'Password')
        for key in keys:
            self.assertTrue(settings.OPENKM.has_key(key))
            
    def test_wsdl_map(self):
        """ Check fof the presence of the WSDL dict map """
        self.assertTrue(isinstance(OPENKM_WSDLS, dict))


class FolderTest(TestCase):
    
    def setUp(self):
        self.folder = Folder()

    def test_get_children(self):
        children = self.folder.get_children('/okm:root/')
        self.assertTrue(hasattr(children, 'item'))

class AuthTest(TestCase):
    
    def setUp(self):
        self.auth = Auth()
        
    def test_login(self):
        """ Check we can login and get a token """
        self.auth.login()
        self.assertTrue(hasattr(self.auth, 'token'), msg="Token has not been set")
        self.assertTrue(len(self.auth.token) > 1, msg="Token is empty")
        
    def test_logout(self):
        """ A successful logout should destroy the session token """
        self.auth.login()
        has_token = hasattr(object, 'token')
        self.auth.logout()

        try:
            has_token = hasattr(object, 'token')
        except AttributeError:
            has_token = False
        finally:
            self.assertFalse(has_token)

    def has_token_attribute(self, object):
        return hasattr(object, 'token')

    def test_get_roles(self):
        self.auth.login()
        roles = self.auth.get_roles()
        self.assertTrue(hasattr(roles, 'item'), msg="instance expected to contain item[]")
        self.assertTrue(isinstance(roles.item, list), msg="role.item expected to be a list")
    
    def test_grant_role(self):
        pass
    
    def test_revoke_role(self):
        pass
    
    def test_get_users(self):
        pass
    
    def test_grant_user(self):
        pass
    
    def test_revoke_user(self):
        pass
    
    def test_get_granted_users(self):
        pass
    

class DocumentTest(TestCase):
    
    test_doc_path = '%s%s' % (settings.OPENKM['UploadRoot'], 'testing123.pdf')
    
    def setUp(self):
        """
        Login to OpenKM, get the session token and use it to instantiate
        a Document object
        """
        self.test_doc = 'xxxx'
        try:
            self.auth = Auth()
            self.auth.login()

            self.doc = Document()
            
            # create a test document
            test_doc = self.doc.new()
            test_doc.path = self.test_doc_path
            self.doc.create(test_doc, "hf7438hf7843h378ot4837ht7")
            self.test_doc = self.doc.get_properties(self.test_doc_path)
        except AssertionError, detail:
            print detail
        
    def test_token_has_been_set(self):
        """
        Check that the token has been set in both Auth and Document,
        otherwise we won't be doing anything
        """
        self.assertTrue(hasattr(self.auth, 'token'), msg="Token not set in Auth")
        self.assertTrue(hasattr(self.doc, 'token'), msg="Token not set in Document")
        
    def document_object(self, doc):
        """ 
        Test the structure of a document instance 
        """
        keys = ('actualVersion', 'author', 'checkedOut', 'convertibleToDxf',
                'convertibleToPdf', 'convertibleToSwf', 'created', 'language', 'lastModified',
                'locked', 'mimeType', 'path', 'permissions', 'subscribed', 'uuid')
        for key in keys:
            msg = "%s doesn't exist" % key
            self.assertTrue(hasattr(doc, key), msg)

        return True
            
    def test_create(self):
        """ Create a test document """
        test_doc = self.doc.new()
        filename = 'abc.pdf'
        test_doc.path = '%s%s' % (settings.OPENKM['UploadRoot'], filename)
        content = "hf8478y7ro48y7y7t4y78o4"
        self.doc.create(test_doc, content)
        new_document = self.doc.get_properties(test_doc.path)
        
        self.assertEqual(test_doc.path, new_document.path, msg="Created document path does not match that uploaded")
        
        # clean up the file, otherwise it will remain on OpenKM causing the next test run to fail
        self.doc.delete(new_document.path)
        
    def test_lock(self):
        """ Lock and unlock a document """
        self.doc.lock(self.test_doc.path)
        properties = self.doc.get_properties(self.test_doc_path)
        self.assertTrue(properties.locked, msg="Document is not locked")
        
        self.doc.unlock(self.test_doc.path)
        properties = self.doc.get_properties(self.test_doc_path)
        self.assertFalse(properties.locked, msg="Document is locked")
        
    def test_get_properties(self):
        """ Get the properites of a document and check the attributes """
        d = self.doc.get_properties(self.test_doc.path)
        contains_keys = self.document_object(d)
        self.assertTrue(contains_keys) # make sure it contains the expected attributes

    def tearDown(self):
        self.doc.delete(self.test_doc_path)
        self.auth.logout()

class PropertyTest(TestCase):
    pass

class PropertyGroupTest(TestCase):

    def setUp(self):
        self.test_document = create_test_document_on_openkm()
        self.property_group = PropertyGroup()
        self.document = Document()
        self.new_group = 'okg:customProperties'

    def test_add_and_remove_group(self):
        """
        Creates a new document
        Adds a property group (which must already exist on OpenKM) to a document
        Checks the property group has been added to the document
        Removes the group
        Checks it has been removed
        Deletes document
        """
        self.property_group.add_group(self.test_document.path, self.new_group)
        property_groups = self.property_group.get_groups(self.test_document.path)
        assigned_property_group = property_groups.item[0].name
        self.assertEqual(assigned_property_group, self.new_group, msg="Assigned property group not as expected")
        self.property_group.remove_group(self.test_document.path, self.new_group)
        property_groups = self.property_group.get_groups(self.test_document.path)
        if property_groups:
            raise Exception('Document has property groups %s' % property_groups)

    def test_get_all_groups(self):
        pass

    def test_get_properties(self):
        pass

    def test_set_properties(self):
        pass

    def test_has_group(self):
        pass

    def tearDown(self):
        delete_test_document_on_openkm()

def get_test_document_path():
    return '%snotes.pdf' % settings.OPENKM['UploadRoot']

def create_test_document_on_openkm():
    document = Document()
    test_doc = document.new()
    test_doc.path = get_test_document_path()
    document.create(test_doc, "hf7438hf7843h378ot4837ht7")
    return document.get_properties(test_doc.path)

def delete_test_document_on_openkm():
    d = Document()
    d.delete(get_test_document_path())

class NoteTest(TestCase):
    
    def setUp(self):
        self.document = Document()
        self.note = Note()
        self.auth = Auth()
        self.auth.login()
        self.test_document = create_test_document_on_openkm()

    def test_add_and_remove(self):
        # add a note
        text = 'hello, this is a note'
        meta = self.note.add(self.test_document.path, text)
        
        # remove it
        self.note.remove(meta.path)
        
    def test_get_list(self):
        """
        Add some notes to a document and retrieve them
        """
        # add three notes
        notes = ('one', 'two', 'three')
        for note in notes:
            self.note.add(self.test_document.path, note)
        
        # test that the notes returned match those added
        list = self.note.list('/okm:root/gsa/notes.pdf')
        for entered, note in zip(notes, list.item):
            self.assertEqual(entered, note.text)
            self.note.remove(note.path)
            
    def test_get(self):
        text = 'Knock, knock...'
        note = self.note.add(self.test_document.path, text)
        note_meta = self.note.get(note.path)
        self.assertEqual(note_meta.text, text, msg='Returned note does not match')
        self.note.remove(note_meta.path)
        
    def tearDown(self):
        delete_test_document_on_openkm()

KEYWORDS = ('One', 'Two', 'Three', 'Hammertime!')

class KeywordTest(TestCase):

    def setUp(self):
        self.keyword = Keyword()
        self.test_document = create_test_document_on_openkm()

    def test_add(self):
        for keyword in KEYWORDS:
            self.keyword.add(self.test_document.path, keyword)

    def test_remove(self):
        for keyword in KEYWORDS:
            self.keyword.remove(self.test_document.path, keyword)
            
    def tearDown(self):
        delete_test_document_on_openkm()

if settings.OPENKM['tagging']:
    class SyncKeywordsTest(TestCase):

        def setUp(self):
            self.resource = OpenKmDocument()
            self.resource.tag_set = u'One, Two, Three'
            self.sync_keywords = SyncKeywords()
            self.path = '/okm:root/test-global.html'
            self.tags = self.sync_keywords.get_tags_from_resource(self.resource)

        def test_get_tags_from_resource(self):
            """
            Should take a a comma separated string of tags and return a list
            """
            self.assertTrue(isinstance(self.tags, list), msg="Tags should be returned as a list")

        def test_tags_are_unicode(self):
            tags = self.sync_keywords.get_tags_from_resource(self.resource)
            for tag in tags:
                self.assertTrue(isinstance(tag, unicode), msg="%s is not a string, it is %s" % (tag, type(tag)))

        def test_add_keyword_to_openkm_document(self):
            self.sync_keywords.add_keyword_to_openkm_document(self.path, 'Example')

            # cleanup
            self.sync_keywords.keyword.remove(self.path, 'Example')

        def test_write_keywords_to_openkm_document(self):
            self.sync_keywords.write_keywords_to_openkm_document(self.path, self.tags)

        def test_single_document_django_to_helix(self):
            pass


class CategoryTest(TestCase):

    def setUp(self):
        self.category = Category()
        self.repository = Repository()

    def test_get_category_root_object_structure(self):
        category_root = self.category.get_category_root()
        attrs = ('author', 'created', 'hasChilds', 'path', 'permissions', 'subscribed', 'uuid')
        for attr in attrs:
            self.assertTrue(hasattr(category_root, attr), msg="%s is not an attribute of the object returned \
            by category root" % attr)

    def test_category_root_path(self):
        category_root = self.category.get_category_root()
        expected = "/okm:categories"
        self.assertEquals(category_root.path, expected, msg="Category root returned %s was not %s" \
        % (category_root.path, expected))

    def test_create_and_remove(self):
        """
        Test these together so we clean up after ourselves
        """
        base_path = self.category.get_category_root().path
        new_category_name = 'UnitTest'
        new_category_path = self.category.construct_valid_path_string(base_path, new_category_name)

        # create the category
        expected_path = new_category_path
        new_category = self.category.create(new_category_path)
        self.assertEquals(new_category.path, expected_path)

        # remove the path
        self.category.remove(new_category.path)

        # test that the category has been removed
        self.assertFalse(self.repository.has_node(new_category.path), msg="Category has not been removed \
        node %s found" % new_category.path)

    def test_construct_valid_path_string(self):
        base_path = '/okm:categories'
        category = 'Products'
        expected = '/okm:categories/Products'
        returned = self.category.construct_valid_path_string(base_path, category)
        self.assertEquals(expected, returned, msg="Returned path %s did not match the expected path %s" %\
                                                  (returned, expected))


class MockResource(object):
    """
    Creates a mock resource, with populated many-to-many fields to be used in tests
    """
    def __init__(self):
        self.sync_categories = SyncCategories()

    def generate_test_resource(self):
        """
        Creates a Resource to be used in testing and populates the many-to-many fields
        with query sets.  Currently simple calling .all() on the related models
        """
        document = OpenKmDocument()
        document.save()

        # for each model
        for klass in self.sync_categories.MODEL_CATEGORY_MAP.keys():

            # get the model_set many-to-many function of the Resource object
            method_name = '%s_set' % klass.__name__.lower()
            _set = getattr(document, method_name)

            # populate the resource with objects from the related model
            objects = klass.objects.all()
            for object in objects:
                _set.add(object)

        return document

    def populate_test_model(self, model_klass, related_model_klasses):
        """
        Populates a model to be used in testing and populates the many-to-many fields
        with query sets.  Currently simple calling .all() on the related models.
        Assumes that the naming convention for related model function names if
        [model_name_lowercase]_set (this comes from a legacy project)
        :param model_klass: the main model class
        :param related_model_klasses: an iterable of related model classes
        """
        main_model = model_klass()
        main_model.save()

        # for each model
        for klass in related_model_klasses:

            # get the many-to-many function of the model_klass object
            method_name = '%s_set' % klass.__name__.lower()
            _set = getattr(main_model, method_name)

            # populate the model_klass instance with objects from the related model
            objects = klass.objects.all()
            for object in objects:
                _set.add(object)

        return main_model



class SyncCategoriesTest(TestCase):

    fixtures = []

    def setUp(self):
        self.sync_categories = SyncCategories()
        self.category = Category()
        m = MockResource()
        self.r = m.generate_test_resource()

    def test_category_map(self):
        """ Check for existence only as content may change """
        self.assertTrue(hasattr(self.sync_categories, 'MODEL_CATEGORY_MAP'), msg="Category map dict not found")

    def test_get_child_categories(self):
        """
        Returns a list of folder objects which are the child categories of the parent given as param
        """

        # add a category to root so we will return results in the next step
        category_root_path = self.category.get_category_root().path
        mock_category_path = self.category.construct_valid_path_string(category_root_path, 'DummyXYZ')
        mock_category = self.category.create(mock_category_path)

        child_categories = self.sync_categories.get_child_categories(category_root_path)

        has_child = False
        for child in child_categories.item:
            if child.path == mock_category.path:
                has_child = True
        self.assertTrue(has_child, msg="The mock category %s was not found in the returned \
        child categories of %s" % (mock_category.path, category_root_path))

        # clean up
        self.category.remove(mock_category.path)

    def test_create_categories_from_django_model(self):
        #print self.sync_categories.create_categories_from_django_model(Resource, 'Test')
        pass

    def test_django_to_openkm(self):
        for django_model, openkm_model in self.sync_categories.MODEL_CATEGORY_MAP.items():
            print django_model, openkm_model

    def test_openkm_to_django(self):
        pass

    def test_get_categories_from_gsa(self):
        for model in self.sync_categories.MODEL_CATEGORY_MAP.keys():
            model_name = model.__name__.lower()
            print self.sync_categories.get_related_objects_from_model(self.r, model_name)


class SyncResourceTest(TestCase):

    def setUp(self):
        m = MockResource()
        self.r = m.generate_test_resource()
        self.sr = SyncResource(self.r)
        self.test_document = create_test_document_on_openkm()

    def test_init_was_successful(self):
        """ Check that the objects we need were instantiated correctly """
        self.assertTrue(isinstance(self.sr.sync_keywords, SyncKeywords))
        self.assertTrue(isinstance(self.sr.auth, Auth))
        self.assertTrue(isinstance(self.sr.document, Document))
        self.assertTrue(isinstance(self.sr.repository, Repository))

    def test_new_openkm_document_object(self):
        """
        Should return a new openkm document object.  Note this does not yet exist on OpenKM until
        Document.create()
        """
        doc_obj = self.sr.new_openkm_document_object()
        self.assertEquals(str(doc_obj.__class__), 'suds.sudsobject.document')

    def test_document_exists_on_openkm(self):
        path = self.test_document.path
        self.assertTrue(self.sr.document_exists_on_openkm(path), msg="Document was not found on OpenKM: %s" % path)

    def categories(self):
        pass

    def properties(self):
        pass

    def file(self):
        """ Uploads the file
        """
        pass

    def tearDown(self):
        delete_test_document_on_openkm()

class DirectoryListingTest(TestCase):

    def setUp(self):
        self.dir = DirectoryListing()

    def test_traverse(self):
        self.dir.traverse_folders('/okm:categories/')


class SyncFolderListTest(TestCase):

    def setUp(self):
        self.folder_list = SyncFolderList()

    def test_get_list_of_root_paths(self):
        paths = self.folder_list.get_list_of_root_paths()
        self.assertTrue(isinstance(paths, list), msg="Expected return value to be a list")



