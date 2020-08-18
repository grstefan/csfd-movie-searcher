from bs4 import BeautifulSoup as bs
import requests as rq
import re
import codecs
from queue import PriorityQueue as Queue
from time import sleep, time
import json
import numpy as np
import os
from elasticsearch import Elasticsearch


def collection_url(page):
    return 'https://www.csfd.cz/filmoteky/strana-' + str(page) + '/?film=&user=&ok=Zobrazit&_form_=collection'


def advanced_filer_url(page, genre):
    return 'https://www.csfd.cz/podrobne-vyhledavani/strana-' + str(
        page) + '/?type%5B0%5D=0&genre%5Btype%5D=1&genre%5Binclude%5D%5B0%5D=' + str(
        genre) + '&genre%5Binclude%5D%5B1%5D=&genre%5Bexclude%5D%5B0%5D=&origin%5Btype%5D=2&origin%5Binclude%5D%5B0%5D' \
                 '=&origin%5Bexclude%5D%5B0%5D=&year_from=&year_to=&rating_from=&rating_to=&actor=&director=&composer' \
                 '=&screenwriter=&author=&cinematographer=&production=&edit=&sound=&scenography=&mask=&costumes=&tag=&ok' \
                 '=Hledat&_form_=film '


def movie_url(page):
    return 'https://www.csfd.cz/film/' + str(page)


def get_soup(page):
    return bs(rq.get(page).text, features="html.parser")


def get_from_collection(number_movies=1):
    movies_pages = {}
    i = 0
    while len(movies_pages) < number_movies:
        soup = get_soup(collection_url(i))
        for link in soup.findAll('a', attrs={'class': re.compile("^film c[1,2]")}):
            link = link['href'].replace('/film/', '')
            direct_key = link[: link.find('-')]
            if direct_key not in movies_pages:
                movies_pages[direct_key] = 1
        i += 1
        sleep(2)

    return movies_pages


def get_directly(start=1, number_movies=1):
    json_to_elastic = []
    with codecs.open('out.txt', 'w', encoding='utf8') as file:
        for page in range(start, start + number_movies):
            soup = get_soup(movie_url(page))
            try:
                movie = Movie(id=page, soup=soup)
                json_to_elastic += [movie.__dict__]
                print('Slovenský: ', movie.title['Slovenský'])
            except Exception as e:
                print(page, e)
            sleep(2)

    with open('movie.json', 'w', encoding='utf-8') as fo:
        json.dump(json_to_elastic, fo, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))


def web_spider_priority(start_page, number_page=10):
    queue = Queue(maxsize=150000)
    queue.put((start_page.count('/'), start_page))
    movies_pages = {}
    visited_pages = {start_page: 1}

    while len(movies_pages) <= number_page:
        act_page = queue.get()[1]
        visited_pages[act_page] = 1
        soup = get_soup(act_page)

        for link in soup.findAll('a', attrs={'href': re.compile("^/uzivatel/")}):
            link = link.get('href')
            if not (start_page + link) in visited_pages and not queue.full():
                visited_pages[start_page + link] = 0
                queue.put(((start_page + link).count('/') - 2 if not 'hodnoceni' in link else (start_page + link).count(
                    '/') - 4, (start_page + link)))

        for link in soup.findAll('a', attrs={'href': re.compile("^/tvurce/")}):
            link = link.get('href')
            if not (start_page + link) in visited_pages and not queue.full():
                visited_pages[start_page + link] = 0
                queue.put(((start_page + link).count('/'), (start_page + link)))

        for link in soup.findAll('a', attrs={'href': re.compile("^/film/")}):
            link = link.get('href')
            direct_key = link.replace('/film/', '')
            direct_key = direct_key[: direct_key.find('-')]
            if direct_key not in movies_pages:
                movies_pages[direct_key] = 1
            if not (start_page + link) in visited_pages and not queue.full():
                visited_pages[start_page + link] = 0
                queue.put(((start_page + link).count('/'), (start_page + link)))
        sleep(2)

    return movies_pages


def save_to_html(movies_pages):
    for movie in movies_pages.keys():
        with open('movie_data/' + '_' + str(movie) + '_.html', 'w', encoding='utf-8') as f:
            f.write(rq.get(movie_url(movie)).text)
        sleep(1)


