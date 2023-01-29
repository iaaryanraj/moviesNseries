import json
import os
import re
import subprocess

import requests
from prompt_toolkit import print_formatted_text, prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import (checkboxlist_dialog, message_dialog,
                                      radiolist_dialog, set_title)
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator

from providers.lookmovie import Lookmovie
from utility.content import Episode, Movie, Series
from utility.m3u8_downloader import start_download
from utility.search_suggestions import SearchAutocompletor

set_title('moviesNseries | v1.0 (beta)')


if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')


logo = r"""
                      _            _   _               _           
                     (_)          | \ | |             (_)          
 _ __ ___   _____   ___  ___  ___ |  \| |___  ___ _ __ _  ___  ___ 
| '_ ` _ \ / _ \ \ / / |/ _ \/ __|| . ` / __|/ _ \ '__| |/ _ \/ __|
| | | | | | (_) \ V /| |  __/\__ \| |\  \__ \  __/ |  | |  __/\__ \
|_| |_| |_|\___/ \_/ |_|\___||___/\_| \_/___/\___|_|  |_|\___||___/
                                                                   
"""


style = Style.from_dict({
    # Default style for user input.
    '': 'fg:yellow',
    # Default style for prompt.
    'prompt': 'fg:purple bg:black bold',
    # Style for the logo.
    'logo': 'fg:dodgerblue bg:black bold',
    # Style for the error message.
    'error': 'fg:red bg:black bold',
    # Style for text that shows a loading state.
    'loading': 'fg:green bg:black italic',
    # Style for the info text.
    'info': 'fg:white bg:black bold',
    # Style for the warning text.
    'warning': 'fg:yellow bg:black bold',
})

dialog_style = Style.from_dict({
    'dialog':             'bg:blue',
    'dialog frame.label': 'bg:#ffffff #000000',
    'dialog.body':        'bg:#000000 yellow',
})


print_formatted_text(
    HTML(f'<logo>{logo}</logo>'),
    style=style
)


kb = KeyBindings()


@kb.add('c-c')
def _(event):
    print_formatted_text(HTML('<style fg="red" bg="black">Goodbye!</style>'))
    exit()


@kb.add('c-q')
def _(event):
    print_formatted_text(HTML('<style fg="red" bg="black">Goodbye!</style>'))
    exit()


validator = Validator.from_callable(
    lambda text: text.strip() != '',
    error_message='Please enter a valid search term',
    move_cursor_to_end=True
)


