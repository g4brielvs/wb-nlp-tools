#!/usr/bin/env python
# coding: utf8
from __future__ import unicode_literals, print_function

from spacy.lang.en import English
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span, Token

from wb_cleaning.extraction.whitelist import mappings

class BaseExtractor:
    name = 'base_extractor'

    def __init__(self, nlp, entities: tuple, label: str, extractor_id: str, callback=None, mapping=None):
        self.label = label
        self.label_id = nlp.vocab.strings[label]
        self.extractor_id = extractor_id
        self.type_id = f'is_{extractor_id.lower()}'
        self.mapping = mapping

        # patterns = [nlp(ent) for ent in entities]
        patterns = list(nlp.tokenizer.pipe(entities))
        self.extractor = PhraseMatcher(nlp.vocab)
        self.extractor.add(extractor_id, callback, *patterns)

        Token.set_extension(self.type_id, default=False, force=True)

        extensions = ['code', 'normalized']
        for ext in extensions:
            try:
                Token.set_extension(ext, default='')
            except ValueError:
                pass

        # Register and implement attribute and getter in subclasses.

    def __call__(self, doc):
        extracted = self.extractor(doc)

        with doc.retokenize() as retokenizer:
            for _, start, end in extracted:
                entity = doc[start:end]

                normed = self.mapping.get(entity.text)
                if normed is None:
                    code = ''
                    normalized = entity.text
                else:
                    code = normed.get('code', '')
                    normalized = normed.get('normalized', entity.text)

                for token in entity:
                    token._.set('normalized', normalized)
                    token._.set('code', code)
                    token._.set(self.type_id, True)
                    token.ent_type_ = self.label

                retokenizer.merge(entity)

        return doc


class CountryExtractor(BaseExtractor):
    name = 'country_extractor'

    def __init__(self, nlp, label: str='COUNTRY', extractor_id: str='COUNTRY', lower: bool=False):
        mapping = mappings.get_countries_mapping()

        if lower:
            self.country_mapping = {k.lower(): v for k, v in mapping.items()}
        else:
            self.country_mapping = mapping

        entities = tuple(list(self.country_mapping))

        super(CountryExtractor, self).__init__(nlp, entities, label, extractor_id, None, self.country_mapping)


class WBPresidentsExtractor(BaseExtractor):
    name = 'wb_presidents_extractor'

    def __init__(self, nlp, label: str='WB_PRESIDENT', extractor_id: str='WB_PRESIDENT', lower: bool=False):
        mapping = mappings.get_wb_presidents_mapping()

        if lower:
            self.wb_president_mapping = {k.lower(): v for k, v in mapping.items()}
        else:
            self.wb_president_mapping = mapping

        entities = tuple(list(self.wb_president_mapping))

        super(WBPresidentsExtractor, self).__init__(nlp, entities, label, extractor_id, None, self.wb_president_mapping)
