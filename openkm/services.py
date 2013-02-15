from openkm import models


class OpenKMAuditService(object):

    def record_update(self, token, content, occured):
        """
        token (string)
        content (instance of document) as returned by 
            openkm.client.Document.create_document_content_object
        occured (datetime.datetime)
        """
        return models.OpenKMEvent.objects.create(
            token=token,
            content=content,
            occured=occured
            )

    def record_create(self, token, content, occured):
        """
        token (string)
        content (instance of document) as returned by 
            openkm.client.Document.create_document_content_object
        occured (datetime.datetime)
        """
        return models.OpenKMEvent.objects.create(
            token=token,
            content=content,
            occured=occured
            )