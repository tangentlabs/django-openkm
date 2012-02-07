import base64

import suds

"""
Some useful helper and decorator functions
"""
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

def get_category_from_path(path):
    """
    Document.get_properties returns Category path and uuid information, so doing this
    saves us making a second webservice call
    :param path: string
    :return list
    """
    parts = path.split('/')
    if 'categories' not in parts[1]:
        return []
    else:
        return parts[2:]

def replace_dict_key(dict, old_key, new_key):
    """
    Renames a dictionary key, keeping the value intact, by creating a new key with the original value
    and then deleting the old { key : value }
    """
    dict[new_key] = dict[old_key]
    del dict[old_key]
    return dict

def import_class(module_path, class_name):
    """
    Dynamically imports a class
    :module_path string: e.g. 'my_package.my_module'
    :fromlist string: the class name
    """
    mod = __import__(module_path, fromlist=[class_name])
    return getattr(mod, class_name)


