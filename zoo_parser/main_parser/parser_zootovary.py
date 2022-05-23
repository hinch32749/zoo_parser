from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time


def parser_zootovary():
    list_filters = ['возраст', 'размер', 'особенности', 'свойства', 'тип', 'длина', 'состав', 'вид животного']
    try:
        s = Service('../zoo_parser_conf/chromedriver/chromedriver')
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        browser = webdriver.Chrome(service=s, options=op)
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
                    # new_browser.fullscreen_window()
                    new_browser.implicitly_wait(10)
                    try:
                        products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                        time.sleep(3)
                        for page in products_page:
                            print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)########
                            if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                continue
                            options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(by=By.TAG_NAME, value="li")
                            print('---------------')
                            for option in options:
                                print(f'OPTION -- {option.text}')
                                dict_["age"] = option.text
                                opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                opt.click()
                                time.sleep(5)
                                while True:
                                    products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                    for product in products:
                                        # print(f'IMAGE -- {product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")}')
                                        dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")
                                        url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img").\
                                            find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                        # print(f'URL -- {url_of_product}')
                                        dict_["url_of_product"] = url_of_product
                                        # print(f'TITLE -- {product.find_element(by=By.CSS_SELECTOR, value="h2").text}')
                                        dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                        try:
                                            list_price = []
                                            for price in product.find_elements(by=By.CSS_SELECTOR, value="td"):
                                                if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                    continue
                                                list_price.append(price.text)
                                            pare = len(list_price[2:]) // 2
                                            for i in range(0, pare*2, 2):
                                                dict_["goods"] = list_price[2+i]
                                                dict_["price"] = list_price[3+i]
                                                # dict_save
                                            # print(list_price[2:])
                                        except Exception as ex:
                                            # print(ex)
                                            print("Нет цен!")
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

                                opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                opt.click()
                                time.sleep(2)
                    except:
                        print("No FILTERS")
                        while True:
                            products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                            for product in products:
                                # print(f'IMAGE -- {product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")}')
                                dict_["image"] = product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")
                                url_of_product = product.find_element(by=By.CSS_SELECTOR, value="div.product-img").find_element(
                                    by=By.TAG_NAME, value="a").get_attribute("href")
                                # print(f'URL -- {url_of_product}')
                                dict_["url_of_product"] = url_of_product
                                # print(f'TITLE -- {product.find_element(by=By.CSS_SELECTOR, value="h2").text}')
                                dict_["title"] = product.find_element(by=By.CSS_SELECTOR, value="h2").text
                                try:
                                    list_price = []
                                    for price in product.find_elements(by=By.CSS_SELECTOR, value="td"):
                                        if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                            continue
                                        list_price.append(price.text)
                                    pare = len(list_price[2:]) // 2
                                    for i in range(0, pare * 2, 2):
                                        dict_["goods"] = list_price[2 + i]
                                        dict_["price"] = list_price[3 + i]
                                        # dict_save
                                    print(dict_)
                                    # print(list_price[2:])
                                except Exception as ex:
                                    # print(ex)
                                    print("Нет цен!")
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


parser_zootovary()
