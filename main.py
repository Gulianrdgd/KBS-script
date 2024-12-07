import os
import pickle
import random
import smtplib, ssl
from types import NoneType

import requests
import cssutils
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

def send_email(houses, receiver):

    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()

    email = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_PASS')

    message = MIMEMultipart("alternative")
    message["Subject"] = "Nieuwe kamers!"
    message["From"] = email
    message["To"] = receiver

    text = "Nieuwe huizen gevonden! \n\n" + "\n".join(
        list(map(lambda h: f"<br/><div>{h['title']} - {h['price']} euro </div><br/><img style='width:300px;height:"
                           f"200px;background-size: cover;background-position: center;background-repeat: no-repeat;' "
                           f"src='{h['image']}'> <br/> Type: {h['type']} \n <a href='{h['link']}'>Link</a> <br/>", houses)))
    plain = MIMEText(text, "html")

    message.attach(plain)

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(email, password)
        server.sendmail(email, receiver, message.as_string())

def extract_houses_max(soup):
    houses = []
    for house in soup.select('a.relative.flex.flex-col.p-2.bg-ice.group'):
        try:
            title = house.find_next('h2').text
            price = house.find('dd').text.replace('€', '').replace('p/m', '').replace(' ', '').replace(',', '.')
            price = price.replace('.', '', price.count('.') - 1)

            location = house.find_next('p').text
            link = house['href']
            image = house.find('img')['src']
            verhuurd = house.select("div.orange.text-ice")
            full = len(verhuurd) > 0 and verhuurd[0].text == "Verhuurd"

            houses.append({
                'title': title,
                'price': price,
                'type': "unknown",
                'location': location,
                'image': image,
                'full': full,
                'link': link
            })
        except Exception as e:
            print(e)
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def extract_houses_nederwoon(soup):
    houses = []
    for house in soup.find_all('div', class_='location'):
        try:
            text_block = house.find_all('div', class_='click-see-page-button')
            text_block_ps = text_block[0].find_all('p')
            if 'Garagebox' in text_block_ps[1].text or 'Parkeerplaats' in text_block_ps[1].text:
                continue

            title = text_block[0].find_next('a').text

            price = text_block[1].find_next('p').text.replace('€', '').replace('p/mnd', '').replace(' ', '').replace(',', '.').replace('incl.', '').replace('excl.', '').strip()
            price = price.replace('.', '', price.count('.') - 1)

            location = 'Nijmegen'

            link = 'https://www.nederwoon.nl' + text_block[0].find_next('a')['href']
            image = 'https://www.nederwoon.nl' + house.find_next('img')['data-src']
            full = False

            houses.append({
                'title': title,
                'price': price,
                'type': "unknown",
                'location': location,
                'image': image,
                'full': full,
                'link': link
            })
        except Exception as e:
            print(e)
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def extract_houses_wouw(soup):
    houses = []
    for house in soup.find_all('div', class_='pt-cv-ifield'):
        try:
            title = house.find_next('h4').find_next('a').text
            if len(house.select('div.pt-cv-ctf-prijs')) == 0:
                continue
            price = house.find('div', class_="pt-cv-ctf-prijs").find_next('div').text
            price = price.replace('.', '', price.count('.') - 1)

            location = 'Nijmegen'
            link = house.find('a')['href']
            image = house.find('a').find_next('img')['src']
            full = house.find('div', class_="pt-cv-ctf-status").find_next('div').text != "Te huur"

            houses.append({
                'title': title,
                'price': price,
                'type': "unknown",
                'location': location,
                'image': image,
                'full': full,
                'link': link
            })
        except Exception as e:
            print(e)
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def extract_houses_rotsvast(soup):
    houses = []
    for house in soup.find_all('div', class_='residence-gallery'):
        try:
            title = house.find('div', class_='residence-street').text + " " + house.find('div', class_='residence-zipcode-place').text
            status = house.find('div', class_='status').text
            full = "Verhuurd" in status or status == "Bezichtiging vol"

            price = house.find('div', class_='residence-price').text.replace('€', '').replace('p/mnd', '').replace(' ', '').replace(',', '.').replace('incl.', '').replace('excl.', '').strip()
            price = price.replace('.', '', price.count('.') - 1)

            image_style = house.find('div', class_='residence-image')['style']
            style = cssutils.parseStyle(image_style)
            image = style['background-image'].replace('url(', '').replace(')', '')

            type = 'Unknown'
            location = 'Nijmegen'
            link = house.find('a')['href']

            houses.append({
                'title': title,
                'price': price,
                'type': type,
                'image': image,
                'location': location,
                'link': link,
                'full': full
            })
        except Exception as e:
            print(e)
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def extract_houses_kbs(soup):
    houses = []
    for house in soup.find_all('div', class_='woning'):
        try:
            title = house.find('p').text
            full = False
            if title == 'Bezichtiging vol / Viewing list full' or 'Verhuurd / Rented out':
                title = house.find_next('p').find_next('p').text
                full = True
            price = house.find('div', class_='gb-container').find_all('p')[1].text
            price = price.replace('.', '', price.count('.') - 1)

            sep = house.find('hr')
            image = house.find('img')['src']
            type = sep.find_next('p').text
            location = sep.find_next('p').find_next('p').text
            link = house.find('a')['href']
            houses.append({
                'title': title,
                'price': price,
                'type': type,
                'image': image,
                'location': location,
                'link': link,
                'full': full
            })
        except Exception as e:
            print(e)
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def extract_houses_hans_janssen(soup):
    houses = []
    for house in soup.find_all('div', class_='js-house-item'):
        try:
            title = house.find('div', class_='card-house__title').find_next('h6').text
            full = house.find('div', class_='card-house__label')
            if full is not None:
                full = full.text.strip() == 'Verhuurd'
            else:
                full = False

            price = house.find('div', class_='card-house__price').text
            price = price.replace('€', '').replace('per maand', '').replace(' ', '').replace(',', '').replace('-', '').replace('.', '').strip()
            image = 'https://www.hansjanssen.nl' + house.find_all('img')[1]['src']

            if not full:
                link = house.find_next('a')['href']
            else:
                link = 'unknown'

            type = 'Unknown'
            location = 'Nijmegen'

            houses.append({
                'title': title,
                'price': price,
                'type': type,
                'image': image,
                'location': location,
                'link': link,
                'full': full
            })
        except Exception as e:
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def extract_houses_dolfijn(soup):
    houses = []

    for house in soup.find_all('article', class_='objectcontainer'):
        try:

            data_short = house.find('div', class_='datashort')

            title = data_short.find('span', class_='street').text
            location = data_short.find('span', class_='location').text

            status = house.find('span', class_='object_status')
            if status is not None:
                full = status.text.strip() == 'Verhuurd'
            else:
                full = False

            if not full:
                price = data_short.find('span', class_='obj_price').text.replace('€', '').replace(',-','').replace('/mnd', '').replace('p/m', '').replace(' ', '').replace(',', '.').replace('excl.', '').replace('incl.', '').strip()
                price = price.replace('.', '', price.count('.') - 1)
            else:
                price = None

            image = house.find('img')['src']
            link = 'https://dolfijnwonen.nl' + house.find('a')['href']

            houses.append({
                'title': title,
                'price': price,
                'type': 'Unknown',
                'image': image,
                'location': location,
                'link': link,
                'full': full
            })
        except Exception as e:
            print(e)
            houses.append({
                'title': 'unknown',
                'price': 'unknown',
                'type': 'unknown',
                'location': 'unknown',
                'image': 'unknown',
                'full': False,
                'link': 'unknown'
            })
    return houses


