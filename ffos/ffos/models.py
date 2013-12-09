'''
Created on Nov 21, 2013

Django data models for FFOS Users and APPS.

All the data structure is based in previous structures from the FRAPPE app. The
original data was stored using MongoDB so is modeled in Json.


.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>
'''


from django.db import models, connection
from django.utils.translation import ugettext as _
from ffos.util import parseDir
from django.utils.timezone import utc
from datetime import datetime
import itertools, collections, logging

BULK_QUERY = 'INSERT INTO %(table)s %(columns)s VALUES %(values)s;'

class Filterble(object):


    @classmethod
    def in_db(cls,obj):
        '''
        Filter the enter queue so don't have any repetitions or
        crash database query
        '''
        if not hasattr(cls,'olds'):
            cls.olds = cls.already_in_db()
        if not hasattr(cls,'news'):
            cls.news = set(),[]
        return cls.identify(obj) in cls.olds.keys()

    @classmethod
    def already_in_db(cls):
        '''
        Return a list o identifiers of the categories in db
        '''
        return {cls.identify_obj(obj): obj for obj in cls.objects.all()}

    @classmethod
    def prepare(cls,app):
        objs = [cls.get_obj(app)] if not cls.has_many(cls.get_obj(app)) \
            else cls.get_obj(app)
        result = []
        for obj in objs:
            if cls.in_db(obj):
                result.append(cls.olds[cls.identify(obj)])
            else:
                result.append(cls.prepare_to_db(cls.identify(obj)))
                cls.news[0].add(cls.identify(obj))
                if len(cls.news[0]) != len(cls.news[1]):
                    cls.news[1].append(result[-1])
        return result if cls.has_many(cls.get_obj(app)) else result[0]

    @classmethod
    def has_many(cls,obj):
        return isinstance(obj,collections.Iterable) and \
            not isinstance(obj,dict)

    @classmethod
    def new_to_add(cls):
        return cls.news[1]



class FFOSAppCategory(models.Model, Filterble):
    '''
    Category of a FireFox OS App. It only has a name.
    '''
    name = models.CharField(_('category name'),max_length=255)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        
    def __unicode__(self):
        return self.name

    @classmethod
    def identify(cls,obj):
        return obj

    @classmethod
    def identify_obj(cls,obj):
        return obj.name

    @classmethod
    def prepare_to_db(cls,ident):
        '''
        Prepares the object to db based on its identifier
        '''
        return FFOSAppCategory(name=ident)

    @classmethod
    def get_obj(cls,app):
        return app['categories']

        
class FFOSDeviceType(models.Model, Filterble):
    '''
    A FFOS Device type. 
    '''
    name = models.CharField(_('device type'),max_length=255)
    
    class Meta:
        verbose_name = _('device type')
        verbose_name_plural = _('device types')
        
    def __unicode__(self):
        return self.name

    @classmethod
    def identify(cls,obj):
        '''
        An identifier for the object. May be a str or a tuple with str.
        '''
        return obj

    @classmethod
    def identify_obj(cls,obj):
        return obj.name

    @classmethod
    def prepare_to_db(cls,ident):
        '''
        Prepares the object to db based on its identifier
        '''
        return FFOSDeviceType(name=ident)

    @classmethod
    def get_obj(cls,app):
        return app['device_types']

class FFOSAppIcon(models.Model, Filterble):
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
        #return _('%(app_name)s icon') % {'app_name': self.app.name}
        return self.size16

    @classmethod
    def identify(cls,obj):
        '''
        An identifier for the object. May be a str or a tuple with str.
        '''
        return obj['16'],obj['48'],obj['64'],obj['128']

    @classmethod
    def identify_obj(cls,obj):
        return obj.size16,obj.size48,obj.size64,obj.size128

    @classmethod
    def prepare_to_db(cls,ident):
        '''
        Prepares the object to db based on its identifier
        '''
        return FFOSAppIcon(size16=ident[0],size48=ident[1],size64=ident[2],
            size128=ident[3])

    @classmethod
    def get_obj(cls,app):
        return app['icons']

        
