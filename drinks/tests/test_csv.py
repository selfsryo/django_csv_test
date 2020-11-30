import csv
import io
import tempfile
import urllib

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from drinks.models import Drink
from drinks.tests.factories import factory_drink


class TestCSVUpload(TestCase):
    """CSVアップロードのテスト
    """
    def setUp(self):
        self.url = reverse('drinks:list')

        self.fp = tempfile.NamedTemporaryFile(mode='r+', encoding='utf-8', suffix='.csv')
        self.test_csv = self.fp.name

    def tearDown(self):
        self.fp.close()

    def test_clean_csv_file(self):
        """正常系
        """
        with open(self.test_csv, mode='r+') as f:
            f.writelines([
                'ドリンク1,1\n',
                'ドリンク2,2147483647\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertRedirects(res, reverse('drinks:list'))
        self.assertEquals(Drink.objects.count(), 2)

        res = self.client.get(reverse('drinks:list'))
        drinks = res.context.get('drinks')
        self.assertEquals(drinks[0].name, 'ドリンク2')
        self.assertEquals(drinks[0].price, 2147483647)
        self.assertEquals(drinks[1].name, 'ドリンク1')
        self.assertEquals(drinks[1].price, 1)

    def test_invalid_extension(self):
        """拡張子のテスト
        """
        with tempfile.NamedTemporaryFile(mode='r+', encoding='utf-8', suffix='.txt') as txt_fp:
            with open(txt_fp.name, mode='r+') as f:
                f.write('ドリンク1,100\n',)
                f.seek(0)
                res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '拡張子.csvのファイルを選択してください。')

    def test_over_row_limit(self):
        """指定した行数までしか登録されないことをテスト
        """
        with open(self.test_csv, mode='r+') as f:
            for _ in range(settings.CSV_ROW_LIMIT + 1):
                f.write('ドリンク1,100\n',)
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertEquals(Drink.objects.count(), settings.CSV_ROW_LIMIT)

    def test_over_filesize(self):
        """ファイルサイズのテスト
        """
        with open(self.test_csv, mode='r+') as f:
            import os
            while os.path.getsize(f.name) < settings.CSV_FILE_SIZE_LIMIT:
                f.write('ドリンク1,100\n',)
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', f'ファイルサイズが大きすぎます。{settings.CSV_FILE_SIZE_LIMIT//1000//1000}MBより小さいサイズにしてください。')

    def test_too_long_name(self):
        """Drinkモデルのnameフィールド文字数上限のテスト
        """
        with open(self.test_csv, mode='r+') as f:
            too_long_name = ''
            for _ in range(256):
                too_long_name += '0'
            f.writelines([
                'ドリンク1,100\n',
                f'{too_long_name},200\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '2行目の名称を255文字以内にしてください。')

    def test_too_cheap_price(self):
        """Drinkモデルのpriceフィールド下限のテスト
        """
        with open(self.test_csv, mode='r+') as f:
            f.writelines([
                'ドリンク1,100\n',
                'ドリンク2,0\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '2行目の価格を1以上にしてください。')

    def test_too_expensive_price(self):
        """Drinkモデルのpriceフィールド上限のテスト
        """
        with open(self.test_csv, mode='r+') as f:
            f.writelines([
                'ドリンク1,100\n',
                'ドリンク2,2147483648\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '2行目の価格を2,147,483,647以下にしてください。')

    def test_invalid_price(self):
        """Drinkモデルのpriceフィールドの型テスト
        """
        with open(self.test_csv, mode='r+') as f:
            f.writelines([
                'ドリンク1,100\n',
                'ドリンク2,200円\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '2行目の価格を数字にしてください。')

    def test_over_column(self):
        """CSVの列に余剰がないかテスト
        """
        with open(self.test_csv, mode='r+') as f:
            f.writelines([
                'ドリンク1,100\n',
                'ドリンク2,200,1\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '2行目に不要な列があります。')

    def test_lack_of_column(self):
        """CSVの列に不足がないかテスト
        """
        with open(self.test_csv, mode='r+') as f:
            f.writelines([
                'ドリンク1,100\n',
                'ドリンク2\n',
            ])
            f.seek(0)
            res = self.client.post(self.url, {'csv_file': f})
        self.assertFormError(res, 'form', 'csv_file', '2行目に不足している列があります。')


class TestCSVDownload(TestCase):
    """CSVダウンロードのテスト
    """
    def setUp(self):
        self.url = reverse('drinks:download')
        self.drink1 = factory_drink(name='ドリンク1', price=100)
        self.drink2 = factory_drink(name='ドリンク2', price=200)

    def test_download_content(self):
        """正常系
        """
        res = self.client.get(self.url)
        content = res.content.decode('utf-8')
        io_str = io.StringIO(content)
        reader = csv.reader(io_str)

        rows = list(reader)
        row_drink1 = rows[0]
        row_drink2 = rows[1]

        self.assertEquals(row_drink1[0], 'ドリンク1')
        self.assertEquals(row_drink1[1], '100')
        self.assertEquals(row_drink2[0], 'ドリンク2')
        self.assertEquals(row_drink2[1], '200')

    def test_download_file_title(self):
        """downloadしたcsvのファイルタイトルが正しいかテスト
        """
        res = self.client.get(self.url)
        self.assertTrue(res.has_header('content-disposition'))

        attachment = res._headers['content-disposition'][1]
        self.assertIn('飲料情報.csv', urllib.parse.unquote(attachment))
