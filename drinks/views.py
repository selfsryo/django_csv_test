import urllib

from django.http import HttpResponse
from django.shortcuts import redirect, render 

from drinks.forms import UploadCSVForm
from drinks.handle_csv import write_data
from drinks.models import Drink


def drink_list(request):
    """
    飲料データ一覧
    POSTされた場合CSV一括登録
    """
    drinks = Drink.objects.order_by('-created_at')
    form = UploadCSVForm()

    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('drinks:list')
            
    context = {
        'drinks': drinks,
        'form': form,
    }
    return render(request, 'drinks/list.html', context)


def drink_download(request):
    """飲料データをCSV出力
    """
    response = HttpResponse(content_type='text/csv')
    # ファイル名が日本語なのでutf-8でURLエンコード
    filename = urllib.parse.quote((u'飲料情報.csv').encode('utf-8'))

    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
    write_data(response)
    return response
