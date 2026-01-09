from django.apps import AppConfig


class PayrollappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payrollapp"

    def ready(self):
        import payrollapp.signals
