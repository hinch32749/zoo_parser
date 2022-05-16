from django.shortcuts import render
from .models import Product


def index(request):
    p = Product.objects.all()
    context = {'p': p}
    return render(request, 'main_parser/index.html', context)
