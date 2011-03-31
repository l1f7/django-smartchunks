import logging

from django.core.exceptions import ImproperlyConfigured
from django import template
from django.db import models
from django.core.cache import cache


logger = logging.getLogger(__name__)

register = template.Library()

Chunk = models.get_model('chunks', 'chunk')
InlineChunk = models.get_model('chunks', 'inlinechunk')

CACHE_PREFIX = "chunk_"

CONTEXT_IMPROPERLY_CONFIGURED = lambda: ImproperlyConfigured(\
                    "Please, add `django.core.context_processors.request` \n"\
                    "to settings.CONTEXT_PROCESSORS: `request` variable "\
                    "is required by `chunks` app")


class ObjChunkNode(template.Node):
    def __init__(self, obj, key, cache_time=0):
        self.obj = template.Variable(obj)
        self.key = key
        self.cache_time = cache_time

    def render(self, context):
        try:
            obj = self.obj.resolve(context)
            cache_key = "%s_%s_%d_%s" % (
                                    CACHE_PREFIX,
                                    obj._meta.object_name.lower(),
                                    obj.id,
                                    self.key)
            content = cache.get(cache_key)
            if content is None:
                c = InlineChunk.objects.get(content_object=obj, key=self.key)
                request = context.get('request', None)
                if not request:
                    raise CONTEXT_IMPROPERLY_CONFIGURED()

                content = c.build_content(request, context)
                cache.set(cache_key, content, int(self.cache_time))

        except (Chunk.DoesNotExist, template.VariableDoesNotExist):
            content = ''
        return content


class ObjChunksListNode(template.Node):
    """Class to put dictionary with all chunks content into context
    variable"""
    def __init__(self, obj, context_name=None):
        self.obj = template.Variable(obj)
        quotes = ["'\""]
        self.context_name = None
        self.context_name_var = None
        if context_name[1] in quotes:
            if context_name[1] != context_name[-1]:
                raise template.TemplateSyntaxError(\
                "Context variable name should be quoted "\
                "with similar quote characters")
            self.context_name = context_name[1:-1]
        else:
            self.context_name_var = template.Variable(context_name)

    def render(self, context):
        context_name = ""
        if self.context_name:
            context_name = self.context_name
        if self.context_name_var:
            context_name = self.context_name_var.resolve(context)

        try:
            obj = self.obj.resolve(context)
            request = context.get('request', None)

            if not request:
                raise CONTEXT_IMPROPERLY_CONFIGURED()

            chunks = obj.chunks(request, context)

        except (Chunk.DoesNotExist, template.VariableDoesNotExist):
            chunks = {}
        context[context_name] = chunks
        return ""


class ChunkNode(template.Node):
    def __init__(self, key, cache_time=0):
        self.key = key
        self.cache_time = cache_time

    def render(self, context):
        try:
            cache_key = CACHE_PREFIX + self.key
            content = cache.get(cache_key)
            if content is None:
                c = Chunk.objects.get(key=self.key)

                request = context.get('request', None)
                if not request:
                    raise CONTEXT_IMPROPERLY_CONFIGURED()

                content = c.build_content(request, context)
                cache.set(cache_key, content, int(self.cache_time))

        except Chunk.DoesNotExist:
            content = ''
        return content


def do_get_chunk(parser, token):
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) < 2 or len(tokens) > 3:
        raise template.TemplateSyntaxError, \
            "%r tag should have either 2 or 3 arguments" % (tokens[0],)
    if len(tokens) == 2:
        tag_name, key = tokens
        cache_time = 0
    if len(tokens) == 3:
        tag_name, key, cache_time = tokens
    # Check to see if the key is properly double/single quoted
    if not (key[0] == key[-1] and key[0] in ('"', "'")):
        raise template.TemplateSyntaxError, \
            "%r tag's argument should be in quotes" % tag_name
    # Send key without quotes and caching time
    return ChunkNode(key[1:-1], cache_time)


def do_get_object_chunk(parser, token):
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) < 2 or len(tokens) > 4:
        raise template.TemplateSyntaxError, \
            "%r tag should have either 3 or 4 arguments" % (tokens[0],)
    if len(tokens) == 3:
        tag_name, obj, key = tokens
        cache_time = 0
    if len(tokens) == 4:
        tag_name, obj, key, cache_time = tokens
    # Check to see if the key is properly double/single quoted
    if not (key[0] == key[-1] and key[0] in ('"', "'")):
        raise template.TemplateSyntaxError, \
            "%r tag's argument should be in quotes" % tag_name
    # Send key without quotes and caching time
    return ObjChunkNode(obj, key[1:-1], cache_time)


def do_get_object_chunks_list(parser, token):
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) != 3:
        raise template.TemplateSyntaxError, \
            "%r tag should have only 2 arguments" % (tokens[0],)

    tag_name, obj, context_name = tokens

    # Send key without quotes and caching time
    return ObjChunksListNode(obj, context_name=context_name)

register.tag('chunk', do_get_chunk)
register.tag('object_chunk', do_get_object_chunk)
register.tag('object_chunks_list', do_get_object_chunks_list)
