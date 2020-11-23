from django.conf import settings

from drinks.models import Drink


def factory_drink(**kwargs):
    d = {
        'name': 'テスト飲料',
        'price': 100,
    }
    d.update(kwargs)
    return Drink.objects.create(**d)