class Region(models.Model, Filterble):
    '''
    A region defined by the FireFox system for the mobile geo system. This is
    the geo information the app can give to the system.
    '''
    adolescent = models.BooleanField(_('adolescent'))
    
    # I will make this a big number for the same reasons bellow
    mcc =  models.BigIntegerField(_('mcc'),null=True,blank=True)
    
    # And this a big string
    name = models.CharField(_('name'),max_length=255)
    
    slug = models.CharField(_('slug'),max_length=255,null=True,blank=True)
    
    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')
        
    def __unicode__(self):
        return self.name

    @classmethod
    def identify(cls,obj):
        '''
        An identifier for the object. May be a str or a tuple with str.
        '''
        return obj['mcc'],obj['name'],obj['adolescent'],obj['slug']

    @classmethod
    def identify_obj(cls,obj):
        return obj.mcc,obj.name,obj.adolescent,obj.slug

    @classmethod
    def prepare_to_db(cls,ident):
        '''
        Prepares the object to db based on its identifier
        '''
        return Region(mcc=ident[0],name=ident[1],adolescent=ident[2],
            slug=ident[3])

    @classmethod
    def get_obj(cls,app):
        return app['regions']
        
class Locale(models.Model, Filterble):
    '''
    Locales to be assigned to the app support
    '''
    name = models.CharField(_('locale'),max_length=5)
    
    class Meta:
        verbose_name = _('locale')
        verbose_name_plural = _('locales')
        
    def __unicode__(self):
        return self.name

    @classmethod
    def identify(cls,obj):
        '''
        An identifier for the object. May be a str or a tuple with str.
        '''
        return obj

    @classmethod
    def identify_obj(cls,obj):
        return obj.name

    @classmethod
    def prepare_to_db(cls,ident):
        '''
        Prepares the object to db based on its identifier
        '''
        return Locale(name=ident)

    @classmethod
    def get_obj(cls,app):
        return app['supported_locales']

class Preview(models.Model, Filterble):
    '''
    Information about the app previews
    '''
    filetype = models.CharField(_('file type'),max_length=255)
    thumbnail_url = models.URLField(_('thumbnail url'))
    image_url = models.URLField(_('image url'))
    ffos_preview_id = models.BigIntegerField(_('firefox preview id'))
    resource_uri = models.CharField(_('resource id'),max_length=255)
    
    class Meta:
        verbose_name = _('preview')
        verbose_name_plural = _('previews')
        
    def __unicode__(self):
        return _('%(app)s preview with id %(preview_id)s') % {'app': self.app, 
            'preview_id': self.ffos_preview_id}

    @classmethod
    def identify(cls,obj):
        '''
        An identifier for the object. May be a str or a tuple with str.
        '''
        return obj['filetype'],obj['thumbnail_url'],obj['image_url'],\
            obj['id'],obj['resource_uri']

    @classmethod
    def identify_obj(cls,obj):
        return obj.filetype,obj.thumbnail_url,obj.image_url,\
            str(int(obj.ffos_preview_id)),obj.resource_uri

    @classmethod
    def prepare_to_db(cls,ident):
        '''
        Prepares the object to db based on its identifier
        '''
        return Preview(filetype=ident[0],thumbnail_url=ident[1],
            image_url=ident[2],ffos_preview_id=ident[3],
            resource_uri=ident[4])

    @classmethod
    def get_obj(cls,app):
        return app['previews']
        
