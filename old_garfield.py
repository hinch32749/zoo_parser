from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time


def parser_garfield():
    from main_parser.models import Product, Age, Size, Specialty, Tasty, TypeProduct, Length, Brand

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
            dict_["animal"] = i.text.lower().strip()
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
                    dict_["category_of_product"] = category_of_product.text.lower().strip()
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
                        for page in range(1, int(last_page.get_attribute("text")) + 1):
                            print(f'Страница {page}')
                            url_of_page = f"https://garfield.by/catalog/cats/suhie-korma-dlya-koshek.html?PAGEN_1={page}&SIZEN_1=18"
                            products_browser = webdriver.Chrome(service=s, options=op)
                            products_browser.get(url_of_page)

                            list_products = WebDriverWait(products_browser, 7, ignored_exceptions=ignored_exceptions) \
                                .until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item-container")))
                            print(f'Количество продуктов на странице -- {len(list_products)}')
                            for product in list_products:
                                # product_image = WebDriverWait(product, 7, ignored_exceptions=ignored_exceptions) \
                                #     .until(EC.presence_of_element_located((By.TAG_NAME, "img")))
                                product_head = WebDriverWait(product, 15, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item-title")))
                                product_url = WebDriverWait(product_head, 15, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.TAG_NAME, "a")))

                                product_browser = webdriver.Chrome(service=s, options=op)
                                product_browser.get(product_url.get_attribute("href"))
                                product_info = WebDriverWait(product_browser, 15, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__info")))
                                product_title = WebDriverWait(product_info, 15, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                                product_img_brand = WebDriverWait(product_info, 15,
                                                                  ignored_exceptions=ignored_exceptions) \
                                    .until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card__producer-img")))
                                product_brand = WebDriverWait(product_img_brand, 15,
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
                            products_browser.close()
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
