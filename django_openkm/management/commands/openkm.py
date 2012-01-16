from django.core.management.base import BaseCommand, CommandError

from django_openkm.sync import SyncFolderList
from django_openkm.utils import logger

class DummyDocument:
    path = ''

class Command(BaseCommand):
    help = """
    Updates the Django database with the document meta data from OpenKM

    args:
    construct_categories - dynamically creates all the categories on OpenKM from Django models
    """

    args = ('construct_categories', 'sync_local_folder_list')

    def handle(self, *args, **options):
        # handle arguments first
        if 'sync_local_folder_list' in args:
            self.sync_local_folder_list()
        else:
            logger.info("No arguments given")

    def sync_local_folder_list(self):
        """
        Updates the local database table of OpenKM folder metadata
        """
        folder_list = SyncFolderList()
        folder_list.execute()








