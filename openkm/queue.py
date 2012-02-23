import sync

from django.conf import settings

class Producer(object):
    """
    Prepares metadata for transport to queue
    """
    def prepare(self, document, openkm_folderlist_class):
        """
        Creates and populates the data ready for transport
        :param document
        """


    def enqueue(self, document, openkm_folderlist_class):

        # prepare the data
        utils = sync.DjangoToOpenKm()
        keywords = sync.SyncKeywords()
        properties = sync.SyncProperties()

        data = {
            'taxonomy': utils.build_taxonomy(document),
            'keywords': keywords.get_tags_from_document(document),
            'properties': properties.populate_property_group_map(settings.OPENKM['properties'], document),
            'categories': utils.get_category_uuids(document, openkm_folderlist_class)
        }

        return data

class Consumer(object):
    """
    Picks up document from the queue.  Makes the webservice calls to OpenKM to create/update the document
    and sends the returned metadata from OpenKM to the queue
    """
    def collect(self):
        pass