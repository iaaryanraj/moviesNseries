import os
import time
from urllib.parse import urlparse

import js2py
import requests

if __name__ == '__main__':
    import sys
    sys.path.append(os.getcwd())
import logging

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from webdriver_manager.chrome import ChromeDriverManager

from utility.content import Episode, Movie, Series
from utility.print_progress import print_progress

options = ChromeOptions()
options.headless = True
options.add_experimental_option('excludeSwitches', ['enable-logging'])
os.environ['WDM_PROGRESS_BAR'] = '0'
os.environ['WDM_LOG'] = str(logging.NOTSET)


class Lookmovie:
    """Class for Lookmovie provider.

    Attributes
    ----------
    name : str
        Name of the provider.
    base_link : str
        Base link of the provider.
    movie_search_link : str
        Link to search for movies.
    series_search_link : str
        Link to search for series.
    movie_link : str
        Link to movie page.
    series_link : str
        Link to series page.

    Methods
    -------
    search(query: str) -> list[Movie | Series]
        Search for movies and series.
    update_info(content: Movie | Series) -> None | bool
        Update the info of the content.

    Raises
    ------
    """
    name = 'Lookmovie'
    base_link = 'https://lookmovie2.to'
    movie_search_link = base_link+'/api/v1/movies/do-search/?q='
    series_search_link = base_link+'/api/v1/shows/do-search/?q='
    movie_link = base_link+'/movies/view/'
    series_link = base_link+'/shows/view/'

    @classmethod
    def search(cls, query: str) -> list[Movie | Series]:
        """Search for movies and series.

        Parameters
        ----------
        query : str
            Query to search for.

        Returns
        -------
        list[Movie | Series]
            List of movies and series, empty list if no results or error
        """
        search_results = []
        try:
            resp = requests.get(cls.movie_search_link+query)
            resp.raise_for_status()
            movie_search_response = resp.json()
            resp = requests.get(cls.series_search_link+query)
            resp.raise_for_status()
            series_search_response = resp.json()
        except requests.exceptions.HTTPError:
            return search_results
        for movie in movie_search_response['result']:
            search_results.append(
                Movie(movie['title'], int(movie['year']), cls.movie_link+movie['slug'], cls))
        for series in series_search_response['result']:
            search_results.append(
                Series(series['title'], int(series['year']), cls.series_link+series['slug'], cls, {}))
        return search_results

    @staticmethod
    def update_info(content: Movie | Series) -> None | bool:
        """Update the info of the content.

        Parameters
        ----------
        content : Movie | Series
            Content to update.

        Returns
        -------
        None | bool
            None if their is no exception while sending request, else False if an exception is raised.
        """
        content_type = 'movie' if isinstance(content, Movie) else 'series'
        print_progress(0, f'Getting {content_type} info...')
        try:
            resp = requests.get(content.link)
            resp.raise_for_status()
        except Exception:
            return False
        print_progress(25, f'Getting {content_type} info...')
        soup = BeautifulSoup(resp.text, 'html.parser')
        frame_link = soup.select_one('a.round-button')['href'].strip()
        content.frame_link = frame_link
        driver = webdriver.Chrome(service=ChromeService(
            ChromeDriverManager().install()), options=options)
        driver.get(frame_link)
        driver.get(frame_link)
        print_progress(50, f'Getting {content_type} info...')
        time.sleep(1)
        # if isinstance(content, Movie):
            # css_selector = '#app > script:nth-child(4)'
        # else:
        css_selector = '#app > script:nth-child(2)'
        try:
            element = driver.find_element(By.CSS_SELECTOR, css_selector)
        except NoSuchElementException:
            # If reload method is not working, try to click on the recaptcha checkbox
            try:
                time.sleep(1)
                driver.switch_to.frame(
                    driver.find_element(By.TAG_NAME, "iframe"))
                driver.find_element(
                    By.CSS_SELECTOR, '.recaptcha-checkbox-border').click()
                # driver.switch_to.default_content()
                time.sleep(2)
                element = driver.find_element(By.CSS_SELECTOR, css_selector)
            except NoSuchElementException:
                driver.close()
                return False
        print_progress(75, f'Getting {content_type} info...')
        script_content = element.get_attribute('innerHTML')
        info_dict = js2py.eval_js(script_content).to_dict()
        print_progress(85, f'Getting {content_type} info...')
        if isinstance(content, Movie):
            content.id = int(info_dict['id_movie'])
        content.hash = info_dict['hash'].strip()
        content.expiry = int(info_dict['expires'])
        if isinstance(content, Series):
            season_dict = {}
            for season in info_dict['seasons']:
                episode_number = int(season['episode'])
                title = season['title']
                id = int(season['id_episode'])
                season_dict.setdefault(int(season['season']), []).append(
                    Episode(episode_number, title, id))
            content.seasons = season_dict
        print_progress(100, f'Getting {content_type} info...')
        print()
        driver.close()

    @staticmethod
    def set_m3u8_n_subtitle(content: Movie | Series, quality: int) -> None | bool:
        """Set the m3u8 link and subtitle of the content.

        Parameters
        ----------
        content : Movie | Series
            Content to update.
        quality : int
            Quality of the m3u8 file.

        Returns
        -------
        None | bool
            None if their is no exception while sending request, else False if an exception is raised.
        """
        domain = urlparse(content.frame_link).netloc
        resources_link = f'https://{domain}/api/v1/security/'
        if isinstance(content, Movie):
            resources_link += f'movie-access?id_movie={content.id}&hash={content.hash}&expires={content.expiry}'
            try:
                resp = requests.get(resources_link)
                resp.raise_for_status()
                resources = resp.json()
                if resources['success'] == False:
                    return (False, resources['message'])
                for subtitle in resources['subtitles']:
                    if subtitle['language'].lower() == 'english':
                        content.subtitle = 'https://'+domain+subtitle['file']
                        break
                for stream in resources['streams']:
                    if int(stream.replace('p', '').strip()) == quality:
                        content.m3u8 = resources['streams'][stream]
                        break
                # If the desired quality is not available, set the first quality
                if content.m3u8 == '':
                    content.m3u8 = resources['streams'][list(
                        resources['streams'].keys())[0]]
            except requests.exceptions.HTTPError:
                return (False, 'HTTP Error')
        else:
            try:
                for season in content.seasons:
                    for episode in content.seasons[season]:
                        resources_link = f'https://{domain}/api/v1/security/'
                        resources_link += f'episode-access?id_episode={episode.id}&hash={content.hash}&expires={content.expiry}'
                        resp = requests.get(resources_link)
                        resp.raise_for_status()
                        resources = resp.json()
                        if resources['success'] == False:
                            return (False, resources['message'])
                        for subtitle in resources['subtitles']:
                            if subtitle['language'].lower() == 'english':
                                episode.subtitle = 'https://' + \
                                    domain+subtitle['file']
                                break
                        for stream in resources['streams']:
                            if int(stream.replace('p', '').strip()) == quality:
                                episode.m3u8 = resources['streams'][stream]
                                break
                        # If the desired quality is not available, set the first quality
                        if episode.m3u8 == '':
                            episode.m3u8 = resources['streams'][list(
                                resources['streams'].keys())[0]]
            except requests.exceptions.HTTPError:
                return (False, 'HTTP Error')


if __name__ == '__main__':
    results = Lookmovie.search('The Haunting Of Hill House')
    print(results[0].get_synopsis())
    Lookmovie.update_info(results[0])
    print(results[0].seasons)
