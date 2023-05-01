<p align="center">
<img src="https://i.imgur.com/58ov8pO.jpeg"/>
</p>

# moviesNseries

## Description

A simple TUI application to search for movies and series, and download them. It uses the [TMDB API](https://developers.themoviedb.org/3/getting-started/introduction) to facilitate autocompletion while searching for movies and series. <span style="color:red">The program now requires a VPN to function because the site it uses has been blocked.</span>

## Installation

```bash
git clone https://github.com/iaaryanraj/moviesNseries.git
cd moviesNseries
pip install -r requirements.txt
```

`Chrome` browser is required. You can download it from [here](https://www.google.com/chrome/).

`FFmpeg` is not necessary for the application to work. It is only used to convert the downloaded `*.ts` file to `*.mp4` file.

For Windows users, just copy the `ffmpeg.exe` file from the `ffmpeg` folder to the `SYSTEM32` folder.

For Linux users, run the following command to install `FFmpeg`:

```bash
sudo apt install ffmpeg
```

<!-- After installing the requirements, you need to create an API key from [TMDB](https://developers.themoviedb.org/3/getting-started/introduction) and add it to the `Config.json` file as the value of the `TMDB_API_KEY` key. -->

## Usage

Set the download quality in the `Config.json` file. The default value is `1080`. The available options are `1080`, `720` and `480`. If the movie or series is not available in the specified quality, the next best quality will be downloaded.

```bash
python moviesNseries.py
```

## Features

- [x] Download movies and series with subtitles
- [x] No annoying ads or popups
- [x] Batch download entire series

## Supported Site(s)

- [x] [Lookmovie](https://lookmovie2.to/)

## TODO

- [ ] Add support for Hindi movies and series
- [ ] Add support for Korean Drama
- [ ] Add support for Anime

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change

## Warning

This project is for educational purposes only. It does not host any content, it just scrapes the content from the supported sites. I am not responsible for any misuse of this project.
