from django.utils.importlib import import_module
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.cache import cache

from builders import ChunkBuilder


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
    desc = models.CharField(max_length=255)
    key = models.CharField(\
            help_text="A unique name for this chunk of content", \
            blank=False, max_length=255, unique=True)
    content = models.TextField(blank=True)

    def build_content(self, request, context):
        """Build content with builder or with default builder"""
        for builder in CHUNK_BUILDERS:
            if builder.appropriate_key(self.key):
                return builder.render(request, self, \
                            parent=None, context=context)
        return self.content

    def __unicode__(self):
        return u"%s" % (self.key,)


class InlineChunk(models.Model):
    desc = models.CharField(max_length=255)
    key = models.CharField(help_text="A name for this chunk of content", \
                            blank=False, max_length=255)
    content = models.TextField(blank=True, default='')
    order = models.IntegerField(default=0)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['order']
        unique_together = ('key', 'content_type', 'object_id')

    def __unicode__(self):
        return u"%s / %s" % (self.content_object, self.key)

    def build_content(self, request, context, obj=None):
        """Build content with builder or with default builder"""

        if not obj:
            obj = self.content_object

        for builder in CHUNK_BUILDERS:
            if builder.appropriate_key(self.key):
                return builder.render(request, self, \
                            parent=obj, context=context)
        return self.content


class ChunksModel(object):
    @property
    def _chunks_cache_key(self):
        return "%s_%s_%d" % (
            CACHE_PREFIX,
            self._meta.object_name.lower(),
            self.id)

    chunks_cache_key = _chunks_cache_key

    def clear_chunks_cache(self):
        cache.delete(self.chunks_cache_key)

    def chunks(self, request, context):
        model_type = ContentType.objects.get_for_model(self.__class__)
        object_id = self.id

        cache_key = self.chunks_cache_key

        # read cache timeout, if==0 then chage will be disabled
        cache_timeout = 0
        if hasattr(self._meta, 'chunks_cache_timeout'):
            cache_timeout = getattr(self._meta, 'chunks_cache_timeout', 0)
            if not cache_timeout:
                cache_timeout = 0

        content = cache.get(cache_key)
        chunks_content = {}
        if not content:
            chunks = InlineChunk.objects.filter(content_type=model_type, \
                                                    object_id=object_id)
            # build all chunks for this particular object
            for ch in chunks:
                chunks_content[ch.key] = ch.build_content(\
                                            request, context, obj=self)
            cache.set(cache_key, chunks_content, cache_timeout)
        return chunks_content


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
