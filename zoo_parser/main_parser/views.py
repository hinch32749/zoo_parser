from django.shortcuts import render, redirect
from django.views.generic import ListView
from django_tables2 import SingleTableView
from .models import Product, P
from .tables import ProductTable
from .tests import st


class ProductListView(SingleTableView):
    queryset = Product.objects.all()
    table_class = ProductTable
    template_name = 'main_parser/index.html'


def index(request):
    if request.method == "POST":
        p = Product.objects.all()
        for i in p:
            i.delete()
        # st()
        return redirect("new")
    return render(request, 'main_parser/tast.html')
