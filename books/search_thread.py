import html
import asyncio
from typing import AsyncGenerator
import aiohttp
from bs4 import BeautifulSoup
from thefuzz import fuzz

from log import Log
from search_result import SearchResult


async def search_books(author: str, title: str, format: str = None) -> AsyncGenerator[SearchResult, None]:
    query = f"{author} {title}".strip()

    async with aiohttp.ClientSession() as session:
        try:
            Log.info(f"Searching for {query}...")

            for page in range(1, 10):
                url = f"https://libgen.li/index.php?req={query}&res=100&page={page}"
                Log.info(f"Requesting {url}")

                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP Error {response.status}")

                    content = await response.text()
                    doc = BeautifulSoup(content, "html.parser")
                    table = doc.select_one("table#tablelibgen tbody")
                    if not table:
                        break

                    rows = table.select("tr")
                    for row in rows:
                        columns = row.select("td")
                        title_cell = columns[0].select_one("a[data-toggle='tooltip']")
                        title_text = title_cell["title"]
                        title_text = html.unescape(title_text)
                        title_text = title_text.split("<br>")[1]

                        authors = columns[1].text.strip().split(";")
                        author_names = ", ".join([fix_author(author) for author in authors])

                        if len(author_names) > 40:
                            author_names = author_names[:40] + "..."

                        series = columns[0].select_one("b").text.strip() if columns[0].select_one("b") else ""
                        language = columns[4].text.strip()
                        if language.lower() != "english":
                            continue

                        file_info = columns[6].select_one("nobr a").text.strip()
                        size = file_info.upper() if file_info else "N/A"
                        extension = columns[7].text.strip().upper()
                        if format and extension != format.upper():
                            continue

                        mirrors = columns[8].select("a[data-toggle='tooltip']")
                        mirror_links = [f"https://libgen.li{mirror['href']}" for mirror in mirrors]

                        author_score = fuzz.token_sort_ratio(author, author_names)
                        title_score = fuzz.token_sort_ratio(title, title_text)
                        score = (author_score + title_score) / 2

                        yield SearchResult(
                            author_names,
                            series,
                            title_text,
                            extension,
                            size,
                            score,
                            mirror_links
                        )

                        await asyncio.sleep(0.1)

            Log.info("Search complete.")

        except Exception as e:
            Log.info(str(e))
            raise


def fix_author(author: str) -> str:
    if "," in author:
        parts = author.split(",")
        return f"{parts[1].strip()} {parts[0].strip()}"
    return author
