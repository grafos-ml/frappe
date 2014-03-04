# -*- coding: utf-8 -*-
"""
.. module:: 
    :platform: 
    :synopsis: 
     3/4/14

.. moduleauthor:: joaonrb <>

"""
__author__ = "joaonrb"


from collections import Counter
from django.core.cache import cache
from recommender.models import Item


class ReRanker(object):
    """
    Reranker is like a filter but it assumes that the second parameter is a
    sorted list with the app ID as values
    """


class RegionReRanker(ReRanker):
    """
    Region Filter

    This filter search the user Region in profile by his info and the info of
    the installed apps. Then he make every app that don't are translated in user
    preferences and put it all to half.
    """

    @staticmethod
    def get_user_pref(user):
        """
        Calculate the user preferences.

        :param user: User to get the preferences
        :type user: ffos.models.FFOSUser
        :return: A list off apps that are available with the same locale as the user.
        """
        apps = cache.get('USER_REGION_%s' % user.external_id)
        if not apps:
            apps = Item.objects.exclude(
                regions__slug__in=([user.region] if user.region else []) + [u"worldwide"]).distinct()
            cache.set('USER_REGION_%s' % user.external_id, apps)
        return apps

    def __call__(self, user, app_score, **kwargs):
        """
        :param user: The FFOSUser or the user external_id
        :param app_scores: The list with the apps scores mapped to their app id
        """
        to_add = []
        for a in self.get_user_pref(user):
            app_score.remove(a.pk)
            to_add.append(a.pk)
        return app_score+to_add


class CategoryReRanker(ReRanker):
    """
    Category Rer-Ranker. It associates the user app category profile with app
    categories.
    """

    PART = 0.33

    def __call__(self, user, app_score, size=4, **kwargs):
        """
        :param user: The FFOSUser or the user external_id
        :param app_scores: The list with the apps scores mapped to their app id
        :param size: The number of recommendations requested. Default: 4
        :type size: int
        """
        tes = len(app_score)
        ucp = self.get_user_category_profile(user)
        soma, prefs = 0, []
        for cat, mass in ucp:
            soma += int(mass*size)
            prefs += [cat] * int(mass*size)
            if soma > size / 2.0:
                break
        acd = self.get_apps_category_dict(app_score)
        to_add = []
        for cat in prefs:
            for aid in acd[cat]:
                if aid not in to_add:
                    to_add.append(aid)
                    break
        for i in to_add:
            app_score.remove(i)
        i = size - len(to_add)
        assert len(app_score[:i]+to_add+app_score[i:]) == tes, "Len size don't match(old:%s != new:%s)" % \
                                                               (tes, len(app_score[:i]+to_add+app_score[i:]))
        #    from django.shortcuts import Http404
        #    raise Http404
        return app_score[:i]+to_add+app_score[i:]

    @staticmethod
    def get_user_category_profile(user):
        """
        Calculate the most common app categories in the user inventory

        :param user: User to get the preferences
        :type user: ffos.models.FFOSUser
        :return: A list of user most famous app categories
        """
        ucp = cache.get('USER_CATEGORY_PROFILE_%s' % user.external_id)
        if not ucp:
            appn = user.installed_apps.all().count()
            ucp = sorted([(key[0], float(value)/appn) for key, value in Counter(user.installed_apps.values_list(
                'categories__name')).items()], key=lambda x: x[1])
            cache.set('USER_CATEGORY_PROFILE_%s' % user.external_id, ucp)
        return ucp

    def get_apps_category_dict(self,sorted_tlist):
        """

        Requires sorted_tlist to be a tuple list sorted by the second element of
        the tuple and the first element to be an app primary key

        :return: A dictionary with categories as keys and a list of app ids.
        :rtype: dict
        """
        acd = cache.get('APP_CATEGORY_PROFILE')
        if not acd:
            part = sorted_tlist[:int(len(sorted_tlist)*CategoryReRanker.PART)]
            rs = Item.objects.filter(id__in=part).values_list('id', 'categories__name')
            acd = {}
            for appID, cat in rs:
                acd[cat] = [] if cat not in acd else acd[cat]+[appID]
            cache.set('APP_CATEGORY_PROFILE', acd)
        return acd


class RepetitionReRanker(ReRanker):
    """
    A re ranker to push installed aps to the end
    """

    def __call__(self, user, app_score, **kwargs):
        """

        """
        user_apps = [app_id for app_id, in user.installed_apps.all().values_list("id")]
        for app_id in user_apps:
            app_score.remove(app_id)
        return app_score + user_apps