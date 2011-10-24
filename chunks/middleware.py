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
                gchunks.append({'id': chunk.id,
                                'key': chunk.key,
                                'content': chunk.content,
                                'description': chunk.description})
                
            out = render_to_string("chunks/chunks_sidebar.html", {'generated_chunks': gchunks})
            response.content = response.content.replace('</body>', '%s</body>' % (out))
        except AttributeError:
            pass
        return response
        