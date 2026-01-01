from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import JobLog


@receiver(post_save, sender=JobLog)
def push_log_to_socket(sender, instance, created, **kwargs):
    if not created:
        return  # only push new log lines

    channel_layer = get_channel_layer()
    group_name = f"job_{instance.job_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_job_log",
            "timestamp": str(instance.timestamp),
            "message": instance.message
        }
    )
