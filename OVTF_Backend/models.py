import uuid

from OVTF_Backend import settings
from datetime import datetime

from dateutil import tz
from django.db import models
from django.utils import timezone

class ActiveManager(models.Manager):
    """
    A basic db manager for get only active & undeleted items.
    """
    def only_actives(self):
        return super().get_queryset().filter(is_active=True, is_deleted=False)

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False, is_active=True)


class CoreModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Created At')
    created_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_created_by",
        verbose_name='Created By'
    )
    updated_at = models.DateTimeField(
        auto_now=True, null=True,
        blank=True, verbose_name='Updated At')
    updated_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_updated_by",
        verbose_name='Updated By'
    )
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    is_deleted = models.BooleanField(
        default=False, verbose_name='Is Deleted')
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Deleted At')
    deleted_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_deleted_by",
        verbose_name='Deleted By'
    )
    data = models.JSONField(null=True, blank=True, default=dict)

    objects = ActiveManager()

    all_objects = models.Manager()

    def __str__(self):
        return str(self.id)

    class Meta:
        abstract = True
        ordering = ["id"]

    def save(self, user=None, *args, **kwargs):
        if not self.id:
            if user:
                self.created_by = user
        else:
            if user:
                self.updated_by = user

        if kwargs.get('update_fields'):
            if 'updated_at' not in kwargs['update_fields']:
                kwargs['update_fields'] = list(kwargs['update_fields']) + ['updated_at']  # noqa

        super().save(*args, **kwargs)


    def mask_value(self, value, visible_char_length):
        val = str(value)[visible_char_length - 1:]
        return f"{val}********"

    def timestamp(self, value):
        if value:
            return int(value.timestamp())
        return value

    def epoch_millis(self, value):
        if value:
            return int(value.timestamp() * 1000)
        return value

    def from_timestamp(self, value):
        if value:
            return datetime.fromtimestamp(
                value, tz=tz.gettz(settings.TIME_ZONE))
        return value

    def delete(self):
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()
