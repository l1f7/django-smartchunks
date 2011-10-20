class ChunksMiddleware(object):
    """
    Monitors all chunks that are created on this request
    and prints them out in the end.
    """
    def process_request(self, request):
        request.generated_chunks = []
        
    def process_template_response(self, request, response):
        gchunks = []
        for chunk in request.generated_chunks:
            gchunks.append({'id': chunk.id,
                            'key': chunk.key,
                            'content': chunk.content,
                            'description': chunk.description})
            
        response.context_data['generated_chunks'] = gchunks
        return response
        