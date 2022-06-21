import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from prettytable import PrettyTable


def parse(index_station1, index_station2, current_d):
    user_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; hu-HU; rv:1.7.8) Gecko/20050511 Firefox/1.0.4'}
    url = f"https://swrailway.gov.ua/timetable/eltrain/?sid1={index_station1}&sid2={index_station2}&eventdate={current_d}"
    source_code = requests.get(url, headers=user_agent, verify='swrailway-gov-ua-chain.pem').text
    soup = BeautifulSoup(source_code, "lxml")

    table_parse = soup.find('table', class_='td_center')

    data_set = {
        'days': {
            'value': [],
            'index': 1
        },
        'route': {
            'value': [],
            'index': 2
        },
        'departure_time_1': {
            'value': [],
            'index': 5
        },
        'arrival_time_2': {
            'value': [],
            'index': 6
        },
    }

    for row in table_parse.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) != 13:
            continue
        for key in data_set:
            data_set[key]['value'].append(columns[data_set[key]['index']].text.strip())

    for key, item in data_set.items():
        data_set[key] = item['value']
    return data_set


def table(index_station1, index_station2, station1, station2, date):
    result_parse = parse(index_station1, index_station2, date)
    table_fields = ['Обіг', 'Маршрут', f'Час відправлення з {station1}', f'Час прибуття до {station2}']
    table_data = PrettyTable(table_fields)
    table_data.title = f'Розклад електричок з {station1} до {station2} на {date}'
    table_data.add_rows(
        [
            [result_parse[i][train] for i in result_parse] for train in range(len(result_parse['days']))
        ]
    )
    table_data = table_data.get_string()

    image_width = 775 + ((len(station1)+len(station2)) * 9)
    image_height = 90 + (len(result_parse['days'] * 20))
    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("FreeMono.ttf", 15)
    draw.text((10, 10), str(table_data), font=font, fill="black")
    image.save("tableData.png")
    return table_data
