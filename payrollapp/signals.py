from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from activity_log.models import UserActivityLog

@receiver(post_save)
def log_object_creation(sender, instance, created, **kwargs):
    if created:
        UserActivityLog.objects.create(
            user=instance.created_by,  # Assuming you have a created_by field
            activity='Created {} instance with ID {}'.format(sender.__name__, instance.pk)
        )

@receiver(pre_save)
def log_object_update(sender, instance, **kwargs):
    # Retrieve the original instance from the database
    try:
        original_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return  # Object is being created, not updated

    # Compare the original instance with the new instance to detect changes
    # Here you can implement your own logic to determine which fields have changed
    # For simplicity, let's assume all fields are considered
    changes = []
    for field in instance._meta.fields:
        if getattr(original_instance, field.attname) != getattr(instance, field.attname):
            changes.append('{}: {} -> {}'.format(field.verbose_name, getattr(original_instance, field.attname), getattr(instance, field.attname)))

    if changes:
        UserActivityLog.objects.create(
            user=instance.updated_by,  # Assuming you have an updated_by field
            activity='Updated {} instance with ID {}. Changes: {}'.format(sender.__name__, instance.pk, ', '.join(changes))
        )
