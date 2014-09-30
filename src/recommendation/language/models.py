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
    items = models.ManyToManyField(Item, verbose_name=_("items"), through="ItemLocale", blank=True, null=True)
    users = models.ManyToManyField(User, verbose_name=_("users"), through="UserLocale", blank=True, null=True)

    class Meta:
        verbose_name = _("locale")
        verbose_name_plural = _("locales")
        unique_together = ("language_code", "country_code")

    def __str__(self):
        return "%s%s" % (self.language_code, "-%s" % self.country_code if self.country_code else "")

    def __unicode__(self):
        return u"%s%s" % (self.language_code, "-%s" % self.country_code if self.country_code else "")

    @staticmethod
    @Cached(cache="local", timeout=60*60)
    def get_all_locales():
        return {locale.pk: locale for locale in Locale.objects.all()}

    @staticmethod
    @Cached(cache="local")
    def get_item_locales(item_id):
        return set([pk[0] for pk in Item.get_item_by_id(item_id).locales.all().values_list("locale_id")])

    @staticmethod
    @Cached(cache="local")
    def get_user_locales(user_id):
        return set([pk[0] for pk in User.get_user_by_id(user_id).locales.all().values_list("locale_id")])

    @staticmethod
    @Cached(cache="local", timeout=60*60)
    def get_items_by_locale(locale_id):
        return set([pk[0] for pk in ItemLocale.objects.filter(locale_id=locale_id).values_list("item_id")])

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


class ItemLocale(models.Model):
    """
    Many to many table to locales
    """

    locale = models.ForeignKey(Locale, verbose_name=_("locale"))
    item = models.ForeignKey(Item, verbose_name=_("item"), related_name="locales")

    class Meta:
        verbose_name = _("item locale")
        verbose_name_plural = _("item locales")
        unique_together = ("locale", "item")

    def __str__(self):
        return "%s: %s" % (self.item, self.locale)

    def __unicode__(self):
        return u"%s: %s" % (self.item, self.locale)


class UserLocale(models.Model):
    """
    Many to many table to locales
    """

    locale = models.ForeignKey(Locale, verbose_name=_("locale"))
    user = models.ForeignKey(User, verbose_name=_("user"), related_name="locales")

    class Meta:
        verbose_name = _("user locale")
        verbose_name_plural = _("user locales")
        unique_together = ("locale", "user")

    def __str__(self):
        return "%s: %s" % (self.user, self.locale)

    def __unicode__(self):
        return u"%s: %s" % (self.user, self.locale)

from django.contrib import admin
admin.site.register([Locale, ItemLocale, UserLocale])