import os
import threading
import requests
from bs4 import BeautifulSoup
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
                                     , day_of_week='*'), parser_garfield_cats,
                             name='parser_garfield_cats')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_garfield_dogs,
                             name='parser_garfield_dogs')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_ezoo_dogs,
                             name='parser_ezoo_dogs')
    sender.add_periodic_task(crontab(hour=2, minute=17
                                     , day_of_week='*'), parser_ezoo_cats,
                             name='parser_ezoo_cats')


@app.task
def parser_zootovary_dogs():
    from main_parser.models import Product, Brand
    from concurrent.futures import ThreadPoolExecutor, wait

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
                animal = i.get_attribute("text").lower().strip()
                dict_["animal"] = animal
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text").lower().strip()
                        url_of_category = cat.get_attribute("href")
                        category_of_product = cat.get_attribute("text")
                        print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                        assert "миск" not in cat.get_attribute("text").lower()
                        op = webdriver.ChromeOptions()
                        op.add_argument('--headless')
                        op.add_argument('window-size=1920,1080')
                        new_browser = webdriver.Chrome(service=s, options=op)
                        new_browser.get(cat.get_attribute("href"))
                        new_browser.implicitly_wait(10)
                        try:
                            products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                            time.sleep(3)
                            for page in products_page:
                                if page.find_element(By.CSS_SELECTOR,
                                                     "div.item-name").text.lower().strip() == 'производитель' \
                                        or page.find_element(By.CSS_SELECTOR,
                                                             "div.item-name").text.lower().strip() == 'производители':

                                    options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                        by=By.TAG_NAME, value="li")
                                    print('---------------')
                                    futures = []
                                    with ThreadPoolExecutor() as executer:
                                        for option in range(len(options)):
                                            option_pr = options[option].text.strip()
                                            futures.append(
                                                executer.submit(threads_zootovary, url_of_category, animal,
                                                                category_of_product, option_pr)
                                            )
                                        wait(futures)
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
                                    print(f'URL - {dict_["url_of_product"]}')
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
                                            dict_["goods"] = "в наличии"
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except:
                                            pass
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        p.goods = dict_["goods"]
                                        p.price = dict_["price"]
                                        p.brand = brand
                                        p.save()
                                        print(f'Saved -{dict_["price"]}- {dict_["url_of_product"]}')
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
    except Exception as ex:
        print(f"BAD CONNECTION or \n{ex}")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_cats():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait

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
                animal = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        url_of_category = cat.get_attribute("href")
                        category_of_product = cat.get_attribute("text")
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
                                if page.find_element(By.CSS_SELECTOR,
                                                     "div.item-name").text.lower().strip() == 'производитель' \
                                        or page.find_element(By.CSS_SELECTOR,
                                                             "div.item-name").text.lower().strip() == 'производители':

                                    options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                        by=By.TAG_NAME, value="li")
                                    print('---------------')
                                    futures = []
                                    with ThreadPoolExecutor() as executer:
                                        for option in range(len(options)):
                                            option_pr = options[option].text.strip()
                                            futures.append(
                                                executer.submit(threads_zootovary, url_of_category, animal,
                                                                category_of_product, option_pr)
                                            )
                                        wait(futures)
                        except Exception as ex:
                            print(f"No FILTERS or \n{ex}")
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
                                            dict_["goods"] = "в наличии"
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except Exception as ex:
                                            print(ex)
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        p.goods = dict_["goods"]
                                        p.price = dict_["price"]
                                        try:
                                            p.brand = brand
                                        except Exception as ex:
                                            print(ex)
                                        p.save()
                                        print(f'{option_pr} -{dict_["price"]}- {dict_["url_of_product"]}')
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
    except Exception as ex:
        print(f"BAD CONNECTION or \n{ex}")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_birds():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait

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
                animal = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        url_of_category = cat.get_attribute("href")
                        category_of_product = cat.get_attribute("text")
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
                                if page.find_element(By.CSS_SELECTOR,
                                                     "div.item-name").text.lower().strip() == 'производитель' \
                                        or page.find_element(By.CSS_SELECTOR,
                                                             "div.item-name").text.lower().strip() == 'производители':

                                    options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                        by=By.TAG_NAME, value="li")
                                    print('---------------')
                                    futures = []
                                    with ThreadPoolExecutor() as executer:
                                        for option in range(len(options)):
                                            option_pr = options[option].text.strip()
                                            futures.append(
                                                executer.submit(threads_zootovary, url_of_category, animal,
                                                                category_of_product, option_pr)
                                            )
                                        wait(futures)
                        except Exception as ex:
                            print(f"No FILTERS or \n{ex}")
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
                                            dict_["goods"] = "в наличии"
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except Exception as ex:
                                            print(ex)
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        p.goods = dict_["goods"]
                                        p.price = dict_["price"]
                                        try:
                                            p.brand = brand
                                        except Exception as ex:
                                            print(ex)
                                        p.save()
                                        print(f'{option_pr} -{dict_["price"]}- {dict_["url_of_product"]}')
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except Exception as ex:
                                    print(f"Закончились страницы or \n{ex}")
                                    break

                        finally:
                            new_browser.close()
    except Exception as ex:
        print(f"BAD CONNECTION or \n{ex}")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_rodents():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait

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
                animal = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        url_of_category = cat.get_attribute("href")
                        category_of_product = cat.get_attribute("text")
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
                                if page.find_element(By.CSS_SELECTOR,
                                                     "div.item-name").text.lower().strip() == 'производитель' \
                                        or page.find_element(By.CSS_SELECTOR,
                                                             "div.item-name").text.lower().strip() == 'производители':

                                    options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                        by=By.TAG_NAME, value="li")
                                    print('---------------')
                                    futures = []
                                    with ThreadPoolExecutor() as executer:
                                        for option in range(len(options)):
                                            option_pr = options[option].text.strip()
                                            futures.append(
                                                executer.submit(threads_zootovary, url_of_category, animal,
                                                                category_of_product, option_pr)
                                            )
                                        wait(futures)
                        except Exception as ex:
                            print(f"No FILTERS or \n{ex}")
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
                                            dict_["goods"] = "в наличии"
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]
                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except Exception as ex:
                                            print(ex)
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        p.goods = dict_["goods"]
                                        p.price = dict_["price"]
                                        try:
                                            p.brand = brand
                                        except Exception as ex:
                                            print(ex)
                                        p.save()
                                        print(f'{option_pr} -{dict_["price"]}- {dict_["url_of_product"]}')
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except Exception as ex:
                                    print(f"Закончились страницы or \n {ex}")
                                    break

                        finally:
                            new_browser.close()
    except Exception as ex:
        print(f"BAD CONNECTION or \n{ex}")
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_zootovary_fishes():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait

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
                animal = i.get_attribute("text").lower().strip()
                for category in categories:
                    categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                    for cat in categ:
                        cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        time.sleep(2)
                        dict_["category_of_product"] = cat.get_attribute("text")
                        url_of_category = cat.get_attribute("href")
                        category_of_product = cat.get_attribute("text")
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
                                if page.find_element(By.CSS_SELECTOR,
                                                     "div.item-name").text.lower().strip() == 'производитель' \
                                        or page.find_element(By.CSS_SELECTOR,
                                                             "div.item-name").text.lower().strip() == 'производители':

                                    options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                                        by=By.TAG_NAME, value="li")
                                    print('---------------')
                                    futures = []
                                    with ThreadPoolExecutor() as executer:
                                        for option in range(len(options)):
                                            option_pr = options[option].text.strip()
                                            futures.append(
                                                executer.submit(threads_zootovary, url_of_category, animal,
                                                                category_of_product, option_pr)
                                            )
                                        wait(futures)
                        except Exception as ex:
                            print(f"No FILTERS or \n{ex}")
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
                                            dict_["goods"] = "в наличии"
                                            dict_["price"] = pr
                                        p = Product.objects.get_or_create(title=dict_["title"], price=dict_["price"])[0]

                                        try:
                                            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
                                        except Exception as ex:
                                            print(ex)
                                        p.site_url = dict_["site_url"]
                                        p.animal = dict_["animal"]
                                        p.category_of_product = dict_["category_of_product"]
                                        p.url_of_product = dict_["url_of_product"]
                                        p.title = dict_["title"]
                                        p.goods = dict_["goods"]
                                        p.price = dict_["price"]
                                        try:
                                            p.brand = brand
                                        except Exception as ex:
                                            print(ex)
                                        p.save()
                                        print(f'{option_pr} -{dict_["price"]}- {dict_["url_of_product"]}')
                                    print('================')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                                except Exception as ex:
                                    print(f"Закончились страницы or \n{ex}")
                                    break

                        finally:
                            new_browser.close()
    except Exception as ex:
        print(f"BAD CONNECTION or \n{ex}")
    finally:
        browser.close()
        browser.quit()


