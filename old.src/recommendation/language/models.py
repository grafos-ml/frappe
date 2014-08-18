# -*- encoding=utf-8 -*-
"""
The locale models moudle. It must contain the locale
"""
__author__ = "joaonrb"


from django.db import models
from django.utils.translation import ugettext as _
from recommendation.models import Item, User
from django.core.cache import get_cache


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
    def load_unsupported_items_by_locale():
        cache = get_cache("models")
        users = User.objects.all()
        for u in users:
            supported_locales = u.required_locales.values_list("language_code", flat=True)
            unsupported_items_or_null = Item.objects.exclude(available_locales__language_code=supported_locales)
            unsupported_items = unsupported_items_or_null.exclude(available_locales__isnull=True)
            cache.set("user<%s>.unsupported_items" % u.external_id, list(unsupported_items), None)

    @staticmethod
    def get_unsupported_items_by_locale(user):
        cache = get_cache("models")
        return cache.get("user<%s>.unsupported_items" % user.external_id)

from django.contrib import admin
admin.site.register([Locale])