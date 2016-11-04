from abc import ABCMeta, abstractmethod

import six

from corehq.apps.domain.dbaccessors import get_doc_ids_in_domain_by_type
from corehq.util.couch import get_document_class_by_doc_type


class BaseIDProvider(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def get_doc_ids(self, domain):
        """
        :param domain:
        :return: iterable of tuple(doc_type, list(doc_ids))
        """
        raise NotImplementedError


class DocTypeIDProvider(BaseIDProvider):
    def __init__(self, doc_types):
        self.doc_types = doc_types

    def get_doc_ids(self, domain):
        for doc_type in self.doc_types:
            doc_class = get_document_class_by_doc_type(doc_type)
            doc_ids = get_doc_ids_in_domain_by_type(domain, doc_type)
            yield doc_class, doc_ids


class ViewIDProvider(BaseIDProvider):
    """ID provider that gets ID's from view rows
    :param doc_type: Doc Type of returned docs
    :param view_name: Name of the view to query
    :param key_generator: (optional) function to call to generate the view key.
                          Arguments passed are ``doc_type`` and ``domain_name``.
                          If not provided the key will be just the domain_name.
    """
    def __init__(self, doc_type, view_name, key_generator=None):
        self.doc_type = doc_type
        self.view_name = view_name
        self.key_generator = key_generator

    def get_doc_ids(self, domain):
        doc_class = get_document_class_by_doc_type(self.doc_type)
        key = self.key_generator(self.doc_type, domain) if self.key_generator else domain
        doc_ids = [
            row['id']
            for row in doc_class.get_db().view(self.view_name, key=key, include_docs=False)
        ]
        return [(doc_class, doc_ids)]
