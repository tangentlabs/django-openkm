django-openkm
=============

**WORK IN PROGRESS**
There are existing tests (500+ lines), models and views - however they need to be refactored to abstract them from their
current project.  So basically, the Django stuff will come later, but not much later.

A Python/Django client library for interaction with the OpenKM web services API.

OpenKM is an open-source, Java document management system with Lucene search built-in.

Add the following to your settings::

    OPENKM = {
        'UploadRoot': '/okm:root/',
        'Host': 'http://localhost:8080/',
        'User': 'okmAdmin',
        'Password': 'admin'
    }


Useful links:
-------------

http://www.openkm.com/
http://wiki.openkm.com/index.php/Webservices_Guide
http://lucene.apache.org/java/docs/index.html