import StringIO

from django.http import HttpResponse

import client, utils

def get_document_by_uuid(request, uuid):
    """
    Returns a document from OpenKM
    """
    # get path from the uuid, and from that get the content
    document = client.Document()
    document_path = document.get_path(uuid)
    doc_meta = document.get_properties(document_path)
    java_byte_array = document.get_content(document_path, False)
    
    # convert the string back to binary
    file_obj = StringIO.StringIO(java_byte_array)
    document = utils.java_byte_array_to_binary(file_obj)
    
    # set the headers and return the file
    file_name = doc_meta.path.split("/")[-1]
    response = HttpResponse(document, doc_meta.mimeType)
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    return response