def download_content(content: Movie | Series) -> None:
    """Download the content from the provider.

    Parameters
    ----------
    content : Movie | Series
        The content to download.
    """
    os.chdir('Downloads')
    print_formatted_text(
        HTML(f'<info>Working on <u>{content.title}</u></info>'),
        style=style
    )
    content.title = re.sub(re.compile(r'[\\/*?:"<>|]'), '', content.title)
    if not os.path.exists(content.title):
        os.mkdir(content.title)
    os.chdir(content.title)
    if isinstance(content, Movie):
        with open(f'{content.title}.vtt', 'wb') as f_subtitle:
            try:
                resp = requests.get(content.subtitle, stream=True)
                resp.raise_for_status()
                print_formatted_text(
                    HTML(f'<loading>Downloading subtitle</loading>'),
                    style=style
                )
                for chunk in resp.iter_content(chunk_size=1024):
                    f_subtitle.write(chunk)
                print_formatted_text(
                    HTML(f'<info>Subtitle downloaded</info>'),
                    style=style
                )
            except Exception:
                print_formatted_text(
                    HTML(
                        f'<error>Could not download subtitle for {content.title}!</error>'),
                    style=style
                )
        print_formatted_text(
            HTML(f'<loading>Downloading m3u8</loading>'),
            style=style
        )
        while True:
            try:
                start_download(
                    m3u8=content.m3u8,
                    file_name=content.title
                )
                print_formatted_text(
                    HTML(f'<info>Download complete!</info>'),
                    style=style
                )
                break
            except ValueError:
                success = content.provider.set_m3u8_n_subtitle(content, quality)
                if success == False:
                    print_formatted_text(
                        HTML('<error>Failed to download!</error>'),
                        style=style
                    )
                    break
        os.chdir('..')
    else:
        for season in content.seasons:
            print_formatted_text(
                HTML(f'<info>Working on <u>Season {season}</u></info>'),
                style=style
            )
            if not os.path.exists(f'Season {season}'):
                os.mkdir(f'Season {season}')
            os.chdir(f'Season {season}')
            for episode in content.seasons[season]:
                print_formatted_text(
                    HTML(f'<info>Working on <u>Episode {episode.number}</u></info>'),
                    style=style
                )
                with open(f'{episode.title}.vtt', 'wb') as f_subtitle:
                    try:
                        resp = requests.get(episode.subtitle, stream=True)
                        resp.raise_for_status()
                        print_formatted_text(
                            HTML(f'<loading>Downloading subtitle</loading>'),
                            style=style
                        )
                        for chunk in resp.iter_content(chunk_size=1024):
                            f_subtitle.write(chunk)
                        print_formatted_text(
                            HTML(f'<info>Subtitle downloaded</info>'),
                            style=style
                        )
                    except Exception:
                        print_formatted_text(
                            HTML(
                                f'<error>Could not download subtitle for Episode {episode.number}!</error>'),
                            style=style
                        )
                print_formatted_text(
                    HTML(f'<loading>Downloading Episode {episode.number}</loading>'),
                    style=style
                )
                while True:
                    try:
                        start_download(
                            m3u8=episode.m3u8,
                            file_name=re.sub(re.compile(r'[\\/*?:"<>|]'), '', episode.title)
                        )
                        print_formatted_text(
                            HTML(f'<info>Download complete!</info>'),
                            style=style
                        )
                        break
                    except ValueError:
                        success = content.provider.set_m3u8_n_subtitle(content, quality)
                        if success == False:
                            print_formatted_text(
                                HTML('<error>Failed to download!</error>'),
                                style=style
                            )
                            break
            os.chdir('..')
    os.chdir('..')


def get_download_choice(seasons: dict[int, list[Episode]]) -> dict[int, list[Episode]] | None:
    """Get the user's choice of seasons and episodes to download.

    Parameters
    ----------
    seasons : dict[int, list[Episode]]
        The seasons and episodes to choose from.

    Returns
    -------
    dict[int, list[Episode]] | None
        The user's choice of seasons and episodes to download, or None if the user cancelled the dialog.
    """
    values = []
    for season in seasons:
        item = ((season, range(len(seasons[season]))), f'Season {season}')
        values.append(item)
        for episode in seasons[season]:
            item = ((season, episode.number-1),
                    f'    Episode {episode.number} | {episode.title}')
            values.append(item)
            # print('\t', episode.number, episode.title)
    checkbox = checkboxlist_dialog(
        title='Select seasons and episodes to download',
        values=values,
        ok_text='Download',
        cancel_text='Cancel',
        style=dialog_style,
    )
    checkbox.mouse_support = True
    checkbox.key_bindings = kb
    download_choice = checkbox.run()
    if download_choice is None or download_choice == []:
        return download_choice
    else:
        whole_seasons = []
        for choice in download_choice:
            if isinstance(choice[1], range):
                whole_seasons.append(choice)
        # Remove the whole seasons from the list
        for season in whole_seasons:
            download_choice.remove(season)
        individual_episodes = download_choice.copy()
        # Remove the individual episodes from the list if the whole season of that episode is selected.
        for season in whole_seasons:
            for choice in download_choice:
                if season[0] == choice[0] and isinstance(choice[1], int):
                    individual_episodes.remove(choice)
        download_choice = {}
        for season in whole_seasons:
            download_choice.setdefault(season[0], seasons[season[0]])
        for episode in individual_episodes:
            download_choice.setdefault(
                episode[0], []).append(seasons[episode[0]][episode[1]])
        return download_choice


