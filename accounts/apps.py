# In accounts/apps.py

from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # This line is the fix. It imports the signals (located in your models.py)
        # when the app is ready, ensuring they are properly connected.
        import accounts.models
