from django.apps import AppConfig


class BidsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bids'
    verbose_name = 'შეთავაზებები'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.bids.signals  # noqa: F401