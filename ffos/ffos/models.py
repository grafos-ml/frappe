'''
Created on Nov 21, 2013

Django data models for FFOS Users and APPS.

All the data structure is based in previous structures from the FRAPPE app. The
original data was stored using MongoDB so is modeled in Json.


@author: joaonrb
'''


from django.db import models
from django.utils.translation import ugettext as _

class FFOSAppCategory(models.Model):
    '''
    Category of a FireFox OS App. It only has a name.
    '''
    name = models.CharField(_('category name'),max_length=255)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        
    def __unicode__(self):
        return self.name
        
class FFOSDeviceType(models.Model):
    '''
    A FFOS Device type. 
    '''
    name = models.CharField(_('device type'),max_length=255)
    
    class Meta:
        verbose_name = _('device type')
        verbose_name_plural = _('device types')
        
    def __unicode__(self):
        return self.name

class FFOSAppIcon(models.Model):
    '''
    The FireFox App API is, in the moment that this is being developed and
    documented, using 4 sizes of icons. For beauty purposes I decided not to
    put the in the app model. Instead one model to keep the icons and an
    foreign key in the app.
    '''
    size16 = models.URLField(_('icon 16x16'))
    size48 = models.URLField(_('icon 48x48'))
    size64 = models.URLField(_('icon 64x64'))
    size128 = models.URLField(_('icon 128x128'))
    
    class Meta:
        verbose_name = _('app icon')
        verbose_name_plural = _('app icons')
        
    def __unicode__(self):
        '''
        Return the name of the app + the word icon
        '''
        return _('%(app_name)s icon') % {'app_name': self.app.name}
        
class Region(models.Model):
    '''
    A region defined by the FireFox system for the mobile geo system. This is
    the geo information the app can give to the system.
    '''
    adolescent = models.BooleanField(_('adolescent'))
    
    # I will make this a big number for the same reasons bellow
    mcc =  models.BigIntegerField(_('mcc'))
    
    # And this a big string
    name = models.CharField(_('name'),max_length=255)
    
    slug = models.CharField(_('slug'),max_length=5)
    
    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')
        
    def __unicode__(self):
        return self.name
        
class Locales(models.Model):
    '''
    Locales to be assigned to the app support
    '''
    name = models.CharField(_('locale'),max_length=5)
    
    class Meta:
        verbose_name = _('locale')
        verbose_name_plural = _('locales')
        
    def __unicode__(self):
        return self.name
        
class FFOSApp(models.Model):
    '''
    FireFox OS App. It keeps the app data of a firefox os application. Some of
    the data types are not clear in the API so it may have to be changed in the
    future. So for many char fields I'm going to use 255 length. Linas said it
    was fine.
    '''
    
    app_type = models.CharField(_('app type'),max_length=255)
    
    author = models.CharField(_('author'),max_length=255)
    
    categories = models.ManyToManyField(FFOSAppCategory,
        verbose_name=_('categories'),related_name='apps')
    
    content_ratings = models.CharField(_('content rating'),max_length=255,
        null=True,blank=True)
    
    created = models.DateTimeField(_('created date'))
    
    current_version = models.CharField(_('current version'),max_length=10)
    
    default_locale = models.CharField(_('default locale'),max_length=5)
    
    description = models.TextField(_('description'))
    
    device_types = models.ManyToManyField(FFOSDeviceType,
        verbose_name=_('device types'),related_name='apps')
    
    home_page = models.URLField(_('home page'))
    
    icon = models.ForeignKey(FFOSAppIcon,verbose_name=_('app icon'),
        related_name='app')
    
    ffos_app_id = models.BigIntegerField(_('firefox app id'))
    
    is_packed = models.BooleanField(_('is packed?'))
    
    manifest_url = models.URLField(_('manifest url'))
    
    name = models.CharField(_('name'),max_length=255)
    
    payment_account = models.CharField(_('payment account'),max_length=255,
        null=True,blank=True)
    
    price_locale = models.CharField(_('price locale'),max_length=255,null=True,
        blank=True)
    
    privacy_policy = models.CharField(_('privacy policy'), max_length=255)
    
    public_stats = models.BooleanField(_('public stats'))
    
    rating_average = models.DecimalField(_('rating (average)'),max_digits=10,
        decimal_places=3)
    
    rating_count = models.BigIntegerField(_('rating count'))
    
    regions = models.ManyToManyField(Region,verbose_name=_('regions'),
        related_name='apps')
    
    recource_uri = models.CharField(_('recource uri'),max_length=255)
    
    slug = models.CharField(_('slug'),max_length=255)
    
    status = models.IntegerField(_('status'),max_length=4)
    
    support_email = models.EmailField(_('support e-mail'))
    
    support_url = models.URLField(_('support url'))
    
    supported_locales = models.ManyToManyField(Locales,
        verbose_name=_('supported locales'),related_name='apps')
    
    tags = models.TextField(_('tags'))
    
    upsell = models.BooleanField(_('upsell'))
    
    upsold = models.CharField(_('upsold'),max_length=255,null=True,blank=True)
    
    weekly_downloads = models.CharField(_('weekly downloads'),max_length=255,
        null=True,blank=True)
    
    class Meta:
        verbose_name = _('firefox os app')
        verbose_name_plural = _('firefox os apps')
        
    def __unicode__(self):
        return _('%(app_name)s version %(version)s') % {'app_name': self.name,
                                                        'version': self.version}

class FFOSUser(models.Model):
    '''
    FireFox OS User/client. Is a model for FFOS experience information. Some id
    stamp and locale info mostly.
    
    > IMPORTANT: The unique internal id is standard SQL incremented ID. The
    > implementation it depends on the DBMS type and settings. Maybe is a topic
    > to discuss.
    '''
    
    # Length is 5 not only for 'en' type of lang but also to the 'en_en' kind.
    # Can lang be null???
    # Lang or Locale???
    locale = models.CharField(_('locale'),max_length=5,null=True,blank=True)
    
    # Length is 25, a bit more than 'Santa Cruz de Tenerife', the largest name
    # in the list of Spanish regions.
    region = models.CharField(_('region'),max_length=25,null=True,blank=True)
    
    # Length is 70, a bit more than the dummy data field send by FireFox. Linas
    # said it's fine.
    # The documentation defines this has a md5 hash so a 32 hexa digit will be
    # enough?
    external_id = models.CharField(_('external id'),max_length=70,unique=True)
    
    installed_apps = models.ManyToManyField(FFOSApp,
        verbose_name=_('installed apps'),related_name='users')
    
    class Meta:
        verbose_name = _('firefox client')
        verbose_name_plural = _('firefox clients')
        
    def __unicode__(self):
        '''
        Return the word client followed by the client external id
        '''
        return _('client %(external_id)s') % {'external_id': self.external_id}
        

from django.contrib import admin

admin.site.register([FFOSApp,FFOSUser,FFOSAppCategory,FFOSAppIcon,
    FFOSDeviceType,Region,Locales])
    
    
    