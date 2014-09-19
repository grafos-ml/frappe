#! -*- encoding: utf-8 -*-
"""
Dummy model for testing
"""
__author__ = "joaonrb"

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from recommendation.models import CacheManager


class TestLocalCache(models.Model):

    token = models.IntegerField(max_length=20)

    cache = CacheManager("testlocalcache")


@receiver(post_save, sender=TestLocalCache)
def add_to_cache(sender, instance, created, raw, using, update_fields, *args, **kwargs):
    p = TestLocalCache.cache.get("dummy_lct", [])
    p.append(instance.token)
    TestLocalCache.cache["dummy_lct"] = p