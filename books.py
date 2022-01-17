import logging, os, json
import datetime, aiofiles
from ruia import Item, AttrField, ElementField, TextField, Spider, Response

OUTDIR = "output/books/" + datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
BASE_URL = "https://books.toscrape.com/"
LASTPAGE = 50


class BookItem(Item):
    target_item = TextField(css_select=".page_inner")
    title = TextField(css_select="h1")
    description = TextField(css_select="div#product_description + p")
    price = TextField(css_select="p.price_color")
    rating = AttrField(css_select=".star-rating", attr="class")
    category = TextField(xpath_select='//ul[@class="breadcrumb"]/li[last()-1]/a')
    upc = ElementField(xpath_select="//table/tr")
    image = AttrField(css_select="#product_gallery > div > div > div > img", attr="src")

    async def clean_price(self, value: str):
        return value.strip("£")

    async def clean_rating(self, value: str):
        value = value.split(" ")[-1]
        if value == "One":
            return 1
        if value == "Two":
            return 2
        if value == "Three":
            return 3
        if value == "Four":
            return 4
        if value == "Five":
            return 5
        return 0

    async def clean_upc(self, value):
        return value.xpath("td[1]")[0].text

    async def clean_image(self, value: str):
        prefix = "../../"
        return value.removeprefix(prefix)

    def to_dict(self):
        dic = self.__dict__
        img_file = self.image.__str__().split("/")[-1]
        return {
            "upc": self.upc,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "rating": str(self.rating),
            "category": self.category,
            "image_file": img_file,
        }


class BookLink(Item):
    target_item = TextField(css_select="h3")
    link = AttrField(css_select="a", attr="href")

    async def clean_link(self, value):
        return f"{BASE_URL}catalogue/{value}"


class PageItem(Item):
    target_item = TextField(css_select="section")


class BooksSpider(Spider):
    concurrency = 5
    start_urls = [
        f"{BASE_URL}catalogue/page-{index}.html" for index in range(1, LASTPAGE + 1)
    ]

    async def parse(self, response: Response):
        book_urls = []
        async for item in BookLink.get_items(html=await response.text()):
            book_urls.append(item.link)
        # book_urls = book_urls[:3]
        async for response in self.multiple_request(book_urls, is_gather=True):
            yield self.parse_book(response)

    async def parse_book(self, response: Response):
        book: BookItem = await BookItem.get_item(html=await response.text())

        data = book.to_dict()
        json_file = f"{OUTDIR}/{book.upc}.json"
        image_file = data["image_file"]
        image_url = f"{BASE_URL}{book.image}"
        async with aiofiles.open(json_file, "w") as f:
            self.logger.info(f"writing book json {book.upc}")
            await f.write(json.dumps(data))
        yield self.request(
            url=image_url,
            metadata={"filename": f"{OUTDIR}/{image_file}"},
            callback=self.save_image,
        )

    async def save_image(self, response: Response):
        try:
            content = await response.read()
        except Exception as e:
            self.logger.error(e)
        else:
            filename = response.metadata["filename"]
            async with aiofiles.open(filename, "wb") as f:
                await f.write(content)
                self.logger.info(f"saved image {filename}")


async def after_start_fn(spider: Spider):
    logger = logging.getLogger("Ruia")
    print(f"{logger}")
    # logger.setLevel(logging.CRITICAL)
    # print(f"{logger}")
    logger.info(f"output data to {OUTDIR}")
    os.mkdir(OUTDIR)


if __name__ == "__main__":
    BooksSpider.start(after_start=after_start_fn)
