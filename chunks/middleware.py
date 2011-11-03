from django.conf import settings
from django.template.loader import render_to_string
from chunks.models import CodeChunk, Chunk

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
                    
            # codechunks
            for chunk in CodeChunk.codechunks:
                ch = Chunk.objects.get(key=chunk.key)
                if ch:
                    gchunks.append({'id': ch.id,
                                    'key': ch.key,
                                    'content': ch.content,
                                    'description': ch.description,
                                    'wrapped': chunk.wrap,
                                    'url': '/admin/chunks/chunk/',
                                    })
                
            response.content = response.content.replace('</body>', '%s</body>' % 
                                                        (render_to_string("chunks/chunks_sidebar.html", 
                                                                          {'generated_chunks': gchunks})))            
        except AttributeError:
            pass
        except UnicodeDecodeError as e:
            print e
        return response
        