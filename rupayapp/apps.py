from django.apps import AppConfig


class RupayappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rupayapp'

    def ready(self):
        import rupayapp.signals  # garante que os signals do app sejam registrados