class FFOSApp(models.Model):
    '''
    FireFox OS App. It keeps the app data of a firefox os application. Some of
    the data types are not clear in the API so it may have to be changed in the
    future. So for many char fields I'm going to use 255 length. Linas said it
    was fine.
    '''

    #def __init__(self,*args,**kwargs):
    #    super(FFOSApp,self).__init__(*args,**kwargs)
    #    print '.',
    
    app_type = models.CharField(_('app type'),max_length=255)
    
    author = models.CharField(_('author'),max_length=255,null=True,blank=True)
    
    categories = models.ManyToManyField(FFOSAppCategory,blank=True,
        verbose_name=_('categories'),related_name='apps')

    # Sometimes data cames as other stuff
    content_ratings = models.TextField(_('content rating'),null=True,blank=True)
    
    created = models.DateTimeField(_('created date'),null=True,blank=True)

    # Change to 255 length because of data problems
    current_version = models.CharField(_('current version'),max_length=255,
        null=True,blank=True)
    
    default_locale = models.CharField(_('default locale'),max_length=5)
    
    description = models.TextField(_('description'),null=True,blank=True)
    
    device_types = models.ManyToManyField(FFOSDeviceType,blank=True,
        verbose_name=_('device types'),related_name='apps')
    
    homepage = models.URLField(_('homepage'),null=True,blank=True)
    
    icon = models.ForeignKey(FFOSAppIcon,verbose_name=_('app icon'),
        related_name='app',blank=True)
    
    external_id = models.BigIntegerField(_('external id'),unique=True)
    
    is_packaged = models.BooleanField(_('is packaged?'))
    
    manifest_url = models.URLField(_('manifest url'))
    
    name = models.CharField(_('name'),max_length=255)
    
    payment_account = models.CharField(_('payment account'),max_length=255,
        null=True,blank=True)
    
    payment_required = models.BooleanField(_('is payment required?'))
    
    price_locale = models.CharField(_('price locale'),max_length=255,null=True,
        blank=True)
    
    price = models.CharField(_('price'),max_length=255,null=True,blank=True)
    
    premium_type = models.CharField(_('primium type'),max_length=255,null=True,
        blank=True)
    
    privacy_policy = models.CharField(_('privacy policy'), max_length=255)
    
    public_stats = models.BooleanField(_('public stats'))
    
    rating_average = models.DecimalField(_('rating (average)'),max_digits=10,
        decimal_places=3)
    
    rating_count = models.BigIntegerField(_('rating count'))
    
    regions = models.ManyToManyField(Region,verbose_name=_('regions'),
        blank=True,related_name='apps')
    
    resource_uri = models.CharField(_('resource uri'),max_length=255,
        null=True,blank=True)
    
    slug = models.CharField(_('slug'),max_length=255,null=True,blank=True)
    
    status = models.IntegerField(_('status'),max_length=4)
    
    support_email = models.EmailField(_('support e-mail'),null=True,blank=True)
    
    support_url = models.URLField(_('support url'),null=True,blank=True)
    
    supported_locales = models.ManyToManyField(Locale,blank=True,
        verbose_name=_('supported locales'),related_name='apps')
    
    tags = models.TextField(_('tags'))
    
    upsell = models.BooleanField(_('upsell'))
    
    upsold = models.CharField(_('upsold'),max_length=255,null=True,blank=True)
    
    weekly_downloads = models.CharField(_('weekly downloads'),max_length=255,
        null=True,blank=True)
    
    previews = models.ManyToManyField(Preview,verbose_name=_('previews'),
        blank=True,related_name='app')
    
    class Meta:
        verbose_name = _('firefox os app')
        verbose_name_plural = _('firefox os apps')
        
    def __unicode__(self):
        return _('%(app_name)s version %(version)s') % {'app_name': self.name,
            'version': self.current_version}

    @staticmethod
    def load(*apps):
        '''
        Load all json to the database. It assumes that all the files are in the
        FFOSApp format.

        If the apps parameter is according with the prerequisites (respect the
        format) this function should ENSURE that, if the execution ends
        normally, in the end all the data is available in the database.

        **Args**

        ''*''apps *list*:
            A List of dicts with json. Every json in the file must respect the
            following format::

                {
                    "premium_type": String(255),
                    "content_ratings": String(255),
                    "manifest_url": String(url),
                    "current_version": String(10),
                    "upsold": String(255),
                    "id": String(20) or Integer(20),
                    "ratings": {
                        "count": Integer(10),
                        "average": float(10,3)
                    },
                    "app_type": String(255),
                    "author": String(255),
                    "support_url": String(url),
                    "slug": String(255),
                    "regions": [
                        {
                            "mcc": Integer(20),
                            "name": String(255),
                            "adolescent": boolean,
                            "slug": String(5)
                        },...
                    ],
                    "icons": {
                        "16": String(url),
                        "48": String(url),
                        "64": String(url),
                        "128": String(url)
                    },
                    "created": The date when the app was installed in the format
                        "yyyy-mm-ddThh:mm:ss",
                    "homepage": String(url),
                    "support_email": String(255),
                    "public_stats": boolean,
                    "status": integer(4),
                    "privacy_policy": String(255),
                    "is_packaged": boolean,
                    "description": text,
                    "default_locale": String(5),
                    "price": String(255),
                    "previews": [
                        {
                            "filetype": String(255),
                            "thumbnail_url": String(url),
                            "image_url": String(url),
                            "id": String(20) or Integer(20),
                            "resource_uri": String(255)
                        },...
                    ],
                    "payment_account": String(255),
                    "categories": [
                        String(255),
                        ...
                        ],
                    "supported_locales": [
                        String(5),
                        ...
                        ],
                    "price_locale": String(255),
                    "name": "String(255),
                    "versions": {
                        Whatever, this is not going to be use for now
                    },
                    "device_types": [
                        String(255),
                        ...
                    ],
                    "payment_required": boolean,
                    "weekly_downloads": String(255),
                    "upsell": boolean,
                    "resource_uri": String(255)
                }

        '''
        cursor = connection.cursor()
        apps = [(app,FFOSAppIcon.prepare(app),FFOSAppCategory.prepare(app),
            FFOSDeviceType.prepare(app),Region.prepare(app),
            Locale.prepare(app),Preview.prepare(app))
            for app in apps]

        logging.info('Loading icons')
        FFOSAppIcon.objects.bulk_create(FFOSAppIcon.new_to_add())
        icons = {FFOSAppIcon.identify_obj(i): i \
            for i in FFOSAppIcon.objects.all()}

        logging.info('Loading apps')
        try:
            FFOSApp.objects.bulk_create([FFOSApp(
                premium_type = app['premium_type'],
                content_ratings = app['content_ratings'],
                manifest_url = app['manifest_url'],
                current_version = app['current_version'],
                upsold = app['upsold'],
                external_id = app['id'],
                rating_count = app['ratings']['count'],
                rating_average = app['ratings']['average'],
                app_type = app['app_type'],
                author = app.get('author',None),
                support_url = app['support_url'],
                slug = app['slug'],
                icon=icons[FFOSAppIcon.identify(app['icons'])],
                created = datetime.strptime(app['created'],
                    '%Y-%m-%dT%H:%M:%S').replace(tzinfo=utc)
                    if 'created' in app else None,
                homepage = app['homepage'],
                support_email = app['support_email'],
                public_stats = app['public_stats'],
                status = app['status'],
                privacy_policy = app['privacy_policy'],
                is_packaged = app['is_packaged'],
                description = app['description'],
                default_locale = app['default_locale'],
                price = app['price'],
                payment_account = app['payment_account'],
                price_locale = app['price_locale'],
                name = app['name'],

                # Choose false because it looks logical
                payment_required = app.get('payment_required',False),
                weekly_downloads = app.get('weekly_downloads',None),
                upsell = app['upsell'],
                resource_uri = app['resource_uri']
            ) for app,_,_,_,_,_,_ in apps])
        except Exception as e:
            logging.error('%s %s' % (str(app['id']),e))

        # Load all apps to cach. Yet to be improved
        #apps = {a['id']: a for a in zip(*apps)[0]}
        apps = dict(map(lambda x: (x['id'],x),zip(*apps)[0]))
        for a in FFOSApp.objects.all():
            apps[str(int(a.external_id))] = apps[str(int(a.external_id))], a

        logging.info('Loading categories')
        FFOSAppCategory.objects.bulk_create(FFOSAppCategory.new_to_add())

        # Cache all the categories for relation with app. (Yet to be improved)
        categories = {FFOSAppCategory.identify_obj(c): c
            for c in FFOSAppCategory.objects.all()}

        logging.info('Loading device types')
        FFOSDeviceType.objects.bulk_create(FFOSDeviceType.new_to_add())

        # Cache all the devices for relation with app. (Yet to be improved)
        device_type = {FFOSDeviceType.identify_obj(dt): dt
            for dt in FFOSDeviceType.objects.all()}

        logging.info('Loading regions')
        Region.objects.bulk_create(Region.new_to_add())

        # Cache all the regions for relation with app. (Yet to be improved)
        regions = {Region.identify_obj(r): r for r in Region.objects.all()}

        logging.info('Loading locales')
        Locale.objects.bulk_create(Locale.new_to_add())

        # Cache all the locales for relation with app. (Yet to be improved)
        locales = {Locale.identify_obj(l): l for l in Locale.objects.all()}

        logging.info('Loading previews')
        Preview.objects.bulk_create(Preview.new_to_add())

        # Cache all the previews for relation with app. (Yet to be improved)
        previews = {Preview.identify_obj(p): p for p in Preview.objects.all()}

        # Starting to build a raw query for many to many bulk insertion

        logging.info('Loading relations')
        values_cat, values_dev, values_reg, values_loc, values_prev = set([]),\
            set([]), set([]), set([]), set([])
        for a_json, a_obj in apps.values():
            values_cat = itertools.chain(values_cat,set(['(%s, %s)' % \
                (a_obj.pk,categories[FFOSAppCategory.identify(c)].pk)
                for c in FFOSAppCategory.get_obj(a_json)]))
            values_dev = itertools.chain(values_dev, set(['(%s, %s)' % \
                (a_obj.pk,device_type[FFOSDeviceType.identify(dt)].pk)
                for dt in FFOSDeviceType.get_obj(a_json)]))
            values_reg = itertools.chain(values_reg, set(['(%s,%s)' % \
                (a_obj.pk,regions[Region.identify(r)].pk)
                for r in Region.get_obj(a_json)]))
            values_loc = itertools.chain(values_loc, set(['(%s,%s)' % \
                (a_obj.pk,locales[Locale.identify(l)].pk)
                for l in Locale.get_obj(a_json)]))
            values_prev = itertools.chain(values_prev, set(['(%s,%s)' % \
                (a_obj.pk,previews[Preview.identify(p)].pk)
                for p in Preview.get_obj(a_json)]))

        logging.info('Almost there')
        if values_cat:
            cursor.execute(BULK_QUERY % {'table': 'ffos_ffosapp_categories',
                'columns': '(ffosapp_id, ffosappcategory_id)',
                'values': ','.join(values_cat)})
        if values_dev:
            cursor.execute(BULK_QUERY % {'table': 'ffos_ffosapp_device_types',
                'columns': '(ffosapp_id, ffosdevicetype_id)',
                'values': ','.join(values_dev)})
        if values_reg:
            cursor.execute(BULK_QUERY % {'table': 'ffos_ffosapp_regions',
                'columns': '(ffosapp_id, region_id)',
                'values': ','.join(values_reg)})
        if values_loc:
            cursor.execute(BULK_QUERY % {'table':
                'ffos_ffosapp_supported_locales',
                'columns': '(ffosapp_id, locale_id)',
                'values': ','.join(values_loc)})
        if values_prev:
            cursor.execute(BULK_QUERY % {'table': 'ffos_ffosapp_previews',
                'columns': '(ffosapp_id, preview_id)',
                'values': ','.join(values_prev)})
        logging.info('Done!')


