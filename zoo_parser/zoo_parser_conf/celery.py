import os
import threading

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time
from celery import Celery

from celery.schedules import crontab

from zoo_parser_conf import settings

# TODO: сделать логику, если по фильтру нету товаров, чтобы не кидало исключение и не прекращалась работа парсера!!!

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zoo_parser_conf.settings')
app = Celery("zoo_parser_conf")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # sender.add_periodic_task(40 , parser_zootovary_dogs,
    #                          name='parser_dogs')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_zootovary_dogs,
                             name='parser_dogs')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_zootovary_cats,
                             name='parser_cats')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_zootovary_rodents,
                             name='parser_rodents')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_zootovary_fishes,
                             name='parser_fishes')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_zootovary_birds,
                             name='parser_birds')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_garfield,
                             name='parser_garfield')


@app.task
def parser_zootovary_dogs():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand

    dict_filters = {'возраст': 'age', 'размер': 'size', 'особенности': 'specialties',
                    'свойства': 'specialty', 'тип': 'type_product', 'длина': 'length',
                    'состав': 'tasties', 'вид животного': 'age', 'производитель': 'brand',
                    'производители': 'brand'}

    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    browser = webdriver.Chrome(service=s, options=op)
    try:
        time.sleep(3)
        url = "https://zootovary.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        time.sleep(3)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR,
                                                                                                   "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR,
                                                                                               "div.container_12.menu-cat-top").find_elements(
            By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        dict_ = {}
        for i, j in zip(name_of_animals, name_of_categories):
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            if i.get_attribute("text").lower().strip() == "собаки":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text").lower().strip()
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                        assert "миск" not in cat.get_attribute("text").lower()
                        op = webdriver.ChromeOptions()
                        op.add_argument('--headless')
                        op.add_argument('window-size=1920,1080')
                        new_browser = webdriver.Chrome(service=s, options=op)
                        new_browser.get(cat.get_attribute("href"))
                        new_browser.implicitly_wait(5)
                        try:
                            products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                            time.sleep(3)
                            for page in products_page:
                                print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)  ########
                                # if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower().strip() == 'производитель' \
                                #         or page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower().strip() == 'производители':
                                #     continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR,
                                                                  "div.item-name").text.lower().strip():
                                            dict_[dict_filters[i]] = option.text.lower().strip()
                                        else:
                                            try:
                                                dict_.pop(page.find_element(By.CSS_SELECTOR,
                                                                            "div.item-name").text.lower().strip())
                                            except Exception as ex:
                                                pass
                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(3)
                                    got_price = True
                                    while got_price:
                                        products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                            .until(EC.presence_of_all_elements_located(
                                            (By.CSS_SELECTOR, "div.product-item.clearfix")))
                                        for product in products:
                                            dict_["image"] = product.find_element(by=By.TAG_NAME,
                                                                                  value="img").get_attribute("src")
                                            url_of_product = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="div.product-img"). \
                                                find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                            dict_["url_of_product"] = url_of_product
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="h2").text.strip()
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            for i in range(0, pare * 2, 2):
                                                if pr == '':
                                                    dict_["goods"] = list_price[2 + i]
                                                    dict_["price"] = list_price[3 + i]
                                                else:
                                                    dict_["goods"] = None
                                                    dict_["price"] = pr
                                                p = Product.objects.get_or_create(title=dict_["title"],
                                                                                  price=dict_["price"])[0]
                                                try:
                                                    age = Age.objects.get_or_create(name=dict_["age"])[0]
                                                except:
                                                    pass
                                                try:
                                                    brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                                except:
                                                    pass
                                                try:
                                                    size = Size.objects.get_or_create(name=dict_["size"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[
                                                        0]
                                                except:
                                                    pass
                                                try:
                                                    length = Length.objects.get_or_create(name=dict_["length"])[0]
                                                except:
                                                    pass
                                                try:
                                                    specialties = \
                                                        Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                                except:
                                                    pass
                                                p.site_url = dict_["site_url"]
                                                p.animal = dict_["animal"]
                                                p.category_of_product = dict_["category_of_product"]
                                                p.url_of_product = dict_["url_of_product"]
                                                p.title = dict_["title"]
                                                try:
                                                    p.goods = dict_["goods"]
                                                except:
                                                    pass
                                                try:
                                                    p.price = dict_["price"]
                                                except:
                                                    pass
                                                try:
                                                    p.age = age
                                                except:
                                                    pass
                                                try:
                                                    p.brand = brand
                                                except:
                                                    pass
                                                try:
                                                    p.size = size
                                                except:
                                                    pass
                                                try:
                                                    p.type_product = tp
                                                except:
                                                    pass
                                                try:
                                                    p.length = length
                                                except:
                                                    pass
                                                try:
                                                    p.specialties.add(specialties)
                                                except:
                                                    pass
                                                try:
                                                    p.tasties.add(tasties)
                                                except:
                                                    pass
                                                p.save()
                                                print("Saved")
                                            print('================')
                                        time.sleep(1)

                                        try:
                                            paginator = WebDriverWait(new_browser, 10,
                                                                      ignored_exceptions=ignored_exceptions) \
                                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                            paginator.click()
                                            time.sleep(3)
                                            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                        except:
                                            print("Закончились страницы")
                                            break

                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(2)
                        except:
                            print("No FILTERS")
                            got_price = True
                            while got_price:
                                products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                for product in products:
                                    dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute(
                                        "src")
                                    url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img"). \
                                        find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                    dict_["url_of_product"] = url_of_product
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text.strip()
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    for i in range(0, pare * 2, 2):
                                        if pr == '':
                                            dict_["goods"] = list_price[2 + i]
                                            dict_["price"] = list_price[3 + i]
                                        else:
                                            dict_["goods"] = None
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            age = Age.objects.get_or_create(name=dict_["age"])[0]
                                        except:
                                            pass
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except:
                                            pass
                                        try:
                                            size = Size.objects.get_or_create(name=dict_["size"])[0]
                                        except:
                                            pass
                                        try:
                                            tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[0]
                                        except:
                                            pass
                                        try:
                                            length = Length.objects.get_or_create(name=dict_["length"])[0]
                                        except:
                                            pass
                                        try:
                                            specialties = Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                        except:
                                            pass
                                        try:
                                            tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                        except:
                                            pass
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        try:
                                            p.goods = dict_["goods"]
                                        except:
                                            pass
                                        try:
                                            p.price = dict_["price"]
                                        except:
                                            pass
                                        try:
                                            p.age = age
                                        except:
                                            pass
                                        try:
                                            p.brand = brand
                                        except:
                                            pass
                                        try:
                                            p.size = size
                                        except:
                                            pass
                                        try:
                                            p.type_product = tp
                                        except:
                                            pass
                                        try:
                                            p.length = length
                                        except:
                                            pass
                                        try:
                                            p.specialties.add(specialties)
                                        except:
                                            pass
                                        try:
                                            p.tasties.add(tasties)
                                        except:
                                            pass
                                        p.save()
                                        print("Saved")
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except:
                                    print("Закончились страницы")
                                    break

                        finally:
                            new_browser.close()
    except:
        print("BAD CONNECTION")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_cats():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand

    dict_filters = {'возраст': 'age', 'размер': 'size', 'особенности': 'specialties',
                    'свойства': 'specialty', 'тип': 'type_product', 'длина': 'length',
                    'состав': 'tasties', 'вид животного': 'age'}
    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    browser = webdriver.Chrome(service=s, options=op)
    try:
        time.sleep(3)
        url = "https://zootovary.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        time.sleep(3)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR,
                                                                                                   "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR,
                                                                                               "div.container_12.menu-cat-top").find_elements(
            By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        dict_ = {}
        for i, j in zip(name_of_animals, name_of_categories):
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            if i.get_attribute("text").lower().strip() == "кошки":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                        assert "наполнит" not in cat.get_attribute("text").lower()
                        op = webdriver.ChromeOptions()
                        op.add_argument('--headless')
                        op.add_argument('window-size=1920,1080')
                        new_browser = webdriver.Chrome(service=s, options=op)
                        new_browser.get(cat.get_attribute("href"))
                        new_browser.implicitly_wait(5)
                        try:
                            products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                            time.sleep(3)
                            for page in products_page:
                                print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)  ########
                                # if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                #     continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text.lower().srtip()
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR,
                                                                      "div.item-name").text.lower().strip())
                                            except Exception as ex:
                                                pass
                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(3)
                                    got_price = True
                                    while got_price:
                                        products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                            .until(EC.presence_of_all_elements_located(
                                            (By.CSS_SELECTOR, "div.product-item.clearfix")))
                                        for product in products:
                                            dict_["image"] = product.find_element(by=By.TAG_NAME,
                                                                                  value="img").get_attribute("src")
                                            url_of_product = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="div.product-img"). \
                                                find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                            dict_["url_of_product"] = url_of_product
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="h2").text.strip()
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            for i in range(0, pare * 2, 2):
                                                if pr == '':
                                                    dict_["goods"] = list_price[2 + i]
                                                    dict_["price"] = list_price[3 + i]
                                                else:
                                                    dict_["goods"] = None
                                                    dict_["price"] = pr
                                                p = Product.objects.get_or_create(title=dict_["title"],
                                                                                  price=dict_["price"])[0]
                                                try:
                                                    age = Age.objects.get_or_create(name=dict_["age"])[0]
                                                except:
                                                    pass
                                                try:
                                                    brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                                except:
                                                    pass
                                                try:
                                                    size = Size.objects.get_or_create(name=dict_["size"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[
                                                        0]
                                                except:
                                                    pass
                                                try:
                                                    length = Length.objects.get_or_create(name=dict_["length"])[0]
                                                except:
                                                    pass
                                                try:
                                                    specialties = \
                                                        Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                                except:
                                                    pass
                                                p.site_url = dict_["site_url"]
                                                p.animal = dict_["animal"]
                                                p.category_of_product = dict_["category_of_product"]
                                                p.url_of_product = dict_["url_of_product"]
                                                p.title = dict_["title"]
                                                try:
                                                    p.goods = dict_["goods"]
                                                except:
                                                    pass
                                                try:
                                                    p.price = dict_["price"]
                                                except:
                                                    pass
                                                try:
                                                    p.age = age
                                                except:
                                                    pass
                                                try:
                                                    p.brand = brand
                                                except:
                                                    pass
                                                try:
                                                    p.size = size
                                                except:
                                                    pass
                                                try:
                                                    p.type_product = tp
                                                except:
                                                    pass
                                                try:
                                                    p.length = length
                                                except:
                                                    pass
                                                try:
                                                    p.specialties.add(specialties)
                                                except:
                                                    pass
                                                try:
                                                    p.tasties.add(tasties)
                                                except:
                                                    pass
                                                p.save()
                                                print("Saved")
                                            print('================')
                                        time.sleep(1)

                                        try:
                                            paginator = WebDriverWait(new_browser, 10,
                                                                      ignored_exceptions=ignored_exceptions) \
                                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                            paginator.click()
                                            time.sleep(3)
                                            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                        except:
                                            print("Закончились страницы")
                                            break

                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(2)
                        except:
                            print("No FILTERS")
                            got_price = True
                            while got_price:
                                products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                for product in products:
                                    dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute(
                                        "src")
                                    url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img"). \
                                        find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                    dict_["url_of_product"] = url_of_product
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text.strip()
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    for i in range(0, pare * 2, 2):
                                        if pr == '':
                                            dict_["goods"] = list_price[2 + i]
                                            dict_["price"] = list_price[3 + i]
                                        else:
                                            dict_["goods"] = None
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            age = Age.objects.get_or_create(name=dict_["age"])[0]
                                        except:
                                            pass
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except:
                                            pass
                                        try:
                                            size = Size.objects.get_or_create(name=dict_["size"])[0]
                                        except:
                                            pass
                                        try:
                                            tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[0]
                                        except:
                                            pass
                                        try:
                                            length = Length.objects.get_or_create(name=dict_["length"])[0]
                                        except:
                                            pass
                                        try:
                                            specialties = Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                        except:
                                            pass
                                        try:
                                            tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                        except:
                                            pass
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        try:
                                            p.goods = dict_["goods"]
                                        except:
                                            pass
                                        try:
                                            p.price = dict_["price"]
                                        except:
                                            pass
                                        try:
                                            p.age = age
                                        except:
                                            pass
                                        try:
                                            p.brand = brand
                                        except:
                                            pass
                                        try:
                                            p.size = size
                                        except:
                                            pass
                                        try:
                                            p.type_product = tp
                                        except:
                                            pass
                                        try:
                                            p.length = length
                                        except:
                                            pass
                                        try:
                                            p.specialties.add(specialties)
                                        except:
                                            pass
                                        try:
                                            p.tasties.add(tasties)
                                        except:
                                            pass
                                        p.save()
                                        print("Saved")
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except:
                                    print("Закончились страницы")
                                    break

                        finally:
                            new_browser.close()
    except:
        print("BAD CONNECTION")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_birds():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand

    dict_filters = {'возраст': 'age', 'размер': 'size', 'особенности': 'specialties',
                    'свойства': 'specialty', 'тип': 'type_product', 'длина': 'length',
                    'состав': 'tasties', 'вид животного': 'age'}
    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    browser = webdriver.Chrome(service=s, options=op)
    try:
        time.sleep(3)
        url = "https://zootovary.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        time.sleep(3)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR,
                                                                                                   "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR,
                                                                                               "div.container_12.menu-cat-top").find_elements(
            By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        dict_ = {}
        for i, j in zip(name_of_animals, name_of_categories):
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            if i.get_attribute("text").lower().strip() == "птицы":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                        assert "поилк" not in cat.get_attribute("text").lower()
                        op = webdriver.ChromeOptions()
                        op.add_argument('--headless')
                        op.add_argument('window-size=1920,1080')
                        new_browser = webdriver.Chrome(service=s, options=op)
                        new_browser.get(cat.get_attribute("href"))
                        new_browser.implicitly_wait(5)
                        try:
                            products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                            time.sleep(3)
                            for page in products_page:
                                print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)  ########
                                # if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                #     continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text.lower().strip()
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR,
                                                                      "div.item-name").text.lower().strip())
                                            except Exception as ex:
                                                pass
                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(3)
                                    got_price = True
                                    while got_price:
                                        products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                            .until(EC.presence_of_all_elements_located(
                                            (By.CSS_SELECTOR, "div.product-item.clearfix")))
                                        for product in products:
                                            dict_["image"] = product.find_element(by=By.TAG_NAME,
                                                                                  value="img").get_attribute("src")
                                            url_of_product = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="div.product-img"). \
                                                find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                            dict_["url_of_product"] = url_of_product
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="h2").text.strip()
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            for i in range(0, pare * 2, 2):
                                                if pr == '':
                                                    dict_["goods"] = list_price[2 + i]
                                                    dict_["price"] = list_price[3 + i]
                                                else:
                                                    dict_["goods"] = None
                                                    dict_["price"] = pr
                                                p = Product.objects.get_or_create(title=dict_["title"],
                                                                                  price=dict_["price"])[0]
                                                try:
                                                    age = Age.objects.get_or_create(name=dict_["age"])[0]
                                                except:
                                                    pass
                                                try:
                                                    brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                                except:
                                                    pass
                                                try:
                                                    size = Size.objects.get_or_create(name=dict_["size"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[
                                                        0]
                                                except:
                                                    pass
                                                try:
                                                    length = Length.objects.get_or_create(name=dict_["length"])[0]
                                                except:
                                                    pass
                                                try:
                                                    specialties = \
                                                        Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                                except:
                                                    pass
                                                p.site_url = dict_["site_url"]
                                                p.animal = dict_["animal"]
                                                p.category_of_product = dict_["category_of_product"]
                                                p.url_of_product = dict_["url_of_product"]
                                                p.title = dict_["title"]
                                                try:
                                                    p.goods = dict_["goods"]
                                                except:
                                                    pass
                                                try:
                                                    p.price = dict_["price"]
                                                except:
                                                    pass
                                                try:
                                                    p.age = age
                                                except:
                                                    pass
                                                try:
                                                    p.brand = brand
                                                except:
                                                    pass
                                                try:
                                                    p.size = size
                                                except:
                                                    pass
                                                try:
                                                    p.type_product = tp
                                                except:
                                                    pass
                                                try:
                                                    p.length = length
                                                except:
                                                    pass
                                                try:
                                                    p.specialties.add(specialties)
                                                except:
                                                    pass
                                                try:
                                                    p.tasties.add(tasties)
                                                except:
                                                    pass
                                                p.save()
                                                print("Saved")
                                            print('================')
                                        time.sleep(1)

                                        try:
                                            paginator = WebDriverWait(new_browser, 10,
                                                                      ignored_exceptions=ignored_exceptions) \
                                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                            paginator.click()
                                            time.sleep(3)
                                            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                        except:
                                            print("Закончились страницы")
                                            break

                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(2)
                        except:
                            print("No FILTERS")
                            got_price = True
                            while got_price:
                                products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                for product in products:
                                    dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute(
                                        "src")
                                    url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img"). \
                                        find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                    dict_["url_of_product"] = url_of_product
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text.strip()
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    for i in range(0, pare * 2, 2):
                                        if pr == '':
                                            dict_["goods"] = list_price[2 + i]
                                            dict_["price"] = list_price[3 + i]
                                        else:
                                            dict_["goods"] = None
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            age = Age.objects.get_or_create(name=dict_["age"])[0]
                                        except:
                                            pass
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except:
                                            pass
                                        try:
                                            size = Size.objects.get_or_create(name=dict_["size"])[0]
                                        except:
                                            pass
                                        try:
                                            tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[0]
                                        except:
                                            pass
                                        try:
                                            length = Length.objects.get_or_create(name=dict_["length"])[0]
                                        except:
                                            pass
                                        try:
                                            specialties = Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                        except:
                                            pass
                                        try:
                                            tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                        except:
                                            pass
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        try:
                                            p.goods = dict_["goods"]
                                        except:
                                            pass
                                        try:
                                            p.price = dict_["price"]
                                        except:
                                            pass
                                        try:
                                            p.age = age
                                        except:
                                            pass
                                        try:
                                            p.brand = brand
                                        except:
                                            pass
                                        try:
                                            p.size = size
                                        except:
                                            pass
                                        try:
                                            p.type_product = tp
                                        except:
                                            pass
                                        try:
                                            p.length = length
                                        except:
                                            pass
                                        try:
                                            p.specialties.add(specialties)
                                        except:
                                            pass
                                        try:
                                            p.tasties.add(tasties)
                                        except:
                                            pass
                                        p.save()
                                        print("Saved")
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except:
                                    print("Закончились страницы")
                                    break

                        finally:
                            new_browser.close()
    except:
        print("BAD CONNECTION")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_rodents():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand

    dict_filters = {'возраст': 'age', 'размер': 'size', 'особенности': 'specialties',
                    'свойства': 'specialty', 'тип': 'type_product', 'длина': 'length',
                    'состав': 'tasties', 'вид животного': 'age'}
    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    browser = webdriver.Chrome(service=s, options=op)
    try:
        time.sleep(3)
        url = "https://zootovary.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        time.sleep(3)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR,
                                                                                                   "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR,
                                                                                               "div.container_12.menu-cat-top").find_elements(
            By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        dict_ = {}
        for i, j in zip(name_of_animals, name_of_categories):
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            if i.get_attribute("text").lower().strip() == "грызуны":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                        assert "миск" not in cat.get_attribute("text").lower()
                        op = webdriver.ChromeOptions()
                        op.add_argument('--headless')
                        op.add_argument('window-size=1920,1080')
                        new_browser = webdriver.Chrome(service=s, options=op)
                        new_browser.get(cat.get_attribute("href"))
                        new_browser.implicitly_wait(5)
                        try:
                            products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                            time.sleep(3)
                            for page in products_page:
                                print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)  ########
                                # if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                #     continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text.lower().strip()
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR,
                                                                      "div.item-name").text.lower().strip())
                                            except Exception as ex:
                                                pass
                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(3)
                                    got_price = True
                                    while got_price:
                                        products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                            .until(EC.presence_of_all_elements_located(
                                            (By.CSS_SELECTOR, "div.product-item.clearfix")))
                                        for product in products:
                                            dict_["image"] = product.find_element(by=By.TAG_NAME,
                                                                                  value="img").get_attribute("src")
                                            url_of_product = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="div.product-img"). \
                                                find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                            dict_["url_of_product"] = url_of_product
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="h2").text.strip()
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            for i in range(0, pare * 2, 2):
                                                if pr == '':
                                                    dict_["goods"] = list_price[2 + i]
                                                    dict_["price"] = list_price[3 + i]
                                                else:
                                                    dict_["goods"] = None
                                                    dict_["price"] = pr
                                                p = Product.objects.get_or_create(title=dict_["title"],
                                                                                  price=dict_["price"])[0]
                                                try:
                                                    age = Age.objects.get_or_create(name=dict_["age"])[0]
                                                except:
                                                    pass
                                                try:
                                                    brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                                except:
                                                    pass
                                                try:
                                                    size = Size.objects.get_or_create(name=dict_["size"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[
                                                        0]
                                                except:
                                                    pass
                                                try:
                                                    length = Length.objects.get_or_create(name=dict_["length"])[0]
                                                except:
                                                    pass
                                                try:
                                                    specialties = \
                                                        Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                                except:
                                                    pass
                                                p.site_url = dict_["site_url"]
                                                p.animal = dict_["animal"]
                                                p.category_of_product = dict_["category_of_product"]
                                                p.url_of_product = dict_["url_of_product"]
                                                p.title = dict_["title"]
                                                try:
                                                    p.goods = dict_["goods"]
                                                except:
                                                    pass
                                                try:
                                                    p.price = dict_["price"]
                                                except:
                                                    pass
                                                try:
                                                    p.age = age
                                                except:
                                                    pass
                                                try:
                                                    p.brand = brand
                                                except:
                                                    pass
                                                try:
                                                    p.size = size
                                                except:
                                                    pass
                                                try:
                                                    p.type_product = tp
                                                except:
                                                    pass
                                                try:
                                                    p.length = length
                                                except:
                                                    pass
                                                try:
                                                    p.specialties.add(specialties)
                                                except:
                                                    pass
                                                try:
                                                    p.tasties.add(tasties)
                                                except:
                                                    pass
                                                p.save()
                                                print("Saved")
                                                print(dict_)
                                            print('================')
                                        time.sleep(1)

                                        try:
                                            paginator = WebDriverWait(new_browser, 6,
                                                                      ignored_exceptions=ignored_exceptions) \
                                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                            paginator.click()
                                            time.sleep(3)
                                            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                        except:
                                            print("Закончились страницы")
                                            break

                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(2)
                        except:
                            print("No FILTERS")
                            got_price = True
                            while got_price:
                                products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                for product in products:
                                    dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute(
                                        "src")
                                    url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img"). \
                                        find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                    dict_["url_of_product"] = url_of_product
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text.strip()
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)
                                    pare = len(list_price[2:]) // 2
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    for i in range(0, pare * 2, 2):
                                        if pr == '':
                                            dict_["goods"] = list_price[2 + i]
                                            dict_["price"] = list_price[3 + i]
                                        else:
                                            dict_["goods"] = None
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            age = Age.objects.get_or_create(name=dict_["age"])[0]
                                        except:
                                            pass
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except:
                                            pass
                                        try:
                                            size = Size.objects.get_or_create(name=dict_["size"])[0]
                                        except:
                                            pass
                                        try:
                                            tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[0]
                                        except:
                                            pass
                                        try:
                                            length = Length.objects.get_or_create(name=dict_["length"])[0]
                                        except:
                                            pass
                                        try:
                                            specialties = Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                        except:
                                            pass
                                        try:
                                            tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                        except:
                                            pass
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        try:
                                            p.goods = dict_["goods"]
                                        except:
                                            pass
                                        try:
                                            p.price = dict_["price"]
                                        except:
                                            pass
                                        try:
                                            p.age = age
                                        except:
                                            pass
                                        try:
                                            p.brand = brand
                                        except:
                                            pass
                                        try:
                                            p.size = size
                                        except:
                                            pass
                                        try:
                                            p.type_product = tp
                                        except:
                                            pass
                                        try:
                                            p.length = length
                                        except:
                                            pass
                                        try:
                                            p.specialties.add(specialties)
                                        except:
                                            pass
                                        try:
                                            p.tasties.add(tasties)
                                        except:
                                            pass
                                        p.save()
                                        print("Saved")
                                        print(dict_)
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except:
                                    print("Закончились страницы")
                                    break

                        finally:
                            new_browser.close()
    except:
        print("BAD CONNECTION")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_fishes():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand

    dict_filters = {'возраст': 'age', 'размер': 'size', 'особенности': 'specialties',
                    'свойства': 'specialty', 'тип': 'type_product', 'длина': 'length',
                    'состав': 'tasties', 'вид животного': 'age'}
    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    browser = webdriver.Chrome(service=s, options=op)
    try:
        time.sleep(3)
        url = "https://zootovary.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        time.sleep(3)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR,
                                                                                                   "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR,
                                                                                               "div.container_12.menu-cat-top").find_elements(
            By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        for i, j in zip(name_of_animals, name_of_categories):
            dict_ = {}
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            if i.get_attribute("text").lower().strip() == "рыбки":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                        # assert "на чем прекратить поиск" not in cat.get_attribute("text").lower()
                        op = webdriver.ChromeOptions()
                        op.add_argument('--headless')
                        op.add_argument('window-size=1920,1080')
                        new_browser = webdriver.Chrome(service=s, options=op)
                        new_browser.get(cat.get_attribute("href"))
                        new_browser.implicitly_wait(5)
                        try:
                            products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                            time.sleep(3)
                            for page in products_page:
                                print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)  ########
                                # if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                #     continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text.lower().strip()
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR,
                                                                      "div.item-name").text.lower().strip())
                                            except Exception as ex:
                                                pass
                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(3)
                                    got_price = True
                                    while got_price:
                                        products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                            .until(EC.presence_of_all_elements_located(
                                            (By.CSS_SELECTOR, "div.product-item.clearfix")))
                                        for product in products:
                                            dict_["image"] = product.find_element(by=By.TAG_NAME,
                                                                                  value="img").get_attribute("src")
                                            url_of_product = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="div.product-img"). \
                                                find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                            dict_["url_of_product"] = url_of_product
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR,
                                                                                  value="h2").text.strip()
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            for i in range(0, pare * 2, 2):
                                                if pr == '':
                                                    dict_["goods"] = list_price[2 + i]
                                                    dict_["price"] = list_price[3 + i]
                                                else:
                                                    dict_["goods"] = None
                                                    dict_["price"] = pr
                                                p = Product.objects.get_or_create(title=dict_["title"],
                                                                                  price=dict_["price"])[0]
                                                try:
                                                    age = Age.objects.get_or_create(name=dict_["age"])[0]
                                                except:
                                                    pass
                                                try:
                                                    brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                                except:
                                                    pass
                                                try:
                                                    size = Size.objects.get_or_create(name=dict_["size"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[
                                                        0]
                                                except:
                                                    pass
                                                try:
                                                    length = Length.objects.get_or_create(name=dict_["length"])[0]
                                                except:
                                                    pass
                                                try:
                                                    specialties = \
                                                        Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                                except:
                                                    pass
                                                try:
                                                    tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                                except:
                                                    pass
                                                p.site_url = dict_["site_url"]
                                                p.animal = dict_["animal"]
                                                p.category_of_product = dict_["category_of_product"]
                                                p.url_of_product = dict_["url_of_product"]
                                                p.title = dict_["title"]
                                                try:
                                                    p.goods = dict_["goods"]
                                                except:
                                                    pass
                                                try:
                                                    p.price = dict_["price"]
                                                except:
                                                    pass
                                                try:
                                                    p.age = age
                                                except:
                                                    pass
                                                try:
                                                    p.brand = brand
                                                except:
                                                    pass
                                                try:
                                                    p.size = size
                                                except:
                                                    pass
                                                try:
                                                    p.type_product = tp
                                                except:
                                                    pass
                                                try:
                                                    p.length = length
                                                except:
                                                    pass
                                                try:
                                                    p.specialties.add(specialties)
                                                except:
                                                    pass
                                                try:
                                                    p.tasties.add(tasties)
                                                except:
                                                    pass
                                                p.save()
                                                print("Saved")
                                            print('================')
                                        time.sleep(1)

                                        try:
                                            paginator = WebDriverWait(new_browser, 10,
                                                                      ignored_exceptions=ignored_exceptions) \
                                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                            paginator.click()
                                            time.sleep(3)
                                            print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                        except:
                                            print("Закончились страницы")
                                            break

                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(2)
                        except:
                            print("No FILTERS")
                            got_price = True
                            while got_price:
                                products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                for product in products:
                                    dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute(
                                        "src")
                                    url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img"). \
                                        find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                    dict_["url_of_product"] = url_of_product
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text.strip()
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    for i in range(0, pare * 2, 2):
                                        if pr == '':
                                            dict_["goods"] = list_price[2 + i]
                                            dict_["price"] = list_price[3 + i]
                                        else:
                                            dict_["goods"] = None
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            age = Age.objects.get_or_create(name=dict_["age"])[0]
                                        except:
                                            pass
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except:
                                            pass
                                        try:
                                            size = Size.objects.get_or_create(name=dict_["size"])[0]
                                        except:
                                            pass
                                        try:
                                            tp = TypeProduct.objects.get_or_create(name=dict_["type_product"])[0]
                                        except:
                                            pass
                                        try:
                                            length = Length.objects.get_or_create(name=dict_["length"])[0]
                                        except:
                                            pass
                                        try:
                                            specialties = Specialty.objects.get_or_create(name=dict_["specialties"])[0]
                                        except:
                                            pass
                                        try:
                                            tasties = Tasty.objects.get_or_create(name=dict_["tasties"])[0]
                                        except:
                                            pass
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        try:
                                            p.goods = dict_["goods"]
                                        except:
                                            pass
                                        try:
                                            p.price = dict_["price"]
                                        except:
                                            pass
                                        try:
                                            p.age = age
                                        except:
                                            pass
                                        try:
                                            p.brand = brand
                                        except:
                                            pass
                                        try:
                                            p.size = size
                                        except:
                                            pass
                                        try:
                                            p.type_product = tp
                                        except:
                                            pass
                                        try:
                                            p.length = length
                                        except:
                                            pass
                                        try:
                                            p.specialties.add(specialties)
                                        except:
                                            pass
                                        try:
                                            p.tasties.add(tasties)
                                        except:
                                            pass
                                        p.save()
                                        print("Saved")
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except:
                                    print("Закончились страницы")
                                    break

                        finally:
                            new_browser.close()
    except:
        print("BAD CONNECTION")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_garfield_cats():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait
    try:
        s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        # op.add_argument('window-size=1920,1080')
        browser = webdriver.Chrome(service=s, options=op)
        url = "https://garfield.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.header-nav").find_elements(By.CSS_SELECTOR,
                                                                                                   "a.header-nav__link")

        for i in name_of_categories[:-3]:
            dict_ = {}
            print(f'\t\t{i.text} -- {i.get_attribute("href")}')
            print("-------------------------------------------------------")
            animal = i.text.lower().strip()
            dict_["animal"] = animal
            animal_browser = webdriver.Chrome(service=s, options=op)
            animal_browser.get(i.get_attribute("href"))
            cop = WebDriverWait(animal_browser, 10, ignored_exceptions=ignored_exceptions) \
                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.bx_catalog_tile")))
            categories_of_product = WebDriverWait(cop, 10, ignored_exceptions=ignored_exceptions) \
                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "catalog_section_snipet")))
            for c in categories_of_product[:-2]:
                category = WebDriverWait(c, 10, ignored_exceptions=ignored_exceptions) \
                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.bx_catalog_tile_title")))
                category_of_product = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                    .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                if category_of_product.text.lower() == 'сухие корма' \
                        or category_of_product.text.lower().strip() == 'консервы' \
                        or category_of_product.text.lower().strip() == 'лакомства' \
                        or category_of_product.text.lower().strip() == 'витамины и добавки':
                    print(f'{category_of_product.text} -- {category_of_product.get_attribute("href")}')
                    print("=========================================================================")
                    cop = category_of_product.text.lower().strip()
                    dict_["category_of_product"] = cop
                    category_browser = webdriver.Chrome(service=s, options=op)
                    category_browser.get(category_of_product.get_attribute("href"))
                    try:
                        paginator = WebDriverWait(category_browser, 7, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.bx_pagination_page")))
                        pages = WebDriverWait(paginator, 7, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                        last_page = WebDriverWait(pages[-2], 7, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        print(f'Количество страниц: {last_page.get_attribute("text")}')
                        futures = []
                        with ThreadPoolExecutor() as executor:
                            for page in range(1, int(last_page.get_attribute("text")) + 1):
                                futures.append(
                                    executor.submit(thread_parser, page, animal, cop)
                                )
                        wait(futures)
                            # thread = threading.Thread(target=thread_parser, args=(page, animal, cop))
                            # thread.start()
                            # url_of_page = f"https://garfield.by/catalog/cats/suhie-korma-dlya-koshek.html?PAGEN_1={page}&SIZEN_1=18"
                            # products_browser = webdriver.Chrome(service=s, options=op)
                            # products_browser.get(url_of_page)
                            #
                            # list_products = WebDriverWait(products_browser, 7, ignored_exceptions=ignored_exceptions) \
                            #     .until(
                            #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item-container")))
                            # print(f'Количество продуктов на странице -- {len(list_products)}')
                            # for product in list_products:
                            #     # product_image = WebDriverWait(product, 7, ignored_exceptions=ignored_exceptions) \
                            #     #     .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
                            #     product_head = WebDriverWait(product, 15, ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item-title")))
                            #     product_url = WebDriverWait(product_head, 15, ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                            #
                            #     product_browser = webdriver.Chrome(service=s, options=op)
                            #     product_browser.get(product_url.get_attribute("href"))
                            #     product_info = WebDriverWait(product_browser, 15, ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__info")))
                            #     product_title = WebDriverWait(product_info, 15, ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                            #     product_img_brand = WebDriverWait(product_info, 15,
                            #                                       ignored_exceptions=ignored_exceptions) \
                            #         .until(
                            #         EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__producer-img")))
                            #     product_brand = WebDriverWait(product_img_brand, 15,
                            #                                   ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
                            #     product_prices = WebDriverWait(product_info, 10,
                            #                                    ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item__tree")))
                            #     prices = WebDriverWait(product_prices, 10, ignored_exceptions=ignored_exceptions) \
                            #         .until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                            #     for p in prices:
                            #         goods = WebDriverWait(p, 10,
                            #                               ignored_exceptions=ignored_exceptions) \
                            #             .until(EC.presence_of_element_located(
                            #             (By.CSS_SELECTOR, "span.product-card__assortiment-item-wt.pc_text15")))
                            #         price = WebDriverWait(p, 10,
                            #                               ignored_exceptions=ignored_exceptions) \
                            #             .until(EC.presence_of_element_located(
                            #             (By.CSS_SELECTOR, "span.product-card__assortiment-item-price.pc_text16b")))
                            #         dict_["url_of_product"] = product_url.get_attribute("href")
                            #         dict_["title"] = product_title.text
                            #         dict_["brand"] = product_brand.get_attribute("alt")
                            #         dict_["goods"] = goods.text
                            #         dict_["price"] = price.text
                            #         dict_["site_url"] = "https://garfield.by/"
                            #         p = Product.objects.get_or_create(title=dict_["title"],
                            #                                           price=dict_["price"])[0]
                            #         try:
                            #             brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                            #         except:
                            #             pass
                            #         p.site_url = dict_["site_url"]
                            #         p.animal = dict_["animal"]
                            #         p.category_of_product = dict_["category_of_product"]
                            #         p.url_of_product = dict_["url_of_product"]
                            #         p.title = dict_["title"]
                            #         p.brand = brand
                            #         p.goods = dict_["goods"]
                            #         p.price = dict_["price"]
                            #         p.save()
                            #         print('-----------------------------------------------------')
                            #     product_browser.close()
                            # products_browser.close()
                    except:
                        list_products = WebDriverWait(category_browser, 7, ignored_exceptions=ignored_exceptions) \
                            .until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item-container")))
                        for product in list_products:
                            # product_image = WebDriverWait(product, 7, ignored_exceptions=ignored_exceptions) \
                            #     .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
                            product_head = WebDriverWait(product, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item-title")))
                            product_url = WebDriverWait(product_head, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                            product_browser = webdriver.Chrome(service=s, options=op)
                            product_browser.get(product_url.get_attribute("href"))
                            product_info = WebDriverWait(product_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__info")))
                            product_title = WebDriverWait(product_info, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                            product_img_brand = WebDriverWait(product_info, 10,
                                                              ignored_exceptions=ignored_exceptions) \
                                .until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__producer-img")))
                            product_brand = WebDriverWait(product_img_brand, 10,
                                                          ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
                            product_prices = WebDriverWait(product_info, 10,
                                                           ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item__tree")))
                            prices = WebDriverWait(product_prices, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                            for p in prices:
                                goods = WebDriverWait(p, 10,
                                                      ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, "span.product-card__assortiment-item-wt.pc_text15")))
                                price = WebDriverWait(p, 10,
                                                      ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, "span.product-card__assortiment-item-price.pc_text16b")))
                                dict_["url_of_product"] = product_url.get_attribute("href")
                                dict_["title"] = product_title.text
                                dict_["brand"] = product_brand.get_attribute("alt")
                                dict_["goods"] = goods.text
                                dict_["price"] = price.text
                                dict_["site_url"] = "https://garfield.by/"
                                p = Product.objects.get_or_create(title=dict_["title"],
                                                                  price=dict_["price"])[0]
                                try:
                                    brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                except:
                                    pass
                                p.site_url = dict_["site_url"]
                                p.animal = dict_["animal"]
                                p.category_of_product = dict_["category_of_product"]
                                p.url_of_product = dict_["url_of_product"]
                                p.title = dict_["title"]
                                p.brand = brand
                                p.goods = dict_["goods"]
                                p.price = dict_["price"]
                                p.save()
                                print('-----------------------------------------------------')
                            product_browser.close()
                    category_browser.close()
            animal_browser.close()

    except Exception as ex:
        print(f'{ex} -- Something happen!')
    finally:
        browser.close()
        browser.quit()


def thread_parser(page, animal, cop):

    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    url_of_page = f"https://garfield.by/catalog/cats/suhie-korma-dlya-koshek.html?PAGEN_1={page}&SIZEN_1=18"
    products_browser = webdriver.Chrome(service=s, options=op)
    products_browser.get(url_of_page)

    list_products = WebDriverWait(products_browser, 7, ignored_exceptions=ignored_exceptions) \
        .until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item-container")))
    print(f'Страница - {page}')
    print(f'Количество продуктов на странице -- {len(list_products)}')
    for product in list_products:
        product_head = WebDriverWait(product, 15, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item-title")))
        product_url = WebDriverWait(product_head, 15, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        url_product = product_url.get_attribute("href")

        thread = threading.Thread(target=parser_of_product, args=(url_product, animal, cop, page))
        thread.start()
        thread.join()

        # product_browser = webdriver.Chrome(service=s, options=op)
        # product_browser.get(product_url.get_attribute("href"))
        # product_info = WebDriverWait(product_browser, 15, ignored_exceptions=ignored_exceptions) \
        #     .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__info")))
        # product_title = WebDriverWait(product_info, 15, ignored_exceptions=ignored_exceptions) \
        #     .until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        # product_img_brand = WebDriverWait(product_info, 15,
        #                                   ignored_exceptions=ignored_exceptions) \
        #     .until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__producer-img")))
        # product_brand = WebDriverWait(product_img_brand, 15,
        #                               ignored_exceptions=ignored_exceptions) \
        #     .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
        # product_prices = WebDriverWait(product_info, 10,
        #                                ignored_exceptions=ignored_exceptions) \
        #     .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item__tree")))
        # prices = WebDriverWait(product_prices, 10, ignored_exceptions=ignored_exceptions) \
        #     .until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
        # for p in prices:
        #     goods = WebDriverWait(p, 10,
        #                           ignored_exceptions=ignored_exceptions) \
        #         .until(EC.presence_of_element_located(
        #         (By.CSS_SELECTOR, "span.product-card__assortiment-item-wt.pc_text15")))
        #     price = WebDriverWait(p, 10,
        #                           ignored_exceptions=ignored_exceptions) \
        #         .until(EC.presence_of_element_located(
        #         (By.CSS_SELECTOR, "span.product-card__assortiment-item-price.pc_text16b")))
        #     dict_["url_of_product"] = product_url.get_attribute("href")
        #     dict_["title"] = product_title.text
        #     dict_["brand"] = product_brand.get_attribute("alt")
        #     dict_["goods"] = goods.text
        #     dict_["price"] = price.text
        #     dict_["site_url"] = "https://garfield.by/"
        #     p = Product.objects.get_or_create(title=dict_["title"],
        #                                       price=dict_["price"])[0]
        #     try:
        #         brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
        #     except:
        #         pass
        #     p.site_url = dict_["site_url"]
        #     p.animal = dict_["animal"]
        #     p.category_of_product = dict_["category_of_product"]
        #     p.url_of_product = dict_["url_of_product"]
        #     p.title = dict_["title"]
        #     p.brand = brand
        #     p.goods = dict_["goods"]
        #     p.price = dict_["price"]
        #     p.save()
        #     print(f'{page}-----------------------------------------------------')
        # product_browser.close()
    products_browser.close()


def parser_of_product(product_url, animal, cop, page):

    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    import requests
    from bs4 import BeautifulSoup

    dict_ = {}
    dict_["animal"] = animal
    dict_["category_of_product"] = cop
    dict_["url_of_product"] = product_url
    print(f'{page} -- {product_url}')
    dict_["site_url"] = "https://garfield.by/"
    product_response = requests.get(url=product_url).text
    soup_product = BeautifulSoup(product_response, "lxml")
    try:
        product = soup_product.find("div", class_="product-card__main").find("div", class_="product-card__info")
        product_title = product.find("h1").text
        product_brand = product.find("div", class_="product-card__producer-img").find("img").get("alt")
        dict_["title"] = product_title
        dict_["brand"] = product_brand
        try:
            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
        except:
            pass
        try:
            product_prices = product.find("div", class_="product-item__tree").find_all("li")
            for p in product_prices:
                goods = p.find("span", class_="product-card__assortiment-item-wt pc_text15").text.strip()
                price = p.find("span", class_="product-card__assortiment-item-price pc_text16b").text.strip()
                dict_["goods"] = goods
                dict_["price"] = price

                p = Product.objects.get_or_create(title=dict_["title"],
                                                  price=dict_["price"])[0]

                p.site_url = dict_["site_url"]
                p.animal = dict_["animal"]
                p.category_of_product = dict_["category_of_product"]
                p.url_of_product = dict_["url_of_product"]
                p.title = dict_["title"]
                p.brand = brand
                p.goods = dict_["goods"]
                p.price = dict_["price"]
                p.save()
        except:
            dict_["goods"] = "Нет в наличии"
            dict_["price"] = "Нет в наличии"

            p = Product.objects.get_or_create(title=dict_["title"],
                                              price=dict_["price"])[0]

            p.site_url = dict_["site_url"]
            p.animal = dict_["animal"]
            p.category_of_product = dict_["category_of_product"]
            p.url_of_product = dict_["url_of_product"]
            p.title = dict_["title"]
            p.brand = brand
            p.goods = dict_["goods"]
            p.price = dict_["price"]
            p.save()
    except Exception as ex:
        pass
    # s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
    # op = webdriver.ChromeOptions()
    # op.add_argument('--headless')
    # dict_ = {}
    # dict_["animal"] = animal
    # dict_["category_of_product"] = cop
    # product_browser = webdriver.Chrome(service=s, options=op)
    # product_browser.get(product_url.get_attribute("href"))
    # product_info = WebDriverWait(product_browser, 15, ignored_exceptions=ignored_exceptions) \
    #     .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__info")))
    # product_title = WebDriverWait(product_info, 15, ignored_exceptions=ignored_exceptions) \
    #     .until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    # product_img_brand = WebDriverWait(product_info, 15,
    #                                   ignored_exceptions=ignored_exceptions) \
    #     .until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__producer-img")))
    # product_brand = WebDriverWait(product_img_brand, 15,
    #                               ignored_exceptions=ignored_exceptions) \
    #     .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
    # product_prices = WebDriverWait(product_info, 10,
    #                                ignored_exceptions=ignored_exceptions) \
    #     .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item__tree")))
    # prices = WebDriverWait(product_prices, 10, ignored_exceptions=ignored_exceptions) \
    #     .until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
    # for p in prices:
    #     goods = WebDriverWait(p, 10,
    #                           ignored_exceptions=ignored_exceptions) \
    #         .until(EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, "span.product-card__assortiment-item-wt.pc_text15")))
    #     price = WebDriverWait(p, 10,
    #                           ignored_exceptions=ignored_exceptions) \
    #         .until(EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, "span.product-card__assortiment-item-price.pc_text16b")))
    #     dict_["url_of_product"] = product_url.get_attribute("href")
    #     dict_["title"] = product_title.text
    #     dict_["brand"] = product_brand.get_attribute("alt")
    #     dict_["goods"] = goods.text
    #     dict_["price"] = price.text
    #     dict_["site_url"] = "https://garfield.by/"
    #     p = Product.objects.get_or_create(title=dict_["title"],
    #                                       price=dict_["price"])[0]
    #     try:
    #         brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
    #     except:
    #         pass
    #     p.site_url = dict_["site_url"]
    #     p.animal = dict_["animal"]
    #     p.category_of_product = dict_["category_of_product"]
    #     p.url_of_product = dict_["url_of_product"]
    #     p.title = dict_["title"]
    #     p.brand = brand
    #     p.goods = dict_["goods"]
    #     p.price = dict_["price"]
    #     p.save()
    #     print(f'{page}-----------------------------------------------------')
    # product_browser.close()
