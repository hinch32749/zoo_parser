from django.shortcuts import render
from django.views.generic import ListView
from django_tables2 import SingleTableView
from .models import Product
from .tables import ProductTable


class ProductListView(SingleTableView):
    model = Product
    table_class = ProductTable
    template_name = 'main_parser/index.html'
