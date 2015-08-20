# -*- coding: utf-8 -*-
# Standard Library
import re

# Third Party Stuff
import enchant
import html2text

DEFAULT_LANGUAGE = "en_UK"
REGEX_FIND_ENGLISH_WORDS = re.compile(r"[a-zA-Z]+")


def get_word_checker(language=DEFAULT_LANGUAGE):
    """
    Returns a functions which will return True if word is not
    present in dictionary.
    """
    enchant_dictionary = enchant.Dict(language)
    spell_checker = lambda w: not enchant_dictionary.check(w)
    return spell_checker


def find_incorrect_words(text, spell_checker):
    """
    Finds all english words in the text and returns incorrect words
    as they would appear in a english dictionary.
    """
    words = set(REGEX_FIND_ENGLISH_WORDS.findall(text))
    return filter(spell_checker, words)


def check_spelling(text, language=DEFAULT_LANGUAGE):
    '''
    Runs spellcheck and highlights incorrect words using LaTex.
    '''
    spell_checker = get_word_checker(language)
    incorrect_words = find_incorrect_words(text, spell_checker)

    for word in incorrect_words:
        text = text.replace(
            word, r" \textcolor{red}{\Large \textbf{" + word + "}} ")

    return text


def check_spelling_in_html(html, language=DEFAULT_LANGUAGE):
    '''
    - Converts html to text.
    - Filter incorrect words and highlight them using appropriate HTML.
    '''
    spell_checker = get_word_checker(language)

    text = html2text.html2text(html)
    incorrect_words = find_incorrect_words(text, spell_checker)

    for word in incorrect_words:
        replacement = r'<strong style="color: red; font-size: 14px;">' + \
            word + '</strong>'
        html = re.sub(r"\s+{0}\s+".format(word), replacement, html)
    return html
