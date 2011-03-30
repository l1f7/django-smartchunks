from django.utils.importlib import import_module
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from builders import ChunkBuilder


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
        unique_together = ('key', 'content_type', 'object_id')

    def __unicode__(self):
        return u"%s / %s" % (self.content_object, self.key)

    def build_content(self, request, context):
        """Build content with builder or with default builder"""
        for builder in CHUNK_BUILDERS:
            if builder.appropriate_key(self.key):
                return builder.render(request, self, \
                            parent=self.content_object, context=context)
        return self.content

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
