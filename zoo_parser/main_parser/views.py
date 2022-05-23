from django.shortcuts import render
from .models import Product
from zoo_parser_conf.celery import parser_ezoo


def index(request):
    p = Product.objects.all()
    parser_ezoo.delay()
    context = {'p': p}
    return render(request, 'main_parser/index.html', context)
