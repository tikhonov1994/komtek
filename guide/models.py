from django.db import models


class Guide(models.Model):
    name = models.CharField('Наименование', max_length=255, unique=False,
                            blank=True, null=True)
    short_name = models.CharField('Короткое наименование', max_length=63,
                                  unique=False, blank=True, null=True)
    description = models.TextField('Описание', unique=False,
                                   blank=True, null=True)
    version = models.CharField('Версия', max_length=63)
    start_date = models.DateField(
        'Дата начала действия справочника этой версии')

    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'
        indexes = [
            models.Index(fields=['version', 'start_date'])
        ]

    def __str__(self) -> str:
        return f'{self.short_name} version-{self.version}'


class GuideElement(models.Model):
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE,
                              related_name='elements')
    element_code = models.CharField('Код элемента', max_length=63,
                                    unique=False)
    value = models.CharField('Значение элемента', max_length=255,
                             unique=False)

    class Meta:
        verbose_name = 'Элемент справочника'
        verbose_name_plural = 'Элементы справочника'
        indexes = [
            models.Index(fields=['element_code', ])
        ]

    def __str__(self) -> str:
        return self.element_code
