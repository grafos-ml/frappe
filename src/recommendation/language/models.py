# -*- encoding=utf-8 -*-
"""
The locale models moudle. It must contain the locale
"""
__author__ = "joaonrb"


from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from recommendation.models import Item, User, CacheManager


class Locale(models.Model):
    """
    Model for a specific locale
    """
    language_code = models.CharField(_("language code"), max_length=2)
    country_code = models.CharField(_("country code"), max_length=2, default="")
    name = models.CharField(_("country"), max_length=255, default="")
    items = models.ManyToManyField(Item, verbose_name=_("items"), related_name="available_locales", blank=True)
    users = models.ManyToManyField(User, verbose_name=_("users"), related_name="required_locales", blank=True)

    all_locales = CacheManager("locallid")
    item_locales = CacheManager("locits")
    user_locales = CacheManager("locusr")
    items_by_locale = CacheManager("locitsb")
    users_by_locale = CacheManager("locusrb")

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
    def load_locale():
        cache = get_cache("models")
        users = User.objects.all()
        for u in users:
            supported_locales = u.required_locales.values_list("language_code", flat=True)
            unsupported_items_or_null = Item.objects.exclude(available_locales__language_code=supported_locales)
            unsupported_items = unsupported_items_or_null.exclude(available_locales__isnull=True)
            cache.set("user<%s>.unsupported_items" % u.external_id, list(unsupported_items), None)


@receiver(post_save, sender=Locale)
def add_locale_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add locale to cache upon creation
    """
    Locale.all_locales[instance.pk] = instance


@receiver(m2m_changed, sender=Locale.items.through)
def add_item_locale_to_cache(sender, instance, action, reverse, model, pk_set, using, *args, **kwargs):
    """
    Add item to locale cache upon creation
    """
    if action == "post_save":
        for i in pk_set:
            Locale.item_locales[i] = Locale.item_locales.get(1, set([]).union((instance.pk,)))
    if action == "post_remove":
        for i in pk_set:
            l = Locale.item_locales.get(i, set([]))
            l.discard(instance.pk)
            Locale.item_locales[i] = l


@receiver(m2m_changed, sender=Locale.users.through)
def add_user_locale_to_cache(sender, instance, action, reverse, model, pk_set, using, *args, **kwargs):
    """
    Add users to locale cache upon creation
    """
    if action == "post_save":
        for u in pk_set:
            Locale.user_locales[u] = Locale.user_locales.get(u, set([]).union((instance.pk,)))
    if action == "post_remove":
        for u in pk_set:
            l = Locale.user_locales.get(u, set([]))
            l.discard(instance.pk)
            Locale.user_locales[u] = l


from django.contrib import admin
admin.site.register([Locale])