"""

Not used

'''
The recommender serializer

Created on Nov 28, 2013

This module has special kind of classes to help serialize information into
JSON requests or responses.

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from rest_framework import serializers
from django.conf import settings

DEFAULT_NUMBER_RECOMMENDATIONS = getattr(settings,
    'DEFAULT_NUMBER_RECOMMENDATIONS',5)

class UserSerializer(serializers.Serializer):
    '''
    Serializer for the user request for the recommender service

    '''

    user = serializers.CharField(required=True,max_length=255)
    number_of_recommendations = serializers.IntegerField(
        default=DEFAULT_NUMBER_RECOMMENDATIONS)

    def restore_object(self, attrs, instance=None):
        '''
        Create or update a new User instance, given a dictionary
        of deserialized field values.

        #This is the note out the example.
        #Note that if we don't define this method, then deserializing
        #data will simply return a dictionary of items.

        If a model for this request is in order, this method can return
        the model instead of the dictionary.
        '''
        if instance:
            # Update existing instance
            instance['user'] = attrs.get('user', instance['user'])
            instance['number_of_recommendations'] = attrs.get(
                'number_of_recommendations',
                instance.get('number_of_recommendations',
                             DEFAULT_NUMBER_RECOMMENDATIONS))
            return instance

        # Create new instance
        return attrs

"""