def threads_zootovary(url_of_category, animal, category_of_product, option_pr):
    from main_parser.models import Product, Brand

    try:
        s = Service(
            '/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        op.add_argument('window-size=1920,1080')
        thread_browser = webdriver.Chrome(service=s, options=op)
        thread_browser.get(url_of_category)
        thread_browser.implicitly_wait(10)
        dict_ = {}
        dict_["site_url"] = "https://zootovary.by/"
        dict_["animal"] = animal
        dict_["category_of_product"] = category_of_product
        dict_["brand"] = option_pr
        list_navigation = WebDriverWait(thread_browser, 10, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
        time.sleep(3)
        print(f'{option_pr}')
        for navigation in list_navigation:
            if navigation.find_element(By.CSS_SELECTOR, "div.item-name").text.lower().strip() == 'производитель' \
                    or navigation.find_element(By.CSS_SELECTOR,
                                               "div.item-name").text.lower().strip() == 'производители':
                options = navigation.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(
                    by=By.TAG_NAME, value="li")
                for option in options:
                    if option.text.strip() == option_pr:
                        opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                            .until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                        opt.click()
                        time.sleep(10)
                        got_price = True
                        try:
                            while got_price:
                                products = WebDriverWait(thread_browser, 15, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_all_elements_located(
                                    (By.CSS_SELECTOR, "div.product-item.clearfix")))
                                for product in products:
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
                                            dict_["goods"] = "в наличии"
                                            dict_["price"] = pr
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
                                        p.goods = dict_["goods"]
                                        p.price = dict_["price"]
                                        p.brand = brand
                                        p.save()
                                        print(f'{option_pr} -{dict_["price"]}- {dict_["url_of_product"]}')
                                    print('===========')
                                time.sleep(1)

                                try:
                                    paginator = WebDriverWait(thread_browser, 10,
                                                              ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.next")))
                                    paginator.click()
                                    time.sleep(3)
                                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                                except:
                                    print("Закончились страницы")
                                    thread_browser.close()
                                    break
                            time.sleep(5)
                        except Exception as ex:
                            print(f'Нет товаров по фильтру or \n{ex}')
    except Exception as ex:
        print(ex)
    finally:
        thread_browser.close()
        thread_browser.quit()


@app.task
def parser_garfield_cats():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait
    try:
        s = Service(
            '/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        # op.add_argument('window-size=1920,1080')
        browser = webdriver.Chrome(service=s, options=op)
        url = "https://garfield.by/catalog/cats.html"
        browser.get(url)
        browser.implicitly_wait(10)
        animal = "кошки"
        cop = WebDriverWait(browser, 10, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.bx_catalog_tile")))
        categories_of_product = WebDriverWait(cop, 10, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "catalog_section_snipet")))
        for c in categories_of_product:
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
                category_browser = webdriver.Chrome(service=s, options=op)
                url_of_category = category_of_product.get_attribute("href")
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
                                executor.submit(thread_parser, page, animal, cop, url_of_category)
                            )
                    wait(futures)
                except:
                    list_products = WebDriverWait(category_browser, 7, ignored_exceptions=ignored_exceptions) \
                        .until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item-container")))
                    for product in list_products:
                        dict_ = {}
                        dict_["animal"] = animal
                        dict_["category_of_product"] - cop
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

    except Exception as ex:
        print(f'{ex} -- Something happen!')
    finally:
        browser.close()
        browser.quit()


@app.task
def parser_garfield_dogs():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand
    from concurrent.futures import ThreadPoolExecutor, wait
    try:
        s = Service(
            '/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        # op.add_argument('window-size=1920,1080')
        browser = webdriver.Chrome(service=s, options=op)
        url = "https://garfield.by/catalog/dogs.html"
        browser.get(url)
        browser.implicitly_wait(10)
        animal = "собаки"
        cop = WebDriverWait(browser, 10, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.bx_catalog_tile")))
        categories_of_product = WebDriverWait(cop, 10, ignored_exceptions=ignored_exceptions) \
            .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "catalog_section_snipet")))
        for c in categories_of_product:
            category = WebDriverWait(c, 10, ignored_exceptions=ignored_exceptions) \
                .until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.bx_catalog_tile_title")))
            category_of_product = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
            if category_of_product.text.lower() == 'сухой корм' \
                    or category_of_product.text.lower().strip() == 'консервы' \
                    or category_of_product.text.lower().strip() == 'лакомства' \
                    or category_of_product.text.lower().strip() == 'витамины и добавки':
                print(f'{category_of_product.text} -- {category_of_product.get_attribute("href")}')
                print("=========================================================================")
                cop = category_of_product.text.lower().strip()
                category_browser = webdriver.Chrome(service=s, options=op)
                url_of_category = category_of_product.get_attribute("href")
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
                                executor.submit(thread_parser, page, animal, cop, url_of_category)
                            )
                    wait(futures)
                except:
                    list_products = WebDriverWait(category_browser, 7, ignored_exceptions=ignored_exceptions) \
                        .until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item-container")))
                    for product in list_products:
                        dict_ = {}
                        dict_["animal"] = animal
                        dict_["category_of_product"] - cop
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

    except Exception as ex:
        print(f'{ex} -- Something happen!')
    finally:
        browser.close()
        browser.quit()


