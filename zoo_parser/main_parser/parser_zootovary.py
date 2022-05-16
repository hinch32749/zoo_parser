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
    try:
        s = Service('../chromedriver/chromedriver')
        browser = webdriver.Chrome(service=s)
        url = "https://zootovary.by/"
        browser.get(url)
        browser.implicitly_wait(10)
        # browser.fullscreen_window()
        time.sleep(3)
        name_of_categories = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_elements(By.CSS_SELECTOR, "div.container_12.products")
        name_of_animals = browser.find_element(By.CSS_SELECTOR, "div.block-tabs").find_element(By.CSS_SELECTOR, "div.container_12.menu-cat-top").find_elements(By.TAG_NAME, "a")
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)

        for i, j in zip(name_of_animals, name_of_categories):
            categories = j.find_elements(By.CSS_SELECTOR, "div.grid_2")
            print(f' --- {i.get_attribute("text")}')
            for category in categories:
                categ = WebDriverWait(category, 10, ignored_exceptions=ignored_exceptions) \
                    .until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                for cat in categ:
                    cat = WebDriverWait(cat, 10, ignored_exceptions=ignored_exceptions) \
                        .until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                    time.sleep(2)
                    print(f'{cat.get_attribute("text")} --- {cat.get_attribute("href")}')
                    new_browser = webdriver.Chrome(service=s)
                    new_browser.get(cat.get_attribute("href"))
                    new_browser.fullscreen_window()
                    new_browser.implicitly_wait(10)
                    try:
                        products_page = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                            .until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-nav")))
                        time.sleep(3)
                        for page in products_page:
                            print(page.find_element(By.CSS_SELECTOR, "div.item-name").text)
                            if page.find_element(By.CSS_SELECTOR, "div.item-name").text.lower() == 'производитель':
                                continue
                            options = page.find_element(By.CSS_SELECTOR, "ul.view-item").find_elements(by=By.TAG_NAME, value="li")
                            print('---------------')
                            for option in options:
                                print(f'OPTION -- {option.text}')
                                opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                opt.click()
                                time.sleep(5)
                                x = 0
                                while x < 1:
                                    products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                        .until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                                    for product in products:
                                        print(f'IMAGE -- {product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")}')
                                        url = product.find_element(by=By.CSS_SELECTOR, value="div.product-img").find_element(by=By.TAG_NAME, value="a").get_attribute("href")
                                        print(f'URL -- {url}')
                                        for price in product.find_elements(by=By.CSS_SELECTOR, value="td"):
                                            if 'корзин' in price.text.lower() or 'заказ' in price.text.lower():
                                                continue
                                            print(f'PRICE -- {price.text}')
                                        print(f'TITLE -- {product.find_element(by=By.CSS_SELECTOR, value="h2").text}')
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

                                    x += 1

                                opt = WebDriverWait(option, 10, ignored_exceptions=ignored_exceptions) \
                                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.niceCheck.filterInput")))
                                opt.click()
                                time.sleep(2)
                                break
                            break
                    except:
                        print("No FILTERS")
                        x = 0
                        while x < 1:
                            products = WebDriverWait(new_browser, 10, ignored_exceptions=ignored_exceptions) \
                                .until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-item.clearfix")))
                            for product in products:
                                print(f'IMAGE -- {product.find_element(by=By.TAG_NAME, value="img").get_attribute("src")}')
                                url = product.find_element(by=By.CSS_SELECTOR, value="div.product-img").find_element(
                                    by=By.TAG_NAME, value="a").get_attribute("href")
                                print(f'URL -- {url}')
                                for price in product.find_elements(by=By.CSS_SELECTOR, value="td"):
                                    print(list(price))
                                    print(f'PRICE -- {price.text}')
                                print(f'TITLE -- {product.find_element(by=By.CSS_SELECTOR, value="h2").text}')
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
                            x += 1
                    finally:
                        new_browser.close()
                    break
    except:
        print("BAD CONNECTION")
    finally:
        browser.close()
        browser.quit()


parser_zootovary()
