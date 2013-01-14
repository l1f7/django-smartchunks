from django.conf import settings
from django.template.loader import render_to_string
from chunks.models import Chunk
from chunks.templatetags.chunks import CodeChunk


class ChunksMiddleware(object):
    """
    Monitors all chunks that are created on this request
    and prints them out in the end.
    """
    def process_request(self, request):
        if getattr(settings, 'CHUNKS_WRAP', False):
            request.generated_chunks = []

    def process_response(self, request, response):
        if not getattr(settings, 'CHUNKS_WRAP', False):
            return response

        try:
            gchunks = []
            for chunk in request.generated_chunks:
                if 'id' in chunk.keys():
#                    gchunks.append({'id': chunk.id,
#                                'key': chunk.key,
#                                'content': chunk.content,
#                                'description': chunk.description,
#                                'wrapped': chunk.wrapped,
#                                'url': '/admin/chunks/chunk/',
#                                })
                    chunk['url'] = '/admin/chunks/chunk'
                    gchunks.append(chunk)
                else:
                    # new chunk
#                    gchunks.append({'key': chunk['key'],
#                                    'wrapped': chunk['wrapped'],
#                                    'url': '/admin/chunks/chunk/add',
#                                    })
                    pass

            # codechunks
            for chunk in CodeChunk.codechunks:
                # TODO caching!
                ch = Chunk.objects.get(key=chunk.key)
                if ch:
                    gchunks.append({'id': ch.id,
                                    'key': ch.key,
                                    'content': ch.content,
                                    'description': ch.description,
                                    'wrapped': chunk.wrap,
                                    'url': '/admin/chunks/chunk/',
                                    })

            table = render_to_string("chunks/chunks_sidebar.html", {'generated_chunks': gchunks})
            response.content = response.content.replace('</body>', '%s</body>' % (table.encode('utf-8')))

            CodeChunk.codechunks = []
        except AttributeError:
            pass
        except UnicodeDecodeError as e:
            print e
            print table
        return response