def thread_parser(page, animal, cop, url_of_category):
    s = Service('/home/hinch/PycharmProjects/PARSERS/Zoo_parser/zoo_parser/zoo_parser_conf/chromedriver/chromedriver')
    ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    url_of_page = f"{url_of_category}?PAGEN_1={page}&SIZEN_1=18"
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
    products_browser.close()


def parser_of_product(product_url, animal, cop, page):
    from main_parser.models import Product, Brand

    dict_ = {}
    dict_["animal"] = animal
    dict_["category_of_product"] = cop
    dict_["url_of_product"] = product_url
    print(f'{page} -- {product_url}')
    dict_["site_url"] = "https://garfield.by/"
    product_response = requests.get(url=product_url).text
    time.sleep(0.3)
    soup_product = BeautifulSoup(product_response, "lxml")
    try:
        product = soup_product.find("div", class_="product-card__main").find("div", class_="product-card__info")
        product_title = product.find("h1").text
        product_brand = product.find("div", class_="product-card__producer-img").find("img").get("alt")
        dict_["title"] = product_title
        dict_["brand"] = product_brand.strip()
        try:
            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
        except:
            pass
        try:
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
            except Exception as ex:
                print(ex)
                actual = product.find("div", class_="product-card__price-wt").text.strip()
                if 'нет' in actual:
                    dict_["goods"] = 'нет в наличии'
                    dict_["price"] = 'нет в наличии'
                else:
                    dict_["goods"] = 'в наличии'
                    dict_["price"] = product.find("div", class_="product-card__price-main").text.strip()
                p = Product.objects.get_or_create(title=dict_["title"])[0]
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
            print(ex)
            dict_["goods"] = "нет в наличии"
            dict_["price"] = "нет в наличии"

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
        print(ex)


