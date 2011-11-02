import logging

from django.utils.importlib import import_module
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.cache import cache
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext_lazy as _

from builders import ChunkBuilder
from listeners import clear_plain_chunk_cache


logger = logging.getLogger(__name__)

CACHE_PREFIX = 'chunks_obj'

# force init of chunks builders
CHUNK_BUILDERS_LIST = getattr(settings, 'CHUNK_BUILDERS', [])
CHUNK_BUILDERS = []

class Chunk(models.Model):
    """
    A Chunk is a piece of content associated
    with a unique key that can be inserted into
    any template with the use of a special template
    tag
    """
    ITEM_CACHE_PREFIX = "chunk_"

    key = models.CharField(_(u"Key"), \
            help_text=_(u"A unique name for this chunk of content"), \
            blank=False, max_length=255, unique=True)    
    content = models.TextField(_(u"Content"), blank=True)
    description = models.CharField(_(u"Description"), max_length=255)

    def clear_cache(self):
        logger.debug(u"Clean up chunk %s" % self.key)
        cache.delete(Chunk.ITEM_CACHE_PREFIX + self.key)

    def build_content(self, request, context):
        """Build content with builder or with default builder"""
        for builder in CHUNK_BUILDERS:
            if builder.appropriate_key(self.key, chunk=self):
                return builder.render(request, self, \
                            parent=None, context=context)
        return self.content

    def __unicode__(self):
        return u"%s" % (self.key,)

    class Meta:
        verbose_name = _(u'Chunk')
        verbose_name_plural = _(u'Chunks')


class InlineChunk(models.Model):
    desc = models.CharField(_(u"Description"), max_length=255)
    key = models.CharField(_(u"Key"), \
                            help_text=_("A name for this chunk of content"), \
                            blank=False, max_length=255)
    content = models.TextField(_(u"Content"), blank=True, default='')
    order = models.IntegerField(_(u"Order"), default=0)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['order']
        unique_together = ('key', 'content_type', 'object_id')

        verbose_name = _(u'Inline Chunk')
        verbose_name_plural = _(u'Inline Chunks')

    def __unicode__(self):
        return u"%s / %s" % (self.content_object, self.key)

    def build_content(self, request, context, obj=None):
        """Build content with builder or with default builder"""

        if not obj:
            obj = self.content_object

        for builder in CHUNK_BUILDERS:
            if builder.appropriate_key(self.key, chunk=self, obj=obj):
                return builder.render(request, self, \
                            parent=obj, context=context)
        return self.content


class ChunksModel(object):
    """Base class with additional methods for model which will use
    chunks. Usage:
        class YourCustomModel(models.Model, ChunksModel):
            ...


        # and at bottom of the file with models connect clear_cache callback
        post_save.connect(clear_chunks_cache, sender=YourCustomModel)
        pre_delete.connect(clear_chunks_cache, sender=YourCustomModel)
    """
    @property
    def chunks_cache_key(self):
        return "%s_%s_%d" % (
            CACHE_PREFIX,
            self._meta.object_name.lower(),
            self.id)

    def chunk_item_cache_key(self, key):
        return "%s_%s_%d_%s" % (
                    Chunk.ITEM_CACHE_PREFIX,
                    self._meta.object_name.lower(),
                    self.id,
                    key)

    def clear_chunks_cache(self):
        """Cleanup ChunksModel.chunks cache and cache
        for appropriate template tag"""
        logger.debug(\
            u"Clean up cache for list of chunks for %s" % unicode(self))
        cache.delete(self.chunks_cache_key)

        model_type = ContentType.objects.get_for_model(self.__class__)
        object_id = self.id

        chunks = InlineChunk.objects.filter(content_type=model_type, \
                                                object_id=object_id)
        # cleanup all cache for all available chunks of current object
        for ch in chunks:
            cache.delete(self.chunk_item_cache_key(ch.key))

    def chunks(self, request, context):
        """Return list of available chunks for current object
        as python dictionary
        """
        model_type = ContentType.objects.get_for_model(self.__class__)
        object_id = self.id

        cache_key = self.chunks_cache_key

        # read cache timeout, if==0 then chage will be disabled
        cache_timeout = 0
        if hasattr(self, 'ChunksMeta') \
            and hasattr(self.ChunksMeta, 'chunks_cache_timeout'):
            cache_timeout = getattr(self.ChunksMeta, \
                                    'chunks_cache_timeout', 0)
            if not cache_timeout:
                cache_timeout = 0

        chunks_content = cache.get(cache_key)
#        chunks_content = {} # why was this here? Doesn't make sense.
        if not chunks_content:
            chunks = InlineChunk.objects.filter(content_type=model_type, \
                                                    object_id=object_id)
            # build all chunks for this particular object
            for ch in chunks:
                chunks_content[ch.key] = ch.build_content(\
                                            request, context, obj=self)
            cache.set(cache_key, chunks_content, cache_timeout)

        return chunks_content

class CodeChunk(object):
    def __init__(self, key, wrap):
        self.key = key
        self.wrap = wrap
        
    def __str__(self):
        return codechunk(self.key, self.wrap)

def codechunk(key, wrap=False, cache_time=0, context={}):
    """
    Returns the given chunk. Use this function to place chunks in code (views, widgets, etc.)
    If you want to add it to the chunk sidebar, you need to put the current request in the context:
    { 'request': request }
    """
    from chunks.templatetags.chunks import render_chunk
    
    return render_chunk(context, key, wrap, cache_time)

# import and cache all available chunks builders
for cb in CHUNK_BUILDERS_LIST:
    package = cb[:cb.index('.')]
    cls_name = cb[cb.rindex('.') + 1:]
    module_name = cb[len(package) + 1:-len(cls_name) - 1]

    mdl = import_module(module_name, package=package)
    cls = getattr(mdl, cls_name)
    CHUNK_BUILDERS.append(cls())

# add default builder to end of list of builders
CHUNK_BUILDERS.append(ChunkBuilder())


# cleanup Chunk model cache
post_save.connect(clear_plain_chunk_cache, sender=Chunk)
pre_delete.connect(clear_plain_chunk_cache, sender=Chunk)
