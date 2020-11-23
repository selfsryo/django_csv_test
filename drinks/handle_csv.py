import csv
import io

from django.core.exceptions import ValidationError

from drinks.models import Drink


def load_data(csv_file):
    """CSVを読み込んでテキストモードに変換
    """
    io_text = io.TextIOWrapper(csv_file, encoding='utf-8')
    return csv.reader(io_text)

def validate_data(reader):
    """読み込んだデータに誤りがないかチェック
    """
    for i, row in enumerate(reader):
        # 列数チェック
        if len(row) < 2:
            raise ValidationError(f'{i + 1}行目に不足している列があります。')
        elif 2 < len(row):
            raise ValidationError(f'{i + 1}行目に不要な列があります。')

        # 名前チェック
        if 255 < len(row[0]):
            raise ValidationError(f'{i + 1}行目の名称を255文字以内にしてください。')

        # 価格チェック
        try:
            price = int(row[1])
        except ValueError:
            raise ValidationError(f'{i + 1}行目の価格を数字にしてください。')
        if price < 1:
            raise ValidationError(f'{i + 1}行目の価格を1以上にしてください。')
        if price > 2147483647:
            raise ValidationError(f'{i + 1}行目の価格を2,147,483,647以下にしてください。')

def store_data(reader):
    """読み込んだデータをDrinkオブジェクトのリストにして返す
    """
    drinks = []

    for row in reader:
        drink = Drink(
            name=row[0],
            price=row[1],
        )
        drinks.append(drink)

    return drinks

def write_data(response):
    """DrinkオブジェクトをCSVに書き込み
    """
    writer = csv.writer(response)
    for drink in Drink.objects.all():
        writer.writerow([drink.name, drink.price])