@app.task
def parser_ezoo_dogs():
    from concurrent.futures import ThreadPoolExecutor, wait

    site_url = 'https://e-zoo.by/'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    response = requests.get(url=site_url, headers=headers).text
    soup = BeautifulSoup(response, "lxml")
    animals = soup.find("ul", class_="nav__list js-nav-list").find_all("li", class_="nav__item")

    for name_animal in animals:
        animal = name_animal.find("a", class_="nav__link").text.lower().strip()
        if animal == 'собаки':
            dict_ = {}
            dict_["site_url"] = site_url
            dict_["animal"] = animal
            url_animal = name_animal.find("a", class_="nav__link").get("href")
            try:
                response_animal = requests.get(url_animal).text
                soup_animal = BeautifulSoup(response_animal, "lxml")
                categories_of_product = soup_animal.find("div", class_="categories").find_all("a", class_="link-cat")
            except Exception as ex:
                print(f'Maybe bad connection \n{ex}')
            for cop in categories_of_product[:5]:
                category_of_product = cop.text.lower().strip().split("(")[0]
                dict_["category_of_product"] = category_of_product
                print(f'\t\t\t{category_of_product.upper()}')
                print('=======================================')
                url_of_category = cop.get("href")
                response_category = requests.get(url_of_category).text
                soup_category = BeautifulSoup(response_category, "lxml")
                try:
                    try:
                        pagination = soup_category.find("div", class_="pagination").find_all("a")[-2]
                        futures = []
                        with ThreadPoolExecutor() as executer:
                            for page in range(1, int(pagination.text)+1):
                                futures.append(
                                    executer.submit(threads_ezoo, url_of_category, animal,
                                                    category_of_product, site_url, page)
                                )
                            wait(futures)
                    except Exception as ex:
                        print(f'In parser e-zoo DOGS(NO PAGINATION) -- {ex}')
                        list_products = soup_category.find("div", class_="catalog js-catalog").find_all("div",
                                                                                               class_="catalog__item js-catalog-item")
                        for product in list_products:
                            info = product.find("div", class_="cart__inner")
                            url_of_product = info.find("div", class_="cart__title h3").find("a").get("href")
                            thread = threading.Thread(target=parser_product_ezoo,
                                                      args=(url_of_product, animal, category_of_product, site_url, page,))
                            thread.start()
                            thread.join()
                except Exception as ex:
                    print(f'In parser e-zoo DOGS(ALL TRY) -- {ex}')


