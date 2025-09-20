from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    verbose_name = 'PaisaBuddy Main'
    
    def ready(self):
        """
        Import signals when the app is ready
        """
        try:
            import main.signals  # noqa
        except ImportError:
            pass