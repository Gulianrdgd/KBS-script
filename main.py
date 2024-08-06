import os
import random
import smtplib, ssl
import requests
import cssutils
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

def send_email(houses):

    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()

    email = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_PASS')
    receiver = os.getenv('RECEIVER_EMAIL')

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

            link = text_block[0].find_next('a')['href']
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
                full = full.text == 'Verhuurd'
            else:
                full = False

            price = house.find('div', class_='card-house__price').text
            price = price.replace('€', '').replace('per maand', '').replace(' ', '').replace(',', '').replace('-', '').replace('.', '', price.count('.') - 1).strip()
            image = house.find('img')['src']
            link = house.find_next('a')['href']

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

def extract_houses_stmakelaars(soup):
    houses = []
    for house in soup.find_all('div', class_='card--object'):
        try:
            title = house.find_next('h5').text
            full = house.find_next('span')


            print(title)

            if full is not None:
                full = full.text == 'Verhuurd'
            else:
                full = False

            price = house.find_next('strong').text
            price = price.replace('€', '').split('p.m.')[0].replace(' ', '').replace(',', '').replace('-', '').replace('.', '', price.count('.') - 1).strip()
            image = house.find('img')['src']
            link = house.find_next('a')['href']

            print(full, price, image, link)
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

def main():
    old_houses = {}
    url_kbs = "https://kbsvastgoedbeheer.nl/aanbod/"
    url_max = ("https://mvxvastgoedbeheer.nl/aanbod?city=&type_of_house=Studio&minimum_price=0&maximum_price=900"
               "&amount_of_rooms=&status=&square_meters=&amount_of_sleeping_rooms=&amount_of_bathrooms=&garden"
               "=&balcony=&salvage=&parking_available=&sort-by=price-ascending")
    url_wouw = 'https://www.vdwouwvastgoedbeheer.nl/aanbod/'
    url_rotsvast = 'https://www.rotsvast.nl/woningaanbod/rotsvast-nijmegen/?type=2&office=RV013&maximumPrice[2]=900'
    url_nederwoon = "https://www.nederwoon.nl/search?search_type=&type=&rooms=&completion=&sort=1&city=Nijmegen"
    url_hans_janssen = "https://www.hansjanssen.nl/wonen/zoeken/Nijmegen/huur/"
    url_stmakelaars = "https://stmakelaars.nl/wonen/aanbod?buy_rent=rent&distance=5&search=Nijmegen&order_by=created_at-desc&page=1"

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


        houses = list(filter(lambda x: not x['full'] and 'Nijmegen' in x['location'] and float(x['price']) < 900, houses))
        print(houses)

        houses_ready_to_email = []

        for house in houses:
            if not (house['link'] in old_houses):
                print("Not in!")
                houses_ready_to_email.append(house)
                old_houses[house['link']] = house

        if len(houses_ready_to_email) > 0:
            send_email(houses_ready_to_email)

        print(old_houses)

        time.sleep(300 + random.randint(0, 100))


if __name__ == "__main__":
    main()