def filter_per_person(houses, location, price, email, old_houses):
    houses_per_person =  list(filter(lambda x: not x['full'] and location in x['location'] and float(x['price']) < price, houses))

    houses_ready_to_email = []

    for house in houses_per_person:
        if not (house['link'] in old_houses):
            print("Not in!")
            houses_ready_to_email.append(house)

    if len(houses_ready_to_email) > 0:
        send_email(houses_ready_to_email, email)

def main():
    old_houses = {}

    if os.path.exists('old_houses.pkl'):
        with open('old_houses.pkl', 'rb') as f:
            old_houses = pickle.load(f)

    url_kbs = "https://kbsvastgoedbeheer.nl/aanbod/"
    url_max = ("https://mvxvastgoedbeheer.nl/aanbod?city=&type_of_house=Studio&minimum_price=0&maximum_price=900"
               "&amount_of_rooms=&status=&square_meters=&amount_of_sleeping_rooms=&amount_of_bathrooms=&garden"
               "=&balcony=&salvage=&parking_available=&sort-by=price-ascending")
    url_wouw = 'https://www.vdwouwvastgoedbeheer.nl/aanbod/'
    url_rotsvast = 'https://www.rotsvast.nl/woningaanbod/rotsvast-nijmegen/?type=2&office=RV013&maximumPrice[2]=900'
    url_nederwoon = "https://www.nederwoon.nl/search?search_type=&type=&rooms=&completion=&sort=1&city=Nijmegen"
    url_hans_janssen = "https://www.hansjanssen.nl/wonen/zoeken/Nijmegen/huur/"
    url_dolfijn = "https://dolfijnwonen.nl/woningaanbod/huur"

    # Should be changed to the actual searchers
    searchers = [{
        "email": "test@test.com",
        "location": "Nijmegen",
        "price": 900
    },
        {
            "email": "test2@test.com",
            "location": "Nijmegen",
            "price": 500
        },
    ]

    while(True):
        houses = []

        try:
            response = requests.get(url_kbs)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_kbs(soup)
        except Exception as e:
            print(e)

        try:
            response = requests.get(url_max)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_max(soup)
        except Exception as e:
            print(e)

        try:
            response = requests.get(url_wouw)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_wouw(soup)
        except Exception as e:
            print(e)

        try:
            response = requests.get(url_rotsvast)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_rotsvast(soup)
        except Exception as e:
            print(e)

        try:
            response = requests.get(url_nederwoon)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_nederwoon(soup)
        except Exception as e:
            print(e)

        try:
            response = requests.get(url_hans_janssen)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_hans_janssen(soup)
        except Exception as e:
            print(e)

        try:
            response = requests.get(url_dolfijn)
            soup = BeautifulSoup(response.text, 'html.parser')
            houses += extract_houses_dolfijn(soup)
        except Exception as e:
            print(e)

        print(houses)

        for searcher in searchers:
            filter_per_person(houses, searcher['location'], searcher['price'], searcher['email'], old_houses)

        old_houses = list(map(lambda x: x['link'], houses))
        print(old_houses)

        with open('old_houses.pkl', 'wb') as f:
            pickle.dump(old_houses, f)

        time.sleep(300 + random.randint(0, 100))


if __name__ == "__main__":
    main()
