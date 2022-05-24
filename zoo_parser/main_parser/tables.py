import django_tables2 as tables
from .models import Product


class ProductTable(tables.Table):
    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap.html"
        fields = ("animal", "category_of_product", "age", "title",
                  "goods", "price", "specialties", "tasties",
                  "size", "type_product", "length", )
