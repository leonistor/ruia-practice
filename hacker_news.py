import asyncio, aiofiles, json
from ruia import Item, TextField, AttrField, Spider, Response


class HackerNewsItem(Item):
    target_item = TextField(css_select="tr.athing")
    title = TextField(css_select="a.titlelink")
    url = AttrField(css_select="a.titlelink", attr="href")


async def test_item():
    url = "https://news.ycombinator.com/news?p=1"
    async for item in HackerNewsItem.get_items(url=url):
        print(f"{json.dumps(item.__dict__)}")


class HackerNewsSpider(Spider):
    concurrency = 2
    start_urls = ["https://news.ycombinator.com/news?p={index}" for index in range(3)]

    async def parse(self, response: Response):
        async for item in HackerNewsItem.get_items(html=await response.text()):
            yield item

    async def process_item(self, item: HackerNewsItem):
        async with aiofiles.open("output/hacker_news.jsonl", "a") as f:
            await f.write(f'{{"url":"{item.url}", "title": "{item.title}"}}\n')


if __name__ == "__main__":
    # asyncio.run(test_item())
    HackerNewsSpider.start()
