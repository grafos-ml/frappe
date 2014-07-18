#! -*- encoding: utf -*-
__author__ = 'joaonrb'

from recommendation.core import InterfaceController


class ABTesting(InterfaceController):

    def __init__(self, *args, **kwargs):
        """
        Constructor. May receive a
        :param args:
        :param kwargs:
        :return:
        """
        super(ABTesting, self).__init__(*args, **kwargs)

    