django-openkm
=============

A Python/Django client library for interaction with the OpenKM web services API.  Integrates into the Django admin.
OpenKM is an open-source, Java document management system with Lucene search built-in.

INSTALLATION
------------

1. Install with::

    pip install django_openkm

2. Add 'django_openkm' to your INSTALLED_APPS

3. Add the following to your Django settings::

    OPENKM = {
        'UploadRoot': '/okm:root/',
        'Host': 'http://localhost:8080/',
        'User': 'okmAdmin',
        'Password': 'admin',
        'Path': 'OpenKM', 
    }
    
4. Ensure your MEDIA_ROOT is set up with the correct permissions and working

5. Run syncdb and check your Django admin.  You will now be able to upload files through the admin interface.  
(This will likely be removed later in favour of abstract models classes, but just as proof of concept)

[For OpenKM installation see http://wiki.openkm.com/index.php/Quick_Install.  It's pretty straightforward to setup locally
just download, unzip to /opt, run the bash script in bin/run.sh and your up and running]

Developed and maintained by Phil Tysoe at `Tangent Labs`_

.. _`Tangent Labs`: http://tangentlabs.co.uk/


Useful links:
-------------

http://www.openkm.com/

http://wiki.openkm.com/index.php/Webservices_Guide

http://lucene.apache.org/java/docs/index.html
