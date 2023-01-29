import json

import tmdbsimple as tmdb
from prompt_toolkit.completion import Completer, Completion

with open("Config.json") as config_file:
    config = json.load(config_file)

tmdb.API_KEY = config["TMDB_API_KEY"]


class SearchAutocompletor(Completer):
    """
    Autocompletes search box
    """
    def get_completions(self, document, complete_event) -> Completion:
        """
        Yields suggestions for the search box.

        Parameters
        ----------
        document : prompt_toolkit.document.Document
            The document that is being edited.
        complete_event : prompt_toolkit.eventloop.Event
            The event that triggered this function.
        
        Yields
        ------
        prompt_toolkit.completion.Completion
            The suggestions for the search box.
        """
        word = document.text
        try:
            result = tmdb.search.Search().multi(query=word, include_adult=True)
            suggestions = []
            for i in range(min(10, len(result["results"]))):
                if result["results"][i]["media_type"] == "movie":
                    suggestions.append(result["results"][i]["title"])
                else:
                    suggestions.append(result["results"][i]["name"])
            yield from (Completion(suggestion, start_position=-len(word)) for suggestion in suggestions)
        except:
            pass
