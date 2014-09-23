# -*- encoding=utf-8 -*-
"""
The locale models moudle. It must contain the locale
"""
__author__ = "joaonrb"


from django.db import models
from django.utils.translation import ugettext as _
from recommendation.models import Item, User
from recommendation.decorators import Cached


class Locale(models.Model):
    """
    Model for a specific locale
    """
    language_code = models.CharField(_("language code"), max_length=2)
    country_code = models.CharField(_("country code"), max_length=2, default="")
    name = models.CharField(_("country"), max_length=255, default="")
    items = models.ManyToManyField(Item, verbose_name=_("items"), related_name="available_locales", blank=True)
    users = models.ManyToManyField(User, verbose_name=_("users"), related_name="required_locales", blank=True)

    class Meta:
        verbose_name = _("locale")
        verbose_name_plural = _("locales")
        unique_together = ("language_code", "country_code")

    def __str__(self):
        return "%s%s" % (self.language_code, "-%s" % self.country_code if self.country_code else "")

    @staticmethod
    @Cached(cache="local", timeout=60*60)
    def get_all_locales():
        return {locale.pk: locale for locale in Locale.objects.all()}

    @staticmethod
    @Cached(cache="local")
    def get_item_locales(item_id):
        return set([pk for pk, in Locale.objects.filter(items__in=[item_id]).values_list("pk")])

    @staticmethod
    @Cached(cache="local")
    def get_user_locales(user_id):
        return set([pk for pk, in Locale.objects.filter(users__in=[user_id]).values_list("pk")])

    @staticmethod
    @Cached(cache="local", timeout=60*60)
    def get_items_by_locale(locale_id):
        return set([pk for pk, in Item.objects.filter(available_locales__in=[locale_id]).values_list("pk")])

    def save(self, *args, **kwargs):
        """
        Makes the codes to be saved always using lower case
        :param args:
        :param kwargs:
        :return:
        """
        self.language_code = self.language_code.lower()
        self.country_code = self.country_code.lower()
        super(Locale, self).save(*args, **kwargs)

    @staticmethod
    def load_to_cache():
        for locale_id in Locale.get_all_locales():
            Locale.get_item_locales(locale_id)
            Locale.get_items_by_locale(locale_id)
        for u in User.objects.all():
            Locale.get_user_locales(u.pk)
        for i in Item.objects.all():
            Locale.get_item_locales(i.pk)


from django.contrib import admin
admin.site.register([Locale])