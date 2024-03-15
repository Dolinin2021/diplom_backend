import os

from django.contrib.auth import get_user_model
from django.db import models, router
from django.conf import settings
from django.db.models.deletion import Collector

user = get_user_model()


def file_path(instance, filename):
    base_filename, file_extension = os.path.splitext(filename)
    return f'files/storages/{instance.user.id}/{base_filename}{file_extension}'


class File (models.Model):
    """Модель файлов"""

    title = models.CharField(
        'Имя файла',
        max_length=255,
        default='no title'
    )
    file = models.FileField(
        upload_to=file_path
    )
    share = models.UUIDField(
        unique=True,
        null=True,
        editable=True
    )
    file_size = models.PositiveIntegerField(
        'Размер файла',
        editable=False,
        null=True
    )
    date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    comment = models.CharField(
        'Комментарий к файлу',
        null=True,
        max_length=255,
    )
    url = models.URLField(
        'Ссылка на файл',
        null=True,
        max_length=1024,
    )
    user = models.ForeignKey(
        user,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    def save(self, *args, **kwargs):
        super(File, self).save()
        fullpath = os.path.join(settings.MEDIA_ROOT, str(self.file))
        self.file_size = os.path.getsize(fullpath)
        super(File, self).save()

    def delete(self, using=None, keep_parents=False):
        fullpath = os.path.join(settings.MEDIA_ROOT, str(self.file))
        try:
            os.remove(fullpath)
        except FileNotFoundError:
            ...
        if self.pk is None:
            raise ValueError(
                "%s object can't be deleted because its %s attribute is set "
                "to None." % (self._meta.object_name, self._meta.pk.attname)
            )
        using = using or router.db_for_write(self.__class__, instance=self)
        collector = Collector(using=using, origin=self)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'