def get_query() -> str:
    """Get the search query from the user.

    Returns
    -------
    str
        The search query.
    """
    return prompt(
        HTML('<prompt>Enter the name of a movie or series: </prompt>'),
        completer=SearchAutocompletor(),
        complete_in_thread=True,
        validator=validator,
        key_bindings=kb,
        style=style
    )


def get_choice(results: list[Movie | Series]) -> int | None:
    """Get the user's choice from the list of results.

    Parameters
    ----------
    results : list[Movie | Series]
        The list of results.

    Returns
    -------
    int | None
        The index of the user's choice, or None if the user cancelled.
    """
    dialog = radiolist_dialog(
        title='Select a movie or series',
        values=[
            (
                result[0],
                f'{result[1].title} | {result[1].year} | {result[1].provider.name}'
            ) for result in enumerate(results)
        ],
        ok_text='Select',
        cancel_text='Cancel',
        style=dialog_style,
    )
    dialog.mouse_support = True
    dialog.key_bindings = kb
    return dialog.run()


def main() -> None:
    """Main function.

    Returns
    -------
    None
    """
    if not os.path.exists('Downloads'):
        os.mkdir('Downloads')
    global quality
    try:
        with open("Config.json") as config_file:
            config = json.load(config_file)
            quality = int(config['download_quality'])
            assert quality in [1080, 720, 480]
    except FileNotFoundError:
        print_formatted_text(
            HTML('<error>Config.json not found!</error>'),
            style=style
        )
        exit()
    except AssertionError:
        print_formatted_text(
            HTML('<error>Invalid download quality! Valid Options- 1080, 720, 480</error>'),
            style=style
        )
        exit()
    except ValueError:
        print_formatted_text(
            HTML('<error>Invalid download quality! Valid Options- 1080, 720, 480</error>'),
            style=style
        )
        exit()
    try:
        subprocess.run("ffmpeg", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.environ['FFMPEG'] = '1'
    except FileNotFoundError:
        print_formatted_text(
            HTML('<warning>FFmpeg not found! Final file won\'t be converted to mp4</warning>'),
            style=style
        )
        os.environ['FFMPEG'] = '0'
    while True:
        query = get_query()
        results = Lookmovie.search(query)
        if len(results) == 0:
            message_dialog(
                title='No results found',
                text='No results found for your search term. Please try again.',
                ok_text='OK',
                style=style,
            ).run()
        else:
            break
    choice = get_choice(results)
    if choice is None:
        main()
    else:
        success = results[choice].provider.update_info(results[choice])
        if success == False:
            print_formatted_text(
                HTML('<error>Failed to get series info!</error>'),
                style=style
            )
            exit()
        else:
            if isinstance(results[choice], Series):
                print()
                while True:
                    download_choice = get_download_choice(
                        results[choice].seasons)
                    # Update the seasons with the user's choice
                    results[choice].seasons = download_choice
                    if download_choice is None or download_choice == []:
                        main()
                    else:
                        break
            # Try three times to get the m3u8 and subtitle before exiting.
            for i in range(3):
                success = Lookmovie.set_m3u8_n_subtitle(results[choice], quality)
                if success is not None:
                    print_formatted_text(
                        HTML(f'<error>Failed to get m3u8 and subtitle! {success[1]}</error>'),
                        style=style
                    )
                    print_formatted_text(
                        HTML('<info>Trying again...</info>'),
                        style=style
                    )
                    Lookmovie.update_info(results[choice])
                else:
                    download_content(results[choice])
                    break
            else: exit()
                # for season in download_choice:
                    # for episode in download_choice[season]:
                        # print(episode.title, episode.m3u8, episode.subtitle)
                # print(results[choice].title, results[choice].m3u8, results[choice].subtitle)



if __name__ == '__main__':
    main()
