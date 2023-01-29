def print_progress(n: int, msg: str = '') -> None:
    """Print a loading message with a progress bar.

    Parameters
    ----------
    n : int
        Progress percentage.
    msg : str, optional
        Message to print, by default ''
    """
    print(
    '\033[3m', # italic
    '\033[32m', # green foreground
    '\033[40m', # black background
    msg,
    f' {n}%\033[0m',
    end='\r',
    sep='',
    flush=True
)