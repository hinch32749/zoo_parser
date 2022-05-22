import os
import django
import requests
from bs4 import BeautifulSoup
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zoo_parser.zoo_parser_conf.settings")  # zoo_parser_conf название проекта
# django.setup()

# from zoo_parser.main_parser.models import Product
#
# p = Product.objects.all()


def parser_ezoo():
    site_url = 'https://e-zoo.by/'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}
    response = requests.get(url=site_url, headers=headers).text
    soup = BeautifulSoup(response, "lxml")
    animals = soup.find("ul", class_="nav__list js-nav-list").find_all("li", class_="nav__item")

    for animal in animals[4:5]:
        dict_ = {}
        dict_["site_url"] = site_url
        dict_["animal"] = animal.find("a", class_="nav__link").text.strip()

        print('=========================================')
        print("\t\t\t", animal.find("a", class_="nav__link").text.strip().upper())
        url_animal = animal.find("a", class_="nav__link").get("href")
        print('=========================================')
        response_animal = requests.get(url_animal).text
        soup_animal = BeautifulSoup(response_animal, "lxml")
        categories_of_product = soup_animal.find("div", class_="categories").find_all("a", class_="link-cat")

        for category_of_product in categories_of_product[:1]:

            dict_["category_of_product"] = category_of_product.text.strip()

            print(f'\t\t\t{category_of_product.text.strip().upper()}')
            print('=======================================')
            url_category = category_of_product.get("href")
            response_category = requests.get(url_category).text
            soup_category = BeautifulSoup(response_category, "lxml")
            subcategories_of_products = soup_category.find("div", class_="categories").find_all("div", class_="name-cat")

            for subcategory_of_product in subcategories_of_products[:1]:

                dict_["subcategory_of_product"] = subcategory_of_product.text.strip()

                print(f'\t-- {subcategory_of_product.text.strip()}')
                page = 1

                while True:
                    url = subcategory_of_product.find("a").get("href")

                    url = url + f'?page={page}'
                    resp = requests.get(url).text
                    soup = BeautifulSoup(resp, "lxml")
                    print(f'\t url_products -- {url}')

                    products = soup.find("div", class_="catalog js-catalog").find_all("a", class_="cart__title-link")

                    for product in products[:3]:
                        response_product = requests.get(product.get("href")).text
                        dict_["url_of_product"] = product.get("href")
                        soup_product = BeautifulSoup(response_product, "lxml")
                        title = soup_product.find("div", class_="product__header").text.strip()
                        dict_["title"] = title
                        brand = soup_product.find("div", class_="product__meta").find("a").text.strip()
                        dict_["brand"] = brand
                        prices_title = soup_product.find("div", class_="product__variant variant_name_line").find_all("div", class_="product__variant-cell")

                        prices = soup_product.find("div", class_="product__variant-table redline-mod").find_all("form", class_="product__variant js-cart-basket-submit")
                        print("---------------------------------------------------------------------")
                        print(f'-- URL {product.get("href")}')
                        print(f'{soup_product.find("img", class_="product-image__main-img").get("src")}')
                        print(f'-- TITLE "{title}"')
                        print(f'-- BRAND "{brand}"')
                        for p in prices:
                            p = p.find_all("div")
                            titles = ["goods", "price", "price_online_pickup", "price_online_delivery"]
                            for i, j in zip(titles, p[:-2]):
                                j = j.text.replace("\n", " ").strip()
                                print(f'-- {i} = {j}')
                                dict_[i] = j
                            print(dict_)
                        print("---------------------------------------------------------------------")

                    page += 1

                    if not soup.find("a", class_="pagination__link pagination__link_next"):
                        break


def main():
    parser_ezoo()


if __name__ == "__main__":
    main()