@app.task
def parser_ezoo_cats():
    from concurrent.futures import ThreadPoolExecutor, wait

    site_url = 'https://e-zoo.by/'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    response = requests.get(url=site_url, headers=headers).text
    soup = BeautifulSoup(response, "lxml")
    animals = soup.find("ul", class_="nav__list js-nav-list").find_all("li", class_="nav__item")

    for name_animal in animals:
        animal = name_animal.find("a", class_="nav__link").text.lower().strip()
        if animal == 'кошки':
            dict_ = {}
            dict_["site_url"] = site_url
            dict_["animal"] = animal
            url_animal = name_animal.find("a", class_="nav__link").get("href")
            try:
                response_animal = requests.get(url_animal).text
                soup_animal = BeautifulSoup(response_animal, "lxml")
                categories_of_product = soup_animal.find("div", class_="categories").find_all("a", class_="link-cat")
            except Exception as ex:
                print(f'Maybe bad connection \n{ex}')
            for cop in categories_of_product[:5]:
                category_of_product = cop.text.lower().strip().split("(")[0]
                dict_["category_of_product"] = category_of_product
                print(f'\t\t\t{category_of_product.upper()}')
                print('=======================================')
                url_of_category = cop.get("href")
                response_category = requests.get(url_of_category).text
                soup_category = BeautifulSoup(response_category, "lxml")
                try:
                    try:
                        pagination = soup_category.find("div", class_="pagination").find_all("a")[-2]
                        futures = []
                        with ThreadPoolExecutor() as executer:
                            for page in range(1, int(pagination.text)+1):
                                futures.append(
                                    executer.submit(threads_ezoo, url_of_category, animal,
                                                    category_of_product, site_url, page)
                                )
                            wait(futures)
                    except Exception as ex:
                        print(f'In parser e-zoo DOGS(NO PAGINATION) -- {ex}')
                        list_products = soup_category.find("div", class_="catalog js-catalog").find_all("div",
                                                                                               class_="catalog__item js-catalog-item")
                        for product in list_products:
                            info = product.find("div", class_="cart__inner")
                            url_of_product = info.find("div", class_="cart__title h3").find("a").get("href")
                            thread = threading.Thread(target=parser_product_ezoo,
                                                      args=(url_of_product, animal, category_of_product, site_url, page,))
                            thread.start()
                            thread.join()
                except Exception as ex:
                    print(f'In parser e-zoo DOGS(ALL TRY) -- {ex}')


