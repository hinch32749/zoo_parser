import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
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


@app.task
def parser_zootovary_dogs():

    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length

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
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR, "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR, "div.container_12.menu-cat-top").find_elements(By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        dict_ = {}
        for i, j in zip(name_of_animals, name_of_categories):
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            if i.get_attribute("text").lower().strip() == "собаки":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text")
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        # if "миск" in cat.get_attribute("text").lower():
                        #     raise
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
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
                                print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)########
                                if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower().strip() == 'производитель' \
                                        or page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower().strip() == 'производители':
                                    continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text
                                        else:
                                            try:
                                                dict_.pop(page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower())
                                            except Exception as ex:
                                                pass
                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                    opt.click()
                                    time.sleep(3)
                                    got_price = True
                                    while got_price:
                                        products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                            .until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                        for product in products:
                                            dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")
                                            url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img").\
                                                find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                            dict_["url_of_product"] = url_of_product
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            print(pare)
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            print(pare)
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

                                    opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
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
                                    dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")
                                    url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img"). \
                                        find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                    dict_["url_of_product"] = url_of_product
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    print(pare)
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    print(pare)
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
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length
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
                dict_["animal"] = i.get_attribute("text")
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
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
                                if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                    continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower())
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
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            print(pare)
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            print(pare)
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
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    print(pare)
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    print(pare)
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
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length
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
                dict_["animal"] = i.get_attribute("text")
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
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
                                if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                    continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower())
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
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            print(pare)
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            print(pare)
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
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    print(pare)
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    print(pare)
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
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length

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
                dict_["animal"] = i.get_attribute("text")
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
                                if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                    continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower())
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
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            print(pare)
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            print(pare)
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
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)
                                    pare = len(list_price[2:]) // 2
                                    print(pare)
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    print(pare)
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
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length
    list_animals = ["собаки", "кошки", "грызуны", "птицы", "рыбки"]
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
            if i.get_attribute("text").lower().strip() == "рыбки":
                print(f' --- {i.get_attribute("text")}')
                dict_["site_url"] = url
                dict_["animal"] = i.get_attribute("text")
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
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
                                if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                    continue
                                options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                    by=By.TAG_NAME, value="li")
                                print('---------------')
                                for option in options:
                                    print(f'OPTION -- {option.text}')
                                    for i in dict_filters:
                                        if i in page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower():
                                            dict_[dict_filters[i]] = option.text
                                        else:
                                            try:
                                                dict_.pop(
                                                    page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower())
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
                                            dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                            list_price = []
                                            prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                            for price in prices:
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)

                                            pare = len(list_price[2:]) // 2
                                            print(pare)
                                            pr = ''
                                            if len(list_price) == 2:
                                                pr = list_price[1]
                                                pare = 1
                                            elif pare < 1:
                                                print("No prices")
                                                got_price = False
                                                break
                                            print(pare)
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
                                    dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                    list_price = []
                                    prices = product.find_elements(by=By.CSS_SELECTOR, value="td")
                                    for price in prices:
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)

                                    pare = len(list_price[2:]) // 2
                                    print(pare)
                                    pr = ''
                                    if len(list_price) == 2:
                                        pr = list_price[1]
                                        pare = 1
                                    elif pare < 1:
                                        print("No prices")
                                        got_price = False
                                        break
                                    print(pare)
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
