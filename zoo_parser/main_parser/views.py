from django.shortcuts import render, redirect
from django.views.generic import ListView
from django_tables2 import SingleTableView
from .models import Product, Brand
from .tables import ProductTable
from .tests import st


class ProductListView(SingleTableView):
    # b = Brand.objects.filter(name="Happy Dog")
    p = Product.objects.filter(brand__name__icontains='Dog&Dog')
    queryset = p.exclude(price='нет в наличии')
    # queryset = Product.objects.all()
    table_class = ProductTable
    template_name = 'main_parser/index.html'


def index(request):
    # if request.method == "POST":
    #     p = Product.objects.all()
    #     for i in p:
    #         i.delete()
    #     # st()
    #     return redirect("new")
    return render(request, 'main_parser/tast.html')
