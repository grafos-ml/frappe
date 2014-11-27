#! -*- encoding: utf-8 -*-
"""
Models for the base of the recommendation system. The base of the recommendation system makes uses of the user, item
amd connection between them.
"""

from __future__ import division, absolute_import, print_function
import click
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from frappe.decorators import Cached

__author__ = "joaonrb"


class Item(models.Model):
    """
    Item to be used by recommending system
    """
    name = models.CharField(_("name"), max_length=255)
    external_id = models.CharField(_("external id"), max_length=255, unique=True)

    @staticmethod
    def get_item_by_id(item_id):
        """
        Return item by id.
        """
        return Item.get_item_by_external_id(Item.get_item_external_id_by_id(item_id))

    @staticmethod
    @Cached()
    def get_item_external_id_by_id(item_id):
        """
        Return item id from external_id.
        """
        return Item.objects.filter(pk=item_id).values_list("external_id")[0][0]

    @staticmethod
    @Cached()
    def get_item_by_external_id(external_id):
        """
        Return item from external id.
        """
        return Item.objects.get(external_id=external_id)

    def put_item_to_cache(self):
        """
        Loads an app to database.
        """
        Item.get_item_by_external_id.lock_this(
            Item.get_item_by_external_id.cache.set
        )(Item.get_item_by_external_id.key(self.external_id), self, Item.get_item_by_external_id.timeout)
        Item.get_item_external_id_by_id.lock_this(
            Item.get_item_external_id_by_id.cache.set
        )(Item.get_item_external_id_by_id.key(self.pk), self.external_id, Item.get_item_external_id_by_id.timeout)

    def del_item_from_cache(self):
        """
        delete an app to database
        """
        Item.get_item_by_external_id.lock_this(
            Item.get_item_by_external_id.cache.delete
        )(Item.get_item_by_external_id.key(self.external_id))
        Item.get_item_external_id_by_id.lock_this(
            Item.get_item_external_id_by_id.cache.delete
        )(Item.get_item_external_id_by_id.key(self.pk))

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def load_to_cache():
        with click.progressbar(Item.objects.all(), label="Loading items to cache") as bar:
            for item in bar:
                item.put_item_to_cache()


@receiver(post_save, sender=Item)
def add_item_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.put_item_to_cache()


