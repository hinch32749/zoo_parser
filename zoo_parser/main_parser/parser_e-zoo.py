import threading
import time
import requests
from bs4 import BeautifulSoup


def parser_product_ezoo(url_of_product, animal, category_of_product, site_url, page):
    # from main_parser.models import Product, Brand

    dict_ = {}
    dict_["site_url"] = site_url
    dict_["animal"] = animal
    dict_["category_of_product"] = category_of_product
    dict_["url_of_product"] = url_of_product
    product_response = requests.get(url=url_of_product).text
    time.sleep(0.1)
    soup_product = BeautifulSoup(product_response, "lxml")
    title = soup_product.find("div", class_="product__header").text.strip()
    dict_["title"] = title
    brand = soup_product.find("div", class_="product__meta").find("a").text.strip()
    dict_["brand"] = brand
    prices = soup_product.find("div", class_="product__variant-table redline-mod").find_all("form", class_="product__variant js-cart-basket-submit")
    for p in prices:
        p = p.find_all("div")
        titles = ["goods", "price", "price_online_pickup", "price_online_delivery"]
        for i, j in zip(titles, p[:-2]):
            j = j.text.replace("\n", " ").strip()
            dict_[i] = j
        print(f'{page} -- {dict_}')


def threads_ezoo(url_of_category, animal, category_of_product, site_url, page):

    url = f'{url_of_category}?page={page}'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    response = requests.get(url=url, headers=headers).text
    soup = BeautifulSoup(response, "lxml")

    list_products = soup.find("div", class_="catalog js-catalog").find_all("div", class_="catalog__item js-catalog-item")
    for i in list_products:
        info = i.find("div", class_="cart__inner")
        url_of_product = info.find("div", class_="cart__title h3").find("a").get("href")
        thread = threading.Thread(target=parser_product_ezoo, args=(url_of_product, animal, category_of_product, site_url, page, ))
        thread.start()
        thread.join()


def parser_ezoo_dogs():
    from concurrent.futures import ThreadPoolExecutor, wait

    site_url = 'https://e-zoo.by/'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    response = requests.get(url=site_url, headers=headers).text
    soup = BeautifulSoup(response, "lxml")
    animals = soup.find("ul", class_="nav__list js-nav-list").find_all("li", class_="nav__item")

    for name_animal in animals[4:]:
        animal = name_animal.find("a", class_="nav__link").text.lower().strip()
        if animal == 'собаки':
            dict_ = {}
            dict_["site_url"] = site_url
            dict_["animal"] = animal
            url_animal = name_animal.find("a", class_="nav__link").get("href")
            response_animal = requests.get(url_animal).text
            soup_animal = BeautifulSoup(response_animal, "lxml")
            categories_of_product = soup_animal.find("div", class_="categories").find_all("a", class_="link-cat")

            for cop in categories_of_product[:5]:
                category_of_product = cop.text.lower().strip().split("(")[0]
                dict_["category_of_product"] = category_of_product
                print(f'\t\t\t{category_of_product}')
                print('=======================================')
                url_of_category = cop.get("href")
                response_category = requests.get(url_of_category).text
                soup_category = BeautifulSoup(response_category, "lxml")
                pagination = soup_category.find("div", class_="pagination").find_all("a")[-2]
                futures = []
                with ThreadPoolExecutor() as executer:
                    for page in range(1, int(pagination.text)+1):
                        futures.append(
                            executer.submit(threads_ezoo, url_of_category, animal,
                                            category_of_product, site_url, page)
                        )
                    wait(futures)


def main():
    parser_ezoo_dogs()


if __name__ == "__main__":
    main()

