from django.shortcuts import render
from .models import Product
from zoo_parser_conf.celery import hello


def index(request):
    p = Product.objects.all()
    a = hello.delay()
    print(a.status)
    context = {'p': p}
    return render(request, 'main_parser/index.html', context)
