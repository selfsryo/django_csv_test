from itertools import islice

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from drinks import handle_csv
from drinks.models import Drink


def check_csv_size(value):
    """CSVファイルサイズチェック
    """
    if value.size > settings.CSV_FILE_SIZE_LIMIT:
        raise forms.ValidationError(f'ファイルサイズが大きすぎます。{settings.CSV_FILE_SIZE_LIMIT//1000//1000}MBより小さいサイズにしてください。')
    return value


class UploadCSVForm(forms.Form):
    """CSV一括登録用フォーム
    """
    allowed_extentions = ['csv']

    csv_file = forms.FileField(
        help_text = f'名称,価格の形式にしてください。<br/>例...コーヒー,300<br/>一度に{settings.CSV_ROW_LIMIT}行まで登録でき、それより大きい行は無視されます。',
        validators=[
            FileExtensionValidator(
                allowed_extensions=allowed_extentions,
                message='拡張子.csvのファイルを選択してください。'
            ),
            check_csv_size,
        ]
    )

    def clean_csv_file(self):
        """CSVを読み込んでバリデーションチェック
        """
        csv_file = self.cleaned_data['csv_file']
        self._reader = handle_csv.load_data(csv_file)

        try:
            handle_csv.validate_data(self._reader)
        except UnicodeDecodeError:
            raise ValidationError('文字コードをutf-8ににしてください。')
        csv_file.seek(0)

        return csv_file

    def save(self):
        """設定した件数分までのデータを一括登録
        """
        drinks = handle_csv.store_data(self._reader)
        # CSV_ROW_LIMITの値より大きな行番号のデータは無視される
        batch_size = settings.CSV_ROW_LIMIT
        batch = islice(drinks, batch_size)
        Drink.objects.bulk_create(batch, batch_size)