class FFOSUser(models.Model):
    '''
    FireFox OS User/client. Is a model for FFOS experience information. Some id
    stamp and locale info mostly::
    
        IMPORTANT: The unique internal id is standard SQL incremented ID. The
        implementation it depends on the DBMS type and settings. Maybe is a
        topic to discuss.

    '''
    
    # Length is 5 not only for 'en' type of lang but also to the 'en_en' kind.
    # Can lang be null???
    # Lang or Locale???
    locale = models.CharField(_('locale'),max_length=5,null=True,blank=True)
    
    region = models.CharField(_('region'),max_length=255,null=True,blank=True)
    
    # Length is 255, more than the dummy data field send by FireFox. Linas
    # said it's fine.
    # The documentation defines this has a md5 hash so a 32 hexa digit will be
    # enough?
    external_id = models.CharField(_('external id'),max_length=255,unique=True)
    
    installed_apps = models.ManyToManyField(FFOSApp,blank=True,
        verbose_name=_('installed apps'),related_name='users',
        through='Installation')
    
    class Meta:
        verbose_name = _('firefox client')
        verbose_name_plural = _('firefox clients')
        
    def __unicode__(self):
        '''
        Return the word client followed by the client external id
        '''
        return _('client %(external_id)s') % {'external_id': self.external_id}

    def load(*users):
        '''
        Load a list of users to the data model FFOSUser. It also make the
        connection to the installed apps.

        If the users parameter is according with the prerequisites (respects the
        format and for every installed app that app already is registered in
        database) this function should ENSURE that, if the execution ends
        normally, in the end all the data is available in database.

        **Args**

        users *dict*:
            A list with Python dictionaries, each one representing a user.
            Is required that each user as the following format::

                {
                    'lang': two or five size string in the locale format,
                    'region': Although I think this is just a 2 string code of
                        the region, it allow far more (255 length),
                    'user': Is a big string, documented as a md5 hash with size
                        35, but the dummy data has far more than that. To play
                        it safe we use 255.
                    'installed_apps': [
                        {
                            'installed': The date when the app was installed in
                                the format "yyyy-mm-ddThh:mm:ss",
                            'id': The id of the installed app. This should be
                                already on the database.
                            'slug': The slug of the app. It's an important
                                value.
                        },
                        More apps with the same format as the last one...
                    ]
                }
        '''
        logging.info('Preparing user data')
        new_users, apps, install = [], [], []
        for user in users:
            new_users.append(FFOSUser(locale=user['lang'],region=['region'],
                external_id=user['user']))
            for app in user['installed_apps']:
                apps.append(app['id'])
                install.append((user['user'],app['id'],
                    datetime.strptime(app['installed'],"%Y-%m-%dT%H:%M:%S")\
                    .replace(tzinfo=utc)))
        logging.info('Loading users')
        FFOSUser.objects.bulk_create(new_users)
        users = {u['external_id']: u['pk'] for u in FFOSUser.objects.filter(
            external_id__in=map(lambda x: x.external_id,new_users)).values('pk',
                'external_id')}
        apps = {a['external_id']: a['pk'] for a in FFOSApp.objects.filter(
            external_id__in=apps).values('pk','external_id')}
        logging.info('Loading installed apps')
        Installation.objects.bulk_create([Installation(user=users[i[0]],
            app=apps[i[1]],installation_date=i[2]) for i in install])

class Installation(models.Model):
    '''
    The connection between the user and the app. It has information about the
    user and the app such as installation date and eventually the date in which
    the app was removed.
    '''
    user = models.ForeignKey(FFOSUser,verbose_name=_('user'))
    app = models.ForeignKey(FFOSApp,verbose_name=_('app'))
    installation_date = models.DateTimeField(_('installation date'))
    removed_date = models.DateTimeField(_('removed date'),
        null=True,blank=True)
    
    class Meta:
        verbose_name = _('installation')
        verbose_name_plural = _('installations')
        
    def __unicode__(self):
        return _('%(state)s %(app)s app for user %(user)s') % {
            'state': _('removed') if self.removed_date else _('installed'),
            'app': self.app.name, 'user': self.user.external_id}

from django.contrib import admin

admin.site.register([FFOSApp,FFOSUser,FFOSAppCategory,FFOSAppIcon,
    FFOSDeviceType,Region,Locale,Installation])
    
    
    