class ChunksMiddleware(object):
    """
    Monitors all chunks that are created on this request
    and prints them out in the end.
    """
    def process_request(self, request):
        self.chunks = {}
        
    def process_template_response(self, request, response):
        
        return response
        