from django.conf import settings
from django.template.loader import render_to_string

class ChunksMiddleware(object):
    """
    Monitors all chunks that are created on this request
    and prints them out in the end.
    """
    def process_request(self, request):
        if getattr(settings, 'CHUNKS_WRAP', False):
            request.generated_chunks = []
        
    def process_response(self, request, response):
        try:
            gchunks = []
            for chunk in request.generated_chunks:
                if 'id' in chunk.__dict__:
                    gchunks.append({'id': chunk.id,
                                'key': chunk.key,
                                'content': chunk.content,
                                'description': chunk.description,
                                'wrapped': chunk.wrapped,
                                'url': '/admin/chunks/chunk/',
                                })
                else:
                    # new chunk
                    gchunks.append({'key': chunk['key'],
                                    'wrapped': chunk['wrapped'],
                                    'url': '/admin/chunks/chunk/add',
                                    })
            response.content = response.content.replace('</body>', '%s</body>' % 
                                                        (render_to_string("chunks/chunks_sidebar.html", 
                                                                          {'generated_chunks': gchunks})))            
        except AttributeError:
            pass
        return response
        