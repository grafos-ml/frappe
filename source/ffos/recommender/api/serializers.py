# -*- coding: utf-8 -*-
"""
.. module:: ffos.recommender.api.serializers
    :platform: Unix, Windows
    :synopsis: Serializers for the recommender api
     Created at Fev 19, 2014

.. moduleauthor:: joaonrb <joaonrb@gmail.com>

"""
__author__ = "joaonrb"

from ffos.models import FFOSApp
from rest_framework import serializers


class ItemRecommendedSerializer(serializers.ModelSerializer):
    """
    .. py:class:: ffos.recommender.api.serializers.ItemRecommenderSerializer()


    About
    -----

    Serializer for a recommended item.
    """

    class Meta:
        model = FFOSApp
        fields = "external_id",