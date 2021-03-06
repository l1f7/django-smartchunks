import logging

from django.contrib.contenttypes.models import ContentType
from django import template
from django.db import models
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.template.defaultfilters import stringfilter

logger = logging.getLogger(__name__)

register = template.Library()

Chunk = models.get_model('chunks', 'chunk')
InlineChunk = models.get_model('chunks', 'inlinechunk')

CACHE_PREFIX = Chunk.ITEM_CACHE_PREFIX

CONTEXT_IMPROPERLY_CONFIGURED = lambda: ImproperlyConfigured(\
                    "Please, add `django.core.context_processors.request` \n"\
                    "to settings.CONTEXT_PROCESSORS: `request` variable "\
                    "is required by `chunks` app")


class ObjChunkNode(template.Node):
    def __init__(self, obj, key, cache_time=0, default_chunk=None, wrap='True'):
        self.obj = template.Variable(obj)
        self.key = key
        self.cache_time = cache_time
        self.default_chunk = default_chunk
        self.wrap = wrap

    def render(self, context):
        """
        TODO wrapping
        """
        try:
            obj = self.obj.resolve(context)
            cache_key = obj.chunk_item_cache_key(self.key)
            content = cache.get(cache_key)
            if content is None:
                try:
                    model_type = ContentType.objects\
                                    .get_for_model(obj.__class__)
                    object_id = obj.id

                    c = InlineChunk.objects.get(\
                            content_type=model_type, object_id=object_id, \
                            key=self.key)
                except InlineChunk.DoesNotExist:
                    if self.default_chunk:
                        try:
                            c = Chunk.objects.get(key=self.default_chunk)
                        except Chunk.DoesNotExist:
                            return ''
                    else:
                        return ''

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
    def __init__(self, key, cache_time=0, wrap='True'):
        self.key = key
        self.cache_time = cache_time
        self.wrap = wrap

    def render(self, context):
        return render_chunk(context, self.key, self.wrap, self.cache_time)


def do_get_chunk(parser, token):
    """
    Tokens:
    wrap cache_time
    """

    try:
        cache_time = settings.CHUNKS_CACHE_TIME
    except AttributeError:
        cache_time = 300

    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) < 2 or len(tokens) > 4:
        raise template.TemplateSyntaxError(\
            "%r tag should have either 2, 3 or 4 arguments" % (tokens[0],))
    if len(tokens) == 2:
        tag_name, key = tokens
        wrap = 'True'
    if len(tokens) == 3:
        tag_name, key, wrap = tokens
    if len(tokens) == 4:
        tag_name, key, wrap, cache_time = tokens
    # Check to see if the key is properly double/single quoted
    if not (key[0] == key[-1] and key[0] in ('"', "'")):
        raise template.TemplateSyntaxError( \
            "%r tag's argument should be in quotes" % tag_name)
    # Send key without quotes and caching time

    return ChunkNode(key[1:-1], cache_time=cache_time, wrap=wrap)


def do_get_object_chunk(parser, token):
    """
    Tokens:
    wrap cache_time default_chunk
    """
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    default_chunk = None
    if len(tokens) < 2 or len(tokens) > 6:
        raise template.TemplateSyntaxError, \
            "%r tag should have either 3 or 5 arguments" % (tokens[0],)
    if len(tokens) == 3:
        tag_name, obj, key = tokens
        cache_time = 0
        wrap = False
    if len(tokens) == 4:
        tag_name, obj, key, wrap = tokens
        cache_time = 0
    if len(tokens) == 5:
        tag_name, obj, key, wrap, cache_time = tokens
    if len(tokens) == 6:
        tag_name, obj, key, wrap, cache_time, default_chunk = tokens
        if not (default_chunk[0] == default_chunk[-1] \
                    and default_chunk[0] in ("'", '"')):
            raise template.TemplateSyntaxError("Default chunk argument "\
                "should be in quotes")
        default_chunk = default_chunk[1:-1]
    # Check to see if the key is properly double/single quoted
    if not (key[0] == key[-1] and key[0] in ('"', "'")):
        raise template.TemplateSyntaxError(\
            "%r tag's argument should be in quotes" % tag_name)
    # Send key without quotes and caching time
    return ObjChunkNode(obj, key[1:-1], cache_time, \
                                default_chunk=default_chunk,
                                wrap=wrap)


def do_get_object_chunks_list(parser, token):
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) != 3:
        raise template.TemplateSyntaxError, \
            "%r tag should have only 2 arguments" % (tokens[0],)

    tag_name, obj, context_name = tokens

    # Send key without quotes and caching time
    return ObjChunksListNode(obj, context_name=context_name)


class CodeChunk(object):
    """
    The static variable codechunks holds all the codechunks!
    """
    codechunks = []

    def __init__(self, key, wrap=True):
        self.key = key
        self.wrap = wrap
        CodeChunk.codechunks.append(self)


@stringfilter
def do_filter_chunk(value, wrap):
    """
    Chunk filter - for chunks that need to be inside other template tags.
    request should be explicitly passed in the filter!
    CHUNK_WRAP mode.
    """

    CodeChunk(value, wrap)
    return render_chunk({}, value, wrap, 0)


def render_chunk(context, key, wrap='True', cache_time=100):
    """
    Renders the chunk.
    wrap = True will wrap the chunk in <chunk> tags.
    """
    try:
        request = context.get('request', None)
        if not request:
#            raise CONTEXT_IMPROPERLY_CONFIGURED()
            pass  # TODO can it be like this?

        cache_key = CACHE_PREFIX + key
        content = cache.get(cache_key)
        if content is None:
            c = Chunk.objects.get(key=key)

            content = {'id': c.id,
                        'key': c.key,
                        'content': c.build_content(request, context),
                        'description': c.description,
                      }
            cache.set(cache_key, content, int(cache_time))

    except Chunk.DoesNotExist:
        c = Chunk(key=key,
                  content=key,
                  description='')

        c.save()

        content = {'id': c.id,
                   'key': c.key,
                   'content': c.build_content(request, context),
                   'description': c.description,
                  }

    # if CHUNKS_WRAP is True,
    # wrap the chunk into a <chunk> element with an attribute that
    # contains it's ID
    if getattr(settings, 'CHUNKS_WRAP', False) and (wrap == 'True' or wrap == True or wrap == 1):
        content['original'] = content['content']
        content['content'] = '<chunk cid="%d" class="newchunk">%s</chunk><div class="chunkmenu" id="chm_%d"><a class="button" href="%s%d">edit</a></div>' \
                                % (content['id'],
                                 content['content'],
                                 content['id'],
                                 '/admin/chunks/chunk/',
                                 content['id'])
        content['wrapped'] = True
    else:
        content['original'] = content['content']
        content['wrapped'] = False

    if request and 'generated_chunks' in request.__dict__:
        if content not in request.generated_chunks:
            request.generated_chunks.append(content)

    return content['content']

register.filter('chunk', do_filter_chunk)
register.tag('chunk', do_get_chunk)
register.tag('object_chunk', do_get_object_chunk)
register.tag('object_chunks_list', do_get_object_chunks_list)


@register.simple_tag
def chunk_lookup(the_dict, key):
    """
    If the chunks are loaded by the context processor, they're
    already available in the dict ``CHUNKS`` but if they have
    a hypen in the name, they can't be pulled out.

    This will result in far fewer queries if you use chunks a lot.

    {% chunk_lookup CHUNKS "phone-number" %}

    Try to fetch from the dict, and if it's not found return an
    empty string.
    """
    return the_dict.get(key, '')


@register.filter
def keyvalue(dict, key):
    return dict[key]
