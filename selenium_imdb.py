import hashlib
from selenium import webdriver
import time, os, requests, io
from bs4 import BeautifulSoup
from PIL import Image
from math import floor

# Macroparameters to set before running
from selenium.webdriver.common.keys import Keys

DRIVER_PATH = "chromedriver.exe"
sample_size = 5
search_url_imdb = "https://www.imdb.com/find?q={q}&ref_=nv_sr_sm"

def bs_get_page(name: str):
    response = requests.get(search_url_imdb.format(q=name).replace(" ", "+"))
    html_soup = BeautifulSoup(response.text, 'html.parser')
    link = html_soup.find('td', class_='result_text')  # div class where actor names listed
    if (link.a.text) == name:
        page = link.a.get('href').strip()
        return ('https://imdb.com'+ page + 'mediaindex') # could also add /?page=1...2...etc
    else:
        return

def fetch_image_urls_bs(actor_page: str):
    response = requests.get(actor_page)
    html_soup = BeautifulSoup(response.text, 'html.parser')
    link = html_soup.find('div', class_='media_index_thumb_list')
    print(link)
    images_soup = BeautifulSoup(link.text, 'html.parser')
    #print(images_soup)
    images = images_soup.findAll('img')
    #print(images)

    iterator = 1
    links = []
    while iterator <= 48:

        iterator += 1
    if (link.a.text) == name:
        page = link.a.get('href').strip()
        return ('https://imdb.com' + page + 'mediaindex')  # could also add /?page=1...2...etc
    return links

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver,
                     sleep_between_interactions: 1, search_url: str = search_url_imdb):
    # query field currently not used because generating imdb's custom hash in def method above
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    # load the page
    wd.get(query)

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        # scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = (wd.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/a"))
        number_results = len(thumbnail_results)

        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            actual_images = wd.find_elements_by_xpath('/html/head/meta[7]')
            for actual_image in actual_images:
                if actual_image.get_attribute('content') and 'http' in actual_image.get_attribute('content'):
                    image_urls.add(actual_image.get_attribute('content'))
            return image_urls

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        # else:
        #     print("Found:", len(image_urls), "image links, looking for more ...")
        #     time.sleep(30)
        #     return
        #     load_more_button = wd.find_element_by_css_selector(".mye4qd")
        #     if load_more_button:
        #         wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls

maxwidth = 1000
maxheight = 1000
def persist_image(folder_path:str,url:str):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path,hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            width, height = image.size
            aspect_ratio = min(maxwidth / width, maxheight / height)
            new_width = floor(aspect_ratio * width)
            new_height = floor(aspect_ratio * height)
            if width > maxwidth or height > maxheight:
                image = image.resize((new_width, new_height), Image.ANTIALIAS)
            width, height = image.size
            if width < maxwidth and height < maxheight:
                image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

# stadard download size is 5, can be overriden above
def search_and_download(search_term: str, driver_path: str, target_path='./dataset/images_imdb', number_images=5):
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with webdriver.Chrome(executable_path=driver_path) as wd:
        print(bs_get_page(search_term))
        res = fetch_image_urls(bs_get_page(search_term), number_images, wd=wd, sleep_between_interactions=1)

    for elem in res:
        persist_image(target_folder, elem)

# Running the search
with open("dataset/imdbactors.txt","r") as input:
    search_terms = input.readlines()
for item in search_terms:
    search_term = item.strip()
    search_and_download(search_term=search_term, driver_path=DRIVER_PATH, number_images= sample_size)
