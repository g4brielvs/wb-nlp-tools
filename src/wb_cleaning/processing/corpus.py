'''
Module containing common functions used across the scripts.
'''
import os
from pathlib import Path
import glob
import functools
from flashtext import KeywordProcessor
from wb_cleaning import dir_manager
# export DASK_DISTRIBUTED__SCHEDULER__ALLOWED_FAILURES=210
# export DASK_DISTRIBUTED__COMM__TIMEOUTS__CONNECT=60
# export DASK_DISTRIBUTED__COMM__RETRY__COUNT=20


ACCENTED_CHARS = set(
    "ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ")

keyword_processor = KeywordProcessor()
keyword_processor.set_non_word_boundaries(
    keyword_processor.non_word_boundaries | ACCENTED_CHARS)

with open(dir_manager.get_data_dir('whitelists', 'whitelists', 'phrases.txt')) as phrase_file:
    # Use flashtext format
    phrases_map = {l.strip(): [l.strip().replace('_', ' ')]
                   for l in phrase_file if l.strip()}
    keyword_processor.add_keywords_from_dict(phrases_map)


@functools.lru_cache(maxsize=None)
def cached_load_file(fname: Path, split: bool = True):
    return load_file(fname=fname, split=split)


def replace_phrases(txt):
    return keyword_processor.replace_keywords(txt)


def load_file(fname: Path, split: bool = True):
    '''
    Simply loads a file and has an option to return the raw string or a list split by whitespaces
    with the file's corresponding doc_id.
    '''
    # Make sure that fname is a Path instance.
    fname = Path(fname)

    with open(fname) as open_file:
        txt = replace_phrases(open_file.read())

    txt = txt.split() if split else txt

    # Assume that the filename is of the form <doc_id>.txt
    doc_id = os.path.splitext(fname.name)[0]

    return (txt, doc_id)


def generate_files(path: Path, split: bool = True, min_tokens: int = 50, cached: bool = True):
    '''
    A generator that loads text files given a directory.
    '''
    return filter(lambda x: len(x[0]) >= min_tokens,
                  map(lambda x: load_file(x, split=split) if not cached else cached_load_file(x, split=split),
                      path.glob('*.txt')))


class MultiDirGenerator:
    """
    This class creates a generator that returns a tuple containing a loaded file with its doc_id.
    """

    def __init__(self, base_dir: str, source_dir_name: str = None, split: bool = True, min_tokens: int = 5, include_extra: bool = False, return_doc_id: bool = True, cached=True, logger=None):
        self.base_dir = base_dir
        self.source_dir_name = source_dir_name
        self.split = split
        self.min_tokens = min_tokens
        self.include_extra = include_extra
        self.return_doc_id = return_doc_id
        self.cached = cached
        self.logger = logger

        if source_dir_name is None:
            self.source_dirs = [Path(base_dir)]
        else:
            self.source_dirs = [Path(i) for i in glob.glob(
                f'{base_dir}/*/{source_dir_name}')]

        assert len(
            self.source_dirs) > 0, f"{base_dir}/*/{source_dir_name} doesn't exist!"

        for p in self.source_dirs:
            assert p.exists(), f"Path {p} doesn't exist!"

    def __iter__(self):
        for source_dir in self.source_dirs:
            if not self.include_extra and (source_dir.name == "EXTRA"):
                continue

            if self.logger:
                self.logger.info(
                    'Loading files from source_dir %s', source_dir)
            for tokens_doc_id in generate_files(
                    source_dir, split=self.split,
                    min_tokens=self.min_tokens, cached=self.cached):

                value = tokens_doc_id

                if not self.return_doc_id:
                    value = value[0]

                yield value

    def clear_cache(self):
        if self.cached:
            cached_load_file.cache_clear()
