import sys
from datetime import datetime, timedelta
import httpx
import asyncio
import platform
import json


class HttpError(Exception):
    pass


class CurrencyRateFetcher:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def fetch_rates(self, date: str):
        url = f'{self.base_url}/p24api/exchange_rates?date={date}'
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            if r.status_code == 200:
                return r.json()
            else:
                raise HttpError(f"Error status: {r.status_code} for {url}")


class CurrencyRateProcessor:
    def __init__(self, fetcher: CurrencyRateFetcher):
        self.fetcher = fetcher

    def format_date(self, delta_days: int) -> str:
        date = datetime.now() - timedelta(days=delta_days)
        return date.strftime("%d.%m.%Y")

    async def get_rates_for_days(self, days: int, currencies: list = ["EUR", "USD"]):
        rates = []
        for i in range(days):
            date = self.format_date(i)
            try:
                response = await self.fetcher.fetch_rates(date)
                rates.append(self.extract_rates(response, date, currencies))
            except HttpError as err:
                print(err)
        return rates

    def extract_rates(self, response, date: str, currencies: list):
        rates_for_day = {date: {}}
        for currency in currencies:
            currency_data = next((item for item in response['exchangeRate'] if item['currency'] == currency), None)
            if currency_data:
                rates_for_day[date][currency] = {
                    'sale': currency_data['saleRate'],
                    'purchase': currency_data['purchaseRate']
                }
        return rates_for_day


async def main(index_day):
    try:
        days = int(index_day)
    except ValueError:
        days = 1
    fetcher = CurrencyRateFetcher('https://api.privatbank.ua')
    processor = CurrencyRateProcessor(fetcher)
    rates = await processor.get_rates_for_days(days)
    print(json.dumps(rates, indent=2))


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        index_day = sys.argv[1]
    except IndexError:
        index_day = 1
    asyncio.run(main(index_day))
