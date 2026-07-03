from django.apps import AppConfig

class PackingConfig(AppConfig):
    name = 'packing'

    def ready(self):
        import packing.signals
