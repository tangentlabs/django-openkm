django-openkm
=============

A Python/Django client library for interaction with the OpenKM web services API.  Integrates into the Django admin.
OpenKM is an open-source, Java document management system with Lucene search built-in.

INSTALLATION
------------

1. Install with::

    pip install django-openkm

2. Add 'django-openkm' to your INSTALLED_APPS

3. Add the following to your Django settings::

    OPENKM = {
        'configuration': {
            'Logging': True,
            'UploadRoot': '/okm:root/Uploads/',
            'Host': 'http://localhost:8080/',
            'User': 'okmAdmin',
            'Password': 'admin',
            'Path': 'OpenKM',
            'tagging': True
        },
        'categories': {
            # simply a list of string paths pointing to your models
            # { 'path.to.app.model' : 'Category name on OpenKM' }
            'yourproject.foo.models.Region': 'Region',
            'yourproject.foo.models.Role': 'Roles',
            'yourproject.foo.models.Product': 'Products',
            'yourproject.bar.models.Task': 'Task,'
        },
        'properties': {
            "okg:customProperties": {
                "okp:customProperties.title": {'attribute': 'name'},
                'okp:customProperties.description': {'attribute': 'description'},
                'okp:customProperties.languages': {'attribute': 'languages', 'choices': None},
                },
            "okg:salesProperties": {
                'okp:salesProperties.assetType': {'attribute': 'type', 'choices': 'path.to.your.CHOICES'},
                }
        }
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
