Overview
========

django_openkm provides Django integration for the OpenKM document management system.  Once you have added the application
you can extend its abstract models to delegate the storage, search and retrieval of your application's document to OpenKM.

Features:

1. Category construction.  Categories correspond to your Document's many-to-many fields.  These can be dynamically created
on OpenKM based on the data currently stored by your application.
2. Keyword syncing.  OpenKM keywords correspond to the tags provided by django-tagging.  These tags can by synced on a
per document basis allowing you to make use of OpenKM's keyword cloud and search functionality.

Categories
==========

OpenKM categories correspond to a models many-to-many field
        
To update OpenKM with a Document's many-to-many field:

1. Get the m2m model name and its associated objects. With these build a list and pass this to get_uuids_from_custom_list::

        and_predicates = ['categories', 'Region']
        or_predicates = ['North America','EMEA']
        OpenKmFolderList.objects.get_uuids_from_custom_list(and_predicates, or_predicates)

This will return a list of uuids of the categories.  Now simply loop through the list to associate the category with the
document.  (Note: This would be much more efficient as bulk operation, but I am not aware of a way to send an array of
uuids via OpenKM webservices so far)


