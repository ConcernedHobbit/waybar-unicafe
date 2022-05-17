#!/usr/bin/env python3
# scuffed as hell.
import datetime
import urllib.request
import re
import json

API_URI = 'https://messi.hyyravintolat.fi/publicapi'

class MenuEntry:
    _VEGETARIAN_REGEX = re.compile('kala|äyriäis|silakka|lohi|kana|broileri|nau(ta|dan)|kebab|jauheliha|porsa(s|an)', re.IGNORECASE)

    def __init__(self, \
            date: str, \
            name_fi: str = None, name_en: str  = None, name_sv: str  = None, \
            price_name: str  = None, prices: dict[str, str]  = None, \
            ingredients: str  = None, allergens: list[str]  = None, tags: list[str]  = None, additional_information: list[str] = None, \
            nutrition: str = None):
        self.date = MenuEntry._parse_date(date)
        
        self.name_fi = name_fi
        self.name_en = name_en
        self.name_sv = name_sv

        self.price_name = price_name
        self.prices = prices

        self.ingredients = ingredients
        self.allergens = allergens
        self.tags = tags
        self.additional_information = additional_information

        self.nutrition = nutrition

    def is_vegan(self) -> bool:
        if 'VE' in self.tags: return True

    def is_vegetarian(self) -> bool:
        if self.is_vegan(): return True
        if 'Pyydä Ve' in self.tags: return True
        if self._VEGETARIAN_REGEX.search(self.ingredients): return False
        return True

    def _parse_date(datestr: str) -> datetime.date:
        # Assumptions made:
        # - always given english datestring (date_en)
        # - english datestring weekday is always len(3)
        # - english datestring format is {weekday} {dd.mm}
        date = int(datestr[4:6])
        month = int(datestr[7:])
        return datetime.date(datetime.datetime.now().year, month, date)

    def __str__(self) -> str:
        return ("MenuEntry\n"
            f"date: {self.date:%Y-%m-%d}\n"
            f"names: {self.name_fi} {self.name_en} {self.name_sv}\n"
            f"price: {self.price_name} {self.prices}\n"
            f"{self.ingredients = } {self.allergens = } {self.tags = } {self.additional_information = } {self.nutrition = }"
        )

class UnicafeUtil:
    # Assume that tree root passed is data (essentially a list)
    def parse_restaurant_data(data: dict) -> list[MenuEntry]:
        entries = []

        for weekday in data:
            date_en = weekday['date_en']
            menu_entries = weekday['data']

            for menu_entry in menu_entries:
                entry = MenuEntry(date_en)
                entry.name_fi = menu_entry['name']
                entry.name_en = menu_entry['name_en']
                entry.name_sv = menu_entry['name_sv']

                entry.ingredients = menu_entry['ingredients']
                entry.nutrition = menu_entry['nutrition']

                price_details = menu_entry['price']
                entry.price_name = price_details['name']
                entry.prices = price_details['value']

                meta_entries = menu_entry['meta']
                entry.tags = meta_entries['0']
                entry.allergens = meta_entries['1']
                entry.additional_information = meta_entries['2']
                
                entries.append(entry)
        
        return entries

class Restaurant:
    def __init__(self, \
            id: int, name: str = None, area_code: int = None, address: str = None,\
            opens_at: str = None, closes_at: str = None, open_days: list = None, closed: bool = None, \
            menu: list[MenuEntry] = None):
        self.id = id
        self.name = name
        self.area_code = area_code
        self.address = address

        self.opens_at = opens_at
        self.closes_at = closes_at
        self.open_days = open_days

        self.closed = closed
        self.menu = menu

        self.__last_fetched = None

    def _parse(self, data) -> None:
        status = data['status']
        if status != 'OK':
            print(f"Data status is {status}, aborting")
            return

        information = data['information']
        self.name = information['restaurant']
        self.address = information['address']

        self.closed = information['business']['exception'][0]['closed']
        opening_times = information['business']['regular'][0]
        self.opens_at = opening_times['open']
        self.closes_at = opening_times['close']
        self.open_days = list(filter(lambda x: x != False, opening_times['when']))

        self.menu = UnicafeUtil.parse_restaurant_data(data['data'])

    def get_menu_by_date(self, date: datetime) -> list[MenuEntry]:
        return list(filter(lambda x: x.date == date and x.price_name != 'Tiedoitus', self.menu))

    def get_tooltip(self, date: datetime) -> str:
        if self.closed: return f"<b>{self.name}</b>\n<i>Closed</i>"
        return_string = f"<b>{self.name}</b>\n"
        return_string += f"<i>{self.opens_at} - {self.closes_at}</i>"
        for menu_item in self.get_menu_by_date(date):
            return_string += "\n"
            if menu_item.is_vegan():
                return_string += "<b>VE</b>  "
            elif menu_item.is_vegetarian():
                return_string += "  "
            else:
                return_string += "    "
            return_string += f"{menu_item.name_fi}"

        return return_string

    def fetch(self) -> None:
        restaurant_url = f'{API_URI}/restaurant/{self.id}'
        with urllib.request.urlopen(restaurant_url) as url:
            data = json.loads(url.read().decode())
            self._parse(data)

    def __str__(self) -> str:
        return (
            f"Restaurant id {self.id}\n"
            f"{self.name = } {self.address = }\n"
            f"{self.closed = } {self.open_days = }\n"
            f"{self.opens_at = } {self.closes_at = }\n"
            f"{len(self.menu)} menu items"
        )

if __name__ == "__main__":
    export = {}

    tracked_restaurants = [Restaurant(10), Restaurant(11)]
    for restaurant in tracked_restaurants:
        restaurant.fetch()
    
    today = datetime.date.today()
    export['tooltip'] = ""
    for restaurant in tracked_restaurants:
        export['tooltip'] += restaurant.get_tooltip(today)
        export['tooltip'] += "\n\n"

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    export['tooltip'] += "<b>Tomorrow:</b>\n"
    for restaurant in tracked_restaurants:
        export['tooltip'] += restaurant.get_tooltip(tomorrow)
        export['tooltip'] += "\n\n"

    export['tooltip'] = export['tooltip'][:-2]
    export['text'] = "Unicafe"

    print(json.dumps(export))

