from django.db import models


class Age(models.Model):
    name = models.CharField(max_length=50, verbose_name='Возраст')

    class Meta:
        verbose_name_plural = 'Возрасты'
        verbose_name = 'Возраст'

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=70, verbose_name='Размер')

    class Meta:
        verbose_name_plural = 'Размеры'
        verbose_name = 'Размер'

    def __str__(self):
        return self.name


class Specialty(models.Model):
    name = models.CharField(max_length=100, verbose_name='Особенность')

    class Meta:
        verbose_name_plural = 'Особенности'
        verbose_name = 'Особенность'

    def __str__(self):
        return self.name


class Tasty(models.Model):
    name = models.CharField(max_length=100, verbose_name='Вкус')

    class Meta:
        verbose_name_plural = 'Вкусы'
        verbose_name = 'Вкус'

    def __str__(self):
        return self.name


class TypeProduct(models.Model):
    name = models.CharField(max_length=100, verbose_name='Тип')

    class Meta:
        verbose_name_plural = 'Типы'
        verbose_name = 'Тип'

    def __str__(self):
        return self.name


class Length(models.Model):
    name = models.CharField(max_length=100, verbose_name='Длина')

    class Meta:
        verbose_name_plural = 'Длина'
        verbose_name = 'Длины'

    def __str__(self):
        return self.name


class Product(models.Model):
    site_url = models.CharField(max_length=100, verbose_name='Имя сайта')
    animal = models.CharField(max_length=100, verbose_name='Животное')
    category_of_product = models.CharField(max_length=100, verbose_name='Категория продукта')
    age = models.ForeignKey('Age', verbose_name='Возраст', blank=True, null=True, on_delete=models.DO_NOTHING)
    size = models.ForeignKey('Size', verbose_name='Размер', blank=True, null=True, on_delete=models.DO_NOTHING)
    type_product = models.ForeignKey('TypeProduct', verbose_name='Тип', blank=True, null=True, on_delete=models.DO_NOTHING)
    length = models.ForeignKey('Length', verbose_name='Длина', blank=True, null=True, on_delete=models.DO_NOTHING)
    specialties = models.ManyToManyField('Specialty', verbose_name='Особенность', default='нэту')
    tasties = models.ManyToManyField('Tasty', verbose_name='Вкус', default='нэту')
    url_of_product = models.CharField(max_length=200, verbose_name='Ссылка на продукт')
    title = models.CharField(max_length=200, verbose_name='Название продукта')
    brand = models.CharField(max_length=70, verbose_name='Производитель', blank=True, null=True)
    goods = models.CharField(max_length=70, verbose_name='Товар', default='Нет товара', blank=True, null=True)
    price = models.CharField(max_length=70, verbose_name='Цена', default='Нет цены', blank=True, null=True)
    price_online_pickup = models.CharField(max_length=70, verbose_name='Цена online-заказ самовывоз', blank=True, null=True)
    price_online_delivery = models.CharField(max_length=70, verbose_name='Цена online-заказ на доставку', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Товары'
        verbose_name = 'Товар'

    def __str__(self):
        return self.title