@receiver(post_delete, sender=Item)
def delete_item_to_cache(sender, instance, using, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.del_item_from_cache()


class User(models.Model):
    """
    User to own items in recommendation system.
    """
    external_id = models.CharField(_("external id"), max_length=255, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), blank=True, through="Inventory")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.external_id

    def __unicode__(self):
        return unicode(self.external_id)

    @staticmethod
    @Cached()
    def get_user_by_id(user_id):
        """
        Get user by their id
        :param user_id: User id
        :return: A user instance
        """
        return User.objects.get(pk=user_id)

    @staticmethod
    @Cached()
    def get_user_id_by_external_id(external_id):
        """
        Get the user id from external id
        :param external_id: User external id
        :return: The user id
        """
        return User.objects.filter(external_id=external_id).values_list("pk")[0][0]

    @staticmethod
    def get_user_by_external_id(external_id):
        """
        Get the user id from external id
        :param external_id: User external id
        :return: The User instance
        """
        return User.get_user_by_id(User.get_user_id_by_external_id(external_id))

    @staticmethod
    @Cached()
    def get_user_items(user_id):
        """
        Get user items
        :param user_id: User id
        :return: A list of user items in inventory
        """
        return {
            entry.item_id: entry.is_dropped
            for entry in Inventory.objects.filter(user_id=user_id)
        }

    @property
    def all_items(self):
        """
        All items from this user. Key item id and value the inventory register
        """
        return {
            item_id: Item.get_item_by_id(item_id)
            for item_id, is_dropped in User.get_user_items(self.pk).items()
        }

    @property
    def owned_items(self):
        """
        Get the owned items from cache. Key item id and value the inventory register
        """
        return {
            item_id: Item.get_item_by_id(item_id)
            for item_id, is_dropped in User.get_user_items(self.pk).items() if not is_dropped
        }

    def has_more_than(self, n):
        """
        Check if user has more than n items owned
        """
        count = 0
        for is_dropped in User.get_user_items(self.pk).values():
            if not is_dropped:
                count += 1
                if count > n:
                    return True
        return False

    @staticmethod
    def load_to_cache():
        with click.progressbar(User.objects.all(), label="Loading users to cache") as bar:
            for user in bar:
                User.get_user_by_id.lock_this(
                    User.get_user_by_id.cache.set
                )(User.get_user_by_id.key(user.pk), user, User.get_user_by_id.timeout)
                User.get_user_id_by_external_id.lock_this(
                    User.get_user_id_by_external_id.cache.set
                )(User.get_user_id_by_external_id.key(user.external_id), user.pk,
                  User.get_user_id_by_external_id.timeout)
        lenght = Inventory.objects.all().count()
        with click.progressbar(range(0, lenght, 100000),
                               label="Loading owned items to cache") as bar:
            inventory = {}
            max_id = 0
            for i in bar:
                for max_id, user_id, item_id, is_dropped in Inventory.objects.filter(id__gt=max_id) \
                        .order_by("pk")[i:i+100000].values_list("pk", "user_id", "item_id", "is_dropped"):
                    try:
                        inventory[user_id][item_id] = is_dropped
                    except KeyError:
                        inventory[user_id] = {
                            item_id: is_dropped
                        }
            for ueid, items in inventory.items():
                User.get_user_items.lock_this(
                    User.get_user_items.cache.set
                )(User.get_user_items.key(ueid), items, User.get_user_items.timeout)

    def load_user(self):
        """
        Load a single user to cache
        """
        User.get_user_by_id.lock_this(
            User.get_user_by_id.cache.set
        )(User.get_user_by_id.key(self.pk), self, User.get_user_by_id.timeout)
        User.get_user_id_by_external_id.lock_this(
            User.get_user_id_by_external_id.cache.set
        )(User.get_user_id_by_external_id.key(self.external_id), self.pk, User.get_user_id_by_external_id.timeout)
        User.get_user_items(self.pk)

    def delete_user(self):
        """
        Load a single user to cache
        """
        User.get_user_by_id.lock_this(
            User.get_user_by_id.cache.delete
        )(User.get_user_by_id.key(self.external_id))
        User.get_user_id_by_external_id.lock_this(
            User.get_user_id_by_external_id.cache.delete
        )(User.get_user_id_by_external_id.key(self.external_id))
        User.get_user_items.lock_this(
            User.get_user_items.cache.delete
        )(User.get_user_items.key(self.external_id))

    def load_item(self, entry):
        """
        Load a single inventory entry
        """
        cache = User.get_user_items.cache
        entries = cache.get(User.get_user_items.key(self.pk), {})
        entries[entry.item_id] = entry.is_dropped
        cache.set(User.get_user_items.key(self.pk), entries)

    def delete_item(self, entry):
        """
        Load a single inventory entry
        """
        cache = User.get_user_items.cache
        entries = cache.get(User.get_user_items.key(self.pk), {})
        try:
            del entries[entry.item.pk]
        except KeyError:
            pass
        cache.set(User.get_user_items.key(self.pk), entries)


@receiver(post_save, sender=User)
def add_user_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.load_user()


@receiver(post_delete, sender=User)
def delete_user_to_cache(sender, instance, using, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.delete_user()


class Inventory(models.Model):
    """
    The connection between the user and the item. It has information about the user and the item such as acquisition
    date and eventually the date in which the item is dropped.
    """
    user = models.ForeignKey(User, verbose_name=_("user"))
    item = models.ForeignKey(Item, verbose_name=_("item"))
    is_dropped = models.BooleanField(_("is dropped"), default=False)

    class Meta:
        verbose_name = _("owned item")
        verbose_name_plural = _("owned items")

    def __str__(self):
        return _("%(state)s %(item)s item for user %(user)s") % {
            "state": _("dropped") if self.is_dropped else _("owned"), "item": self.item.name,
            "user": self.user.external_id}

    def __unicode__(self):
        return _("%(state)s %(item)s item for user %(user)s") % {
            "state": _("dropped") if self.is_dropped else _("owned"), "item": self.item.name,
            "user": self.user.external_id}


@receiver(post_save, sender=Inventory)
def add_inventory_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.user.load_item(instance)


@receiver(post_delete, sender=Inventory)
def delete_inventory_to_cache(sender, instance, using, *args, **kwargs):
    """
    Add item to cache upon creation
    """
    instance.user.delete_item(instance)