def threads_ezoo(url_of_category, animal, category_of_product, site_url, page):

    url = f'{url_of_category}?page={page}'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    }
    try:
        response = requests.get(url=url, headers=headers).text
        soup = BeautifulSoup(response, "lxml")
        list_products = soup.find("div", class_="catalog js-catalog").find_all("div", class_="catalog__item js-catalog-item")
    except Exception as ex:
        print(f'Maybe bad connection \n{ex}')

    for product in list_products:
        info = product.find("div", class_="cart__inner")
        url_of_product = info.find("div", class_="cart__title h3").find("a").get("href")
        thread = threading.Thread(target=parser_product_ezoo, args=(url_of_product, animal, category_of_product, site_url, page, ))
        thread.start()
        thread.join()


def parser_product_ezoo(url_of_product, animal, category_of_product, site_url, page):
    from main_parser.models import Product, Brand

    dict_ = {}
    dict_["site_url"] = site_url
    dict_["animal"] = animal
    dict_["category_of_product"] = category_of_product
    dict_["url_of_product"] = url_of_product
    try:
        product_response = requests.get(url=url_of_product).text
        soup_product = BeautifulSoup(product_response, "lxml")
        time.sleep(0.1)
    except Exception as ex:
        print(f'Maybe bad connection \n{ex}')
    try:
        title = soup_product.find("div", class_="product__header").text.strip()
        dict_["title"] = title
        try:
            brand = soup_product.find("div", class_="product__meta").find("a").text.strip()
            dict_["brand"] = brand
        except Exception as ex:
            print(f'Has no brand \n{ex}')
        prices = soup_product.find("div", class_="product__variant-table redline-mod").find_all("form", class_="product__variant js-cart-basket-submit")
        try:
            brand = Brand.objects.get_or_create(name=dict_["brand"])[0]
        except Exception as ex:
            print(f'Something with saving BRAND \n{ex}')
        for p in prices:
            p = p.find_all("div")
            titles = ["goods", "price", "price_online_pickup", "price_online_delivery"]
            for i, j in zip(titles, p[:-2]):
                j = j.text.replace("\n", " ").strip()
                dict_[i] = j

            p = Product.objects.get_or_create(title=dict_["title"],
                                              price=dict_["price"])[0]
            p.site_url = dict_["site_url"]
            p.animal = dict_["animal"]
            p.category_of_product = dict_["category_of_product"]
            p.url_of_product = dict_["url_of_product"]
            p.title = dict_["title"]
            try:
                p.brand = brand
            except Exception as ex:
                print(f'Something with add BRAND to Product \n{ex}')
            p.goods = dict_["goods"]
            p.price = dict_["price"]
            p.save()
            print(f'{page} -- {brand} - {url_of_product}')
    except Exception as ex:
        print(f'Parser of product(MAIN TRY) \n{ex}')
