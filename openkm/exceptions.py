class ExceptionParser(object):
    """
        Utitility class to parse returned exceptions from SUDS
        param e:  from except Exception, e:
       """

    def get_message(self, e):
        exception = self.get_raised_exception_class(e)
        return exception[0].message.__str__()

    def get_raised_exception_class_name(self, e):
        return e.fault.detail[0].__class__.__name__

    def get_raised_exception_class(self, e):
        return e.fault.detail


class ItemExistsException(Exception):
    pass


class IOException(Exception):
    pass


class UnsupportedMimeTypeException(Exception):
    pass


class FileSizeExceededException(Exception):
    pass


class VirusDetectedException(Exception):
    pass


class PathNotFoundException(Exception):
    pass


class ItemExistsException(Exception):
    pass


class AccessDeniedException(Exception):
    pass


class RepositoryException(Exception):
    pass