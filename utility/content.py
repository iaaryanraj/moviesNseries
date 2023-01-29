import json

import tmdbsimple as tmdb

with open("Config.json") as config_file:
    config = json.load(config_file)

tmdb.API_KEY = config["TMDB_API_KEY"]


class Content:
    """Base class for movies and series.

    Attributes
    ----------
    title : str
        Title of the content.
    year : int
        Year of the content.
    link : str
        Link to the content.
    provider : object
        Provider of the content.
    hash : str
        Hash of the content.
    expiry : int
        Expiry of the content.
    frame_link : str
        Link to the frame of the content.

    Methods
    -------
    get_synopsis() -> str
        Get the synopsis of the content.
    """

    def __init__(self, title: str, year: int, link: str, provider: object):
        self.title = title
        self.year = year
        self.link = link
        self.provider = provider
        self.hash = ''
        self.expiry = 0
        self.frame_link = ''

    def get_synopsis(self) -> str:
        if isinstance(self, Movie):
            result = tmdb.Search().movie(query=self.title, include_adult=True, year=self.year)
        else:
            result = tmdb.Search().tv(query=self.title, include_adult=True,
                                      first_air_date_year=self.year)
        try:
            return result["results"][0]["overview"]
        except:
            return "No synopsis found"


class Movie(Content):
    """Class for movies.

    Attributes
    ----------
    title : str
        Title of the movie.
    year : int
        Year of the movie.
    link : str
        Link to the movie.
    provider : object
        Provider of the movie.
    id : int
        ID of the movie.
    hash : str
        Hash of the movie's m3u8 file.
    expiry : int
        Expiry of the movie link.
    frame_link : str
        Link to the frame of the movie.
    m3u8 : str
        M3U8 link of the movie.
    subtitle : str
        Subtitle link of the movie.

    Methods
    -------
    get_synopsis() -> str
        Get the synopsis of the movie.
    """

    def __init__(self, title: str, year: int, link: str, provider: object):
        super().__init__(title, year, link, provider)
        self.id = 0
        self.m3u8 = ''
        self.subtitle = ''

    def __str__(self):
        return f"title: {self.title}, year: {self.year}, link: {self.link}, provider: {self.provider.name}, \
            id: {self.id}, hash: {self.hash}, expiry: {self.expiry}, frame_link: {self.frame_link}"


class Episode:
    """Class for episodes.

    Attributes
    ----------
    number : int
        Number of the episode.
    title : str
        Title of the episode.
    id : int
        ID of the episode.
    m3u8 : str
        M3U8 link of the episode.
    subtitle : str
        Subtitle link of the episode.
    """
    def __init__(self, episode_number: int, title: str, id: int):
        self.number = episode_number
        self.title = title
        self.id = id
        self.m3u8 = ''
        self.subtitle = ''

    def __str__(self):
        return f"episode: {self.number}, title: {self.title}, id: {self.id}"


class Series(Content):
    """Class for series.

    Attributes
    ----------
    title : str
        Title of the series.
    year : int
        Year of the series.
    link : str
        Link to the series.
    provider : object
        Provider of the series.
    hash : str
        Hash of the series.
    expiry : int
        Expiry of the series.
    frame_link : str
        Link to the frame of the series.
    seasons : dict[int, list[Episode]]
        Seasons of the series.

    Methods
    -------
    get_synopsis() -> str
        Get the synopsis of the series.
    """
    def __init__(self, title: str, year: int, link: str, provider: object, seasons: dict[int, list[Episode]]):
        super().__init__(title, year, link, provider)
        self.seasons = seasons

    def __str__(self):
        return f"title: {self.title}, year: {self.year}, link: {self.link}, \
            provider: {self.provider}, seasons: {self.seasons}, hash: {self.hash}, expiry: {self.expiry}, frame_link: {self.frame_link}"


if __name__ == "__main__":
    mov = Movie("Into the Wild", 2009, "", None)
    print(mov.get_synopsis())
    ser = Series("The Office", 2005, "", None, {})
    print(ser.get_synopsis())
