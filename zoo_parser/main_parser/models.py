from django.db import models


class Product(models.Model):
    site_url = models.CharField(max_length=100, verbose_name='Имя сайта')
    animal = models.CharField(max_length=100, verbose_name='Животное')
    category_of_product = models.CharField(max_length=100, verbose_name='Категория продукта')
    subcategory_of_product = models.CharField(max_length=100, verbose_name='Подкатегория?)?)')
    url_of_product = models.CharField(max_length=200, verbose_name='Ссылка на продукт')
    title = models.CharField(max_length=200, verbose_name='Название продукта')
    brand = models.CharField(max_length=70, verbose_name='Производитель')
    goods = models.CharField(max_length=70, verbose_name='Товар')
    price = models.CharField(max_length=70, verbose_name='Цена')
    price_online_pickup = models.CharField(max_length=70, verbose_name='Цена online-заказ самовывоз')
    price_online_delivery = models.CharField(max_length=70, verbose_name='Цена online-заказ на доставку')

    class Meta:
        verbose_name_plural = 'Товары'
        verbose_name = 'Товар'

    def __str__(self):
        return self.title


def lol():
    print("HEHE")
