from django.conf import settings
import utils

class Settings:
    """
    Update the settings dictionary, replacing string path descriptors with the objects they point to
    This class runs once to update the settings and does not need to be instantiated by client code
    """
    def __init__(self):
        # ensure we only do this once
        if not hasattr(self, 'openkm'):
            self.__categories()
            self.__properties()
            self.openkm = True

    def __categories(self):
        for path_to_class in settings.OPENKM['categories'].keys():
            model_class = self.__get_object(path_to_class)
            settings.OPENKM['categories'] = utils.replace_dict_key(settings.OPENKM['categories'], path_to_class, model_class)

    def __properties(self):
        for property_group, local_metadata in settings.OPENKM['properties'].items():
            for metadata in local_metadata.values():
                if 'choices' in metadata and metadata['choices']:
                    path_to_class = metadata['choices']
                    metadata['choices'] = self.__get_object(path_to_class)

    def __get_object(self, path_to_class):
        class_name = self.__extract_class_name(path_to_class)
        module_path = self.__reconstruct_module_path(path_to_class)
        return utils.import_class(module_path, class_name)

    def __extract_class_name(self, path_to_class):
        return path_to_class.split('.')[-1:][0]

    def __reconstruct_module_path(self, path_to_class):
        return '.'.join(path_to_class.split('.')[:-1])

Settings()