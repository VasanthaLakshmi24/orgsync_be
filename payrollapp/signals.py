# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver
# from activity_log.models import ActivityLog
# from django.db.models import F
# from payrollapp.models import Employee, Department, Designation, Organization




# @receiver(post_save)
# def log_object_creation(sender, instance, created, **kwargs):
#     if created:
#         UserActivityLog.objects.create(
#             user=instance.created_by,  # Assuming you have a created_by field
#             activity='Created {} instance with ID {}'.format(sender.__name__, instance.pk)
#         )

# @receiver(pre_save)
# def log_object_update(sender, instance, **kwargs):
#     # Retrieve the original instance from the database
#     try:
#         original_instance = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         return  # Object is being created, not updated

#     # Compare the original instance with the new instance to detect changes
#     # Here you can implement your own logic to determine which fields have changed
#     # For simplicity, let's assume all fields are considered
#     changes = []
#     for field in instance._meta.fields:
#         if getattr(original_instance, field.attname) != getattr(instance, field.attname):
#             changes.append('{}: {} -> {}'.format(field.verbose_name, getattr(original_instance, field.attname), getattr(instance, field.attname)))

#     if changes:
#         UserActivityLog.objects.create(
#             user=instance.updated_by,  # Assuming you have an updated_by field
#             activity='Updated {} instance with ID {}. Changes: {}'.format(sender.__name__, instance.pk, ', '.join(changes))
#         )
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import F

from payrollapp.models import Employee, Department, Designation, Organization
from activity_log.models import ActivityLog


# -------------------------------
# 1️⃣ Audit logging
# -------------------------------

@receiver(post_save)
def log_object_creation(sender, instance, created, **kwargs):
    # Only log for payrollapp models
    if sender.__module__ != "payrollapp.models":
        return

    if created:
        user = getattr(instance, "created_by", None)
        ActivityLog.objects.create(
            user=user,
            action=f"Created {sender.__name__} (ID: {instance.pk})",
        )


@receiver(pre_save)
def log_object_update(sender, instance, **kwargs):
    if sender.__module__ != "payrollapp.models":
        return

    if not instance.pk:
        return  # new object, handled above

    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = []
    for field in instance._meta.fields:
        old = getattr(original, field.attname)
        new = getattr(instance, field.attname)
        if old != new:
            changes.append(f"{field.name}: {old} → {new}")

    if changes:
        user = getattr(instance, "updated_by", None)
        ActivityLog.objects.create(
            user=user,
            action=f"Updated {sender.__name__} (ID: {instance.pk}) | " + ", ".join(changes),
        )


# -------------------------------
# 2️⃣ Org version bump (REAL-TIME ENGINE)
# -------------------------------

def bump_org_version(org):
    Organization.objects.filter(id=org.id).update(
        org_version=F("org_version") + 1
    )


@receiver(post_save, sender=Employee)
@receiver(post_delete, sender=Employee)
@receiver(post_save, sender=Department)
@receiver(post_delete, sender=Department)
@receiver(post_save, sender=Designation)
@receiver(post_delete, sender=Designation)
def org_changed(sender, instance, **kwargs):
    if instance.parent:
        bump_org_version(instance.parent)
