class ChunksMiddleware(object):
    """
    Monitors all chunks that are created on this request
    and prints them out in the end.
    """
    def process_request(self, request):
        request.generated_chunks = {}
        
    def process_template_response(self, request, response):
        response.context_data['generated_chunks'] = request.generated_chunks
        return response
        