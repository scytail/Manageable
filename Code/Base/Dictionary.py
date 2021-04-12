import json
from enum import Enum
from random import choice
from typing import Optional
from os import path


class PhraseMap(Enum):
    ExamplePhrase: 1


class Dictionary:
    """Represents a Lexicon of phrases that can be queried as-needed with PhraseMap values.

    Methods
    -------
    __init__    Loads up the provided language, as well as any inherited languages, for consumption
    get_phrase  Queries the loaded language lexicon for the requested phrase
    """

    _LANG_BASE_PATH = 'Data/Languages/'

    def __init__(self, language_file_name: str):
        """Loads up the file with the requested language file name (as well as any parent language files of that file).

        Parameters
        ----------
        language_file_name  str     The language file name to load (without any file extensions). Please note that this
                                    is case-sensitive.
        """
        self.phrase_map = self._load_language_dictionary(language_file_name)

    def get_phrase(self, phrase: PhraseMap, default_value: Optional[str] = None) -> Optional[str]:
        """Queries the loaded lexicon for the requested phrase, defaulting to the default value if it fails.

        Notes
        -----
        By default, the default value for default_value is None, indicating that no phrase is loaded. It is highly
        recommended that this is overridden with a specific "default" phrase that can act as a hard-coded fallback for
        seamless dictionary usage.

        Parameters
        ----------
        phrase          PhraseMap       The PhraseMap value to query the loaded lexicon for.
        default_value   Optional[str]   The default phrase (or None) to return if the phrase was not found.

        Returns
        -------
        Optional[str]   A random text phrase that correlates to the PhraseMap requested. Can also return a default
                        value (or None) if the phrase requested was not found in the loaded lexicon.
        """

        try:

            return choice(self.phrase_map[str(phrase.value)])
        except KeyError:
            return default_value

    def _load_language_dictionary(self, language_file_name: str) -> dict:
        """Load a language file and merge its phrases into a parent's phrases, recursively.

        Notes
        -----
        This method runs recursively, meaning that when it loads the parent dictionary's phrases, it will continue to do
        so until it reaches a dictionary that has a parent dictionary of an empty string. Then, it merges the lexicons
        together, from top-most parent to lowest child, such that any phrases found in a child will always replace the
        parents' phrases.

        Parameters
        ----------
        language_file_name  str     The case-sensitive language file name (without file extensions) to load up.

        Returns
        -------
        dict    A dictionary of numeric phrase IDs (represented by the PhraseMap enum for code readability), and a list
                of each ID's string phrases.
        """
        language_file_path = f'{self._LANG_BASE_PATH}{language_file_name}.json'

        # Validate that the language exists
        if not path.exists(language_file_path):
            raise FileNotFoundError(f'The file "{language_file_name}.json" was not found in the Languages folder.')

        # Load the language file
        with open(language_file_path) as language_file:
            language_file_data = json.load(language_file)
        language_metadata = language_file_data['metadata']
        language_dictionary = language_file_data['phrases']

        # Load up any parent dictionaries recursively and replace phrases as needed
        parent_language_file_name = language_metadata['parent_language_name']
        if parent_language_file_name != '':
            parent_dictionary = self._load_language_dictionary(parent_language_file_name)
            # TODO: Protect against infinite recursion
            # Takes the parent dictionary and updates any already-found keys with this dictionary
            language_dictionary = {**parent_dictionary, **language_dictionary}

        return language_dictionary
