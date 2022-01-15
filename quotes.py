import aiofiles
import json

from ruia import Item, TextField, AttrField, Spider, Response

START_URL = "http://quotes.toscrape.com"
OUTFILE = "output/quotes.jsonl"


class QuotesItem(Item):
    target_item = TextField(css_select=".quote")
    text = TextField(css_select="span.text")
    author = TextField(css_select="small.author")
    tags = TextField(css_select="a.tag", many=True, default="")

    @staticmethod
    async def clean_text(value: str):
        stripped = value.strip("“”")
        return stripped.replace('"', '\\"')

    @staticmethod
    async def clean_tags(value):
        return json.dumps(value)


class QuotesSpider(Spider):
    start_urls = [START_URL]
    concurrency = 3

    async def parse(self, response: Response):
        async for item in QuotesItem.get_items(html=await response.text()):
            yield item
        next_page = AttrField(css_select="li.next a", attr="href", default="")
        next_ref = next_page.extract(
            html_etree=response.html_etree(html=response._html)
        )
        if next_ref:
            next_page_url = START_URL + str(next_ref)
            yield self.request(url=next_page_url, callback=self.parse)

    async def process_item(self, item: QuotesItem):
        async with aiofiles.open(OUTFILE, "a") as f:
            await f.write(
                f'{{"text":"{item.text}", "author": "{item.author}", "tags": {item.tags}}}\n'
            )


async def after_start_fn(spider: Spider):
    import os

    spider.logger.info("Backup outfile")
    if os.path.exists(OUTFILE):
        os.rename(OUTFILE, OUTFILE + ".bak")
        # os.unlink(OUTFILE)


async def before_stop_fn(spider):
    spider.logger.info("Before stop!")


if __name__ == "__main__":
    QuotesSpider.start(after_start=after_start_fn, before_stop=before_stop_fn)
