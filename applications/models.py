from django.db import models
from services.models import Service

# Create your models here.

class Application(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"{self.name} - {self.service.name}"
