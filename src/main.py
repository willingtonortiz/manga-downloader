import os
import urllib.request
import json
import re
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning
import requests
from fpdf import FPDF
from PIL import Image
from bs4 import BeautifulSoup


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Constants and templates
referer_header = 'https://inmanga.com/'

base_chapter_list_url = "https://inmanga.com/chapter/getall?mangaIdentification={}"
# "https://inmanga.com/chapter/getall?mangaIdentification={mangaIdentification}"

base_chapter_url = "https://inmanga.com/chapter/chapterIndexControls?identification={}"
# "https://inmanga.com/chapter/getall?mangaIdentification={anime_id}"

base_image_url = "https://pack-yak.intomanga.com/images/manga/{}/chapter/{}/page/{}/{}"
# "https://pack-yak.intomanga.com/images/manga/{anime_name}/chapter/{chapter_number}/page/{page_number}/{page_id}"

base_image_folder = "./images/{}/{}"
# "./images/{anime_name}/{chapter_number}"

base_image_path = "./images/{}/{}/{}.jpeg"
# "./images/{anime_name}/{chapter_number}/{page_number}"


def add_zeroes(number):
    return str(number).zfill(3)


# (page, 3) -> page-003
# (chapter, 3) -> chapter-003
def append_number(text, page):
    return f"{text}-{add_zeroes(page)}"


def get_chapter_name(number):
    return append_number('chapter', number)


def get_page_name(page):
    return append_number('page', page)


# chapter_name -> TokyoGhoul; page_name ->
def get_image_name(chapter_number, page):
    return f"{get_chapter_name(chapter_number)}_{get_page_name(page)}"


def get_image_path(anime_name, chapter_number, page_number):
    return base_image_path.format(
        anime_name,
        get_chapter_name(chapter_number),
        get_image_name(chapter_number, page_number)
    )


def download_image_in_path(url, path):
    urllib.request.urlretrieve(url, path)


def generate_chapter_pdf():
    pdf = FPDF()

    chapter_info = {
        'name': 'tokyo_ghoul_86',
        'chapters_count': 20
    }
    image_list = [
        f'./images/{chapter_info["name"]}/{get_image_name(chapter_info["name"], i)}' for i in range(1, chapter_info['chapters_count'])
    ]

    for image_path in image_list:
        image = Image.open(image_path)
        width, height = image.size
        page_orientation = 'P' if width < height else 'L'
        page_width = 210 if width < height else 297
        page_height = 297 if width < height else 210

        pdf.add_page(page_orientation)
        pdf.image(image_path, 0, 0, page_width, page_height)
    pdf.output('./tokyo_ghoul_86.pdf', 'F')


def create_chapter_folder(anime_name, chapter_number):
    image_folder = base_image_folder.format(
        anime_name, get_chapter_name(chapter_number)
    )
    if not os.path.isdir(image_folder):
        os.makedirs(image_folder)


def download_all_chapters(anime_id):
    opener = urllib.request.build_opener()
    opener.addheaders = [('Referer', referer_header)]
    urllib.request.install_opener(opener)

    response = requests.get(base_chapter_list_url.format(anime_id))
    data = json.loads(response.text)['data']
    chapters = json.loads(data)['result']
    chapters.sort(key=lambda chapter: chapter['Number'])

    for chapter in chapters:
        chapter_number = str(int(chapter['Number']))
        identification = chapter['Identification']
        chapter_url = base_chapter_url.format(identification)
        page = requests.get(chapter_url)

        soup = BeautifulSoup(page.text)
        anime_name = soup.select_one("#FriendlyMangaName")['value']
        pages = soup.select('select.PageListClass:first-of-type > option')
        pages_half = len(pages) // 2
        pages = pages[:pages_half]

        create_chapter_folder(anime_name, chapter_number)

        for index, option in enumerate(pages):
            page_number = index + 1
            page_id = option['value']
            image_url = base_image_url.format(
                anime_name, chapter_number, page_number, page_id
            )
            image_path = get_image_path(
                anime_name, chapter_number, page_number
            )
            download_image_in_path(image_url, image_path)
            print(f'{image_path} downloaded')
        print(f'Chapter {chapter_number} downloaded')


def get_page_props(width, height):
    page_orientation = 'P' if width < height else 'L'
    page_width = 210 if width < height else 297
    page_height = 297 if width < height else 210
    return (page_orientation, page_width, page_height)


def generate_anime_pdfs(directory_path):
    folders = os.scandir(directory_path)
    for chapter_dir in folders:
        pdf = FPDF()
        pages = sorted(Path(chapter_dir.path).iterdir(), key=os.path.getmtime)

        for chapter_page in pages:
            image_path = str(Path(chapter_page).absolute())
            image = Image.open(image_path)
            width, height = image.size
            page_orientation, page_width, page_height = get_page_props(
                width, height
            )
            pdf.add_page(page_orientation)
            pdf.image(image_path, 0, 0, page_width, page_height)

        pdf.output(f'./pdfs/Tokyo-Ghoul/{chapter_dir.name}.pdf', 'F')
        print(f"Chapter {chapter_dir.name} generated")


def main():
    # tokyo_ghoul_id = "5b2d24eb-5de6-4fc7-a56a-fc6dd6510b7c"
    kaguya_sama_id = "030de05e-ef8f-4cfe-a349-89b4599f6bf5"
    download_all_chapters(kaguya_sama_id)

    # anime_directory_path = "./images/Tokyo-Ghoul"
    # generate_anime_pdfs(anime_directory_path)


if __name__ == "__main__":
    main()
