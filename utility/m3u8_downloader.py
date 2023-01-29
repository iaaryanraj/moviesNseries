import concurrent.futures
import os
import subprocess
import time

import requests
from tqdm import tqdm


def get_segments(m3u8_url: str) -> list[str]:
    """Get segments from m3u8 file.

    Parameters
    ----------
    m3u8_url : str
        m3u8 file url.

    Returns
    -------
    list[str]
        List of segments.

    Raises
    ------
    ValueError
        If hash is wrong.
    """
    base_url = m3u8_url.rsplit('/', 1)[0]+'/'
    resp = requests.get(m3u8_url)
    resp.raise_for_status()
    m3u8_content = resp.text
    if 'HASH' in m3u8_content:
        raise ValueError
    # Create list of segments
    segments = resp.text.replace('\n', '')
    segments = segments.split(',')
    segments.pop(0)
    for segment in enumerate(segments):
        segments[segment[0]] = base_url+segment[1].split('.')[0]+'.ts'
    return segments

def get_response(segment: str) -> requests.Response:
    """Get response from segment url.

    Parameters
    ----------
    segment : str
        Segment url.

    Returns
    -------
    requests.Response
        Response.
    """
    while True: # This is the infinite loop
        try:
            resp = requests.get(segment)
            resp.raise_for_status()
            return resp  # This is the exit from the loop
        except:
            print(
                '\033[91m', # Red foreground
                '\033[40m', # Black background
                f'Error while downloading segment: {segment}, retrying...',
                '\033[0m'
            )
            time.sleep(5) # Wait 5 seconds before trying
            continue

def start_download(m3u8: str, file_name: str) -> None:
    """Start download.

    Parameters
    ----------
    m3u8 : str
        m3u8 file url.
    file_name : str
        File name.
    """
    segments = get_segments(m3u8)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = executor.map(get_response, segments)
        f = open(file_name+'.ts', 'wb')
        try:
            for future in tqdm(futures, desc='Progress', total=len(segments), colour='green'):
                f.write(future.content)
        except KeyboardInterrupt:
            print(
                '\033[91m', # Red foreground
                '\033[40m', # Black background
                'Download interrupted.',
                '\033[0m'
            )
            exit()
        f.close()
        if os.environ.get('FFMPEG') == '1':
            subprocess.run(f'ffmpeg -i "{file_name}.ts" -c copy -bsf:a aac_adtstoasc "{file_name}.mp4"', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(file_name+'.ts')
    
if __name__ == '__main__':
    import os
    import time
    if not os.path.exists('test'): os.mkdir('test')
    os.chdir('test')
    os.environ['FFMPEG'] = '1'
    m3u8 = 'https://no1.cocarruptoo.monster/aes/1Jj2XzAOd8cIi1E8vN74Jg/1671341126/storage3/shows/7767422-sex-education-2019/164745-S1-E1-1663047988/6758cc1616fcd728a373a2dcee522d45.mp4/index.m3u8'
    start_download(m3u8, 'test')