def html_to_jason(bulk=1):
    d_path = np.array(['D:\VINF_DATA\movie_data\\' + x for x in os.listdir('D:\VINF_DATA\movie_data')])
    json_bulk = []
    no_bulk = 0
    for movie in d_path:
        try:
            with open(movie, encoding='utf-8') as fo:
                soup = bs(fo, features="html.parser")
                id = movie.split('\\')[-1].replace('_', '').replace('.html', '')
                movie = Movie(id=id, soup=soup)
            json_bulk += [movie.__dict__]
        except Exception as e:
            print(movie, e)
        if len(json_bulk) == bulk:
            with open('D:\VINF_DATA\movie_json\\bulk_' + str(no_bulk) + '.json', 'w', encoding='utf-8') as fo:
                json.dump(json_bulk, fo, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
            no_bulk += 1
            json_bulk = []

    if len(json_bulk) > 0:
        with open('D:\VINF_DATA\movie_json\\bulk_' + str(no_bulk) + '.json', 'w', encoding='utf-8') as fo:
            json.dump(json_bulk, fo, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
        no_bulk += 1


def html_to_elastic():
    es = Elasticsearch()
    d_path = np.array(['/Users/stefangrivalsky/movie_data/movie_data/' + x for x in
                       os.listdir('/Users/stefangrivalsky/movie_data/movie_data')])
    for movie in d_path:
        try:
            with open(movie, encoding='utf-8') as fo:
                soup = bs(fo, features="html.parser")
                id = movie.split('/')[-1].replace('_', '').replace('.html', '')
                movie_jsn = Movie(soup=soup)
                es.index(index="csfd", doc_type='movie', id=id, body=movie_jsn.__dict__)
        except Exception as e:
            print(movie, e)


def html_debug():
    d_path = np.array(['D:\VINF_DATA\movie_data\\' + x for x in os.listdir('D:\VINF_DATA\movie_data')])
    for movie in d_path:
        with open(movie, encoding='utf-8') as fo:
            soup = bs(fo, features="html.parser")
            id = movie.split('\\')[-1].replace('_', '').replace('.html', '')
            movie_jsn = Movie(soup=soup)


def serialize_movies(movies_pages):
    json_to_elastic = []
    for page in movies_pages.keys():
        soup = get_soup(movie_url(page))
        try:
            movie = Movie(soup=soup)
            json_to_elastic += [movie.__dict__]
            print('Slovenský: ', movie.title['Slovenský'])
            movies_pages[page] = 0
        except Exception as e:
            print(page, e)

        sleep(2)

    with open('movie.json', 'w', encoding='utf-8') as fo:
        json.dump(json_to_elastic, fo, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))

    print(len(movies_pages))


class Movie:

    def __init__(self, soup):

        # MAIN id in non-relation database
        self.rating = int(soup.find('div', {'id': 'rating'}).find('h2').text[:-1])

        # Store titles in all languages
        tmp_main_title = re.sub(r'[\n,\t]', '', soup.find('div', {'class': 'header'}).h1.text)
        self.title = tmp_main_title
        self.titles = tmp_main_title
        # try:
        #     for lang_name in soup.find('ul', {'class': 'names'}).findAll('li'):
        #         if not lang_name.h3.text in self.titles:
        #             self.titles += [lang_name.h3.text]
        # except Exception as e:
        #     pass
        self.no_ratings = re.sub(r'[\n,\t,),(,&nbsp\s]', '', soup.find('div', {'class': 'count'}).text[
                                                             soup.find('div', {'class': 'count'}).text.find('('):])
        self.no_ratings = int(str(self.no_ratings))
        self.creators = {}
        self.content = []
        for div in soup.find('div', {'class': 'creators'}).findAll('div'):
            if not 'id' in div.attrs.keys():
                self.creators[div.find('h4').text] = [a.text for a in div.findAll('a')]
            else:
                for div in div.findAll('div'):
                    self.creators[div.find('h4').text] = [a.text for a in div.findAll('a')]
        for content in soup.find('div', {'id': 'plots'}).findAll('li'):
            div = content.find('div') if content.find('div') is not None else content
            self.content += [{'source': re.sub(r'[),(]', '', div.find('span', {'class', 'source'}).text),
                              'plot': re.sub(r'[\n,\t]', '',
                                             div.text.replace(div.find("span", {"class", "source"}).text, ''))}]
        self.creators['Hrají:'] = ', '.join(self.creators['Hrají:'])
        self.genre = soup.find('p', {'class': 'genre'}).text.split(' / ')
        origin = soup.find('p', {'class': 'origin'}).text.split(', ')
        self.country = origin[0].split(' / ')
        self.year = int(origin[1])
        self.lenght = int(origin[2][:origin[2].find(' ')])


if __name__ == '__main__':
    # bulk 1000
    start_time = time()
    # movies = get_from_collection(6000) # 6000 / 431s
    # movies = web_spider_priority('https://www.csfd.cz', number_page=30000)  # 6000 / 212s
    # html_to_jason(bulk=1000)
    html_to_elastic()
    # get_directly(start=147490, number_movies=32)
    print("--- %s seconds ---" % (time() - start_time))

    # save_to_html(movies)  # getDirectly(start=8275, number_movies=20)
