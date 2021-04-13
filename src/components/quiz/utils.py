import aiohttp
from bs4 import BeautifulSoup
import asyncio
from pylatexenc.latex2text import LatexNodes2Text
from urllib.parse import urljoin

session = aiohttp.ClientSession()


async def IB(url):
    # LOAD NEW EMOJI
    async with session.get(url) as resp:
        data = await resp.read()
    soup = BeautifulSoup(data, 'html.parser')

    info_values = soup.find_all('td', {'class': 'info_value'})

    question_type = None

    for v in info_values:
        if "Paper" in v.text:
            question_type = v.text

    if question_type == "Paper 1":

        questionblocks = soup.find_all('div', {'class': 'question'})

        # First block definitely has some paragraphs in it (unless double image)

        segments = []

        for blk in questionblocks:
            segments.append(LatexNodes2Text().latex_to_text(blk.text))

        question = [line for line in segments[0].splitlines() if len(line) > 0] + \
            [line for line in segments[1].splitlines() if len(line) > 0]

        question.insert(1, "")
        return question

    else:
        print(f"Question Type is: {question_type}, which is not supported right now.")
        return question_type

async def obtain(url):
    '''
    Obtains all questions off a core questions page
    '''
    async with session.get(url) as resp:
        data = await resp.read()
    soup = BeautifulSoup(data, 'html.parser')
    links = soup.find_all('a', href=True)

    for link in links:
        question = await IB(urljoin(url, link["href"]))
        print(question)


if __name__ == "__main__":
    url = '''https://www.ibdocuments.com/IB%20QUESTIONBANKS/4.%20Fourth%20Edition/questionbank.ibo.org/en/teachers/00000/questionbanks/43-dp-biology/questions/86580.html'''
    qs = "https://www.ibdocuments.com/IB%20QUESTIONBANKS/4.%20Fourth%20Edition/questionbank.ibo.org/en/teachers/00000/questionbanks/46-dp-physics/syllabus_sections/2595.html"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(obtain(qs))
