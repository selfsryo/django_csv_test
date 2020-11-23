from django.db import models
from django.core import validators


class Drink(models.Model):
    """飲料マスタ
    """
    name = models.CharField('名前', max_length=255)
    price = models.PositiveIntegerField('価格', 
                                        validators=[
                                            validators.MinValueValidator(1),
                                            # IntegerFieldの最大値
                                            validators.MaxValueValidator(2147483647)
                                        ])
    created_at = models.DateTimeField('登録日時', auto_now_add=True)


    def __str__(self):
        return self.name
