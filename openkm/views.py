import StringIO

from django.http import HttpResponse
from django.utils import encoding

import client, utils


class DocumentWrapper(object):
    document = None
    content = None
    response = None


def get_document_by_uuid(request, uuid, extra_info=False):
    """
    Returns a tuple.
    (HttpResponse object that can be returned to provide the file for download,
    the file name (string),
    the file object)
    """
    document_wrapper = DocumentWrapper()

    # get path from the uuid, and from that get the content
    document = client.Document()
    document_path = document.get_path(uuid)
    document_wrapper.document = document.get_properties(document_path)
    java_byte_array = document.get_content(document_path, False)
    
    # convert the string back to binary
    file_obj = StringIO.StringIO(java_byte_array)
    document_wrapper.content = utils.java_byte_array_to_binary(file_obj)
    
    # set the headers and return the file
    file_name = document_wrapper.document.path.split("/")[-1]
    document_wrapper.response = HttpResponse(document_wrapper.content, document_wrapper.document.mimeType)
    document_wrapper.response['Content-Disposition'] = 'attachment; filename=%s' % encoding.smart_str(file_name, encoding='ascii', errors='ignore')
    
    return document_wrapper