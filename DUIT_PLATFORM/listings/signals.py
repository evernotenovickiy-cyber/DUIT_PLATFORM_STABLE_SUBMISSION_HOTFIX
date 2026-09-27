from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ServicePhoto


@receiver(post_delete, sender=ServicePhoto)
def delete_service_photo_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
