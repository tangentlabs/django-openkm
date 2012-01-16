import base64
import logging

import suds

"""
Some useful helper and decorator functions
"""

def try_except(fn):
    """ A decorator to catch suds exceptions """
    def wrapped(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except suds.WebFault as detail:
            return detail
    return wrapped

def make_file_java_byte_array_compatible(file_obj):
    """ 
    Reads in a file and converts it to a format accepted as Java byte array 
    :param file object
    :return string
    """
    encoded_data = base64.b64encode(file_obj.read())
    strg = ''
    for i in xrange((len(encoded_data)/40)+1):
        strg += encoded_data[i*40:(i+1)*40]
        
    return strg

def java_byte_array_to_binary(file_obj):
    """ 
    Converts a java byte array to a binary stream
    :param java byte array as string (pass in as a file like object, can use StringIO)
    :return binary string
    """
    decoded_data = base64.b64decode(file_obj.read())
    strg = ''
    for i in xrange((len(decoded_data)/40)+1):
        strg += decoded_data[i*40:(i+1)*40]
        
    return strg

def find_key(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.iteritems() if v == val][0]

logger = logging.getLogger('tce')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(message)s')

