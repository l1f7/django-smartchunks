class ChunksMiddleware(object):
    def process_request(self, request):
        self.chunks = {}
        
    def process_template_response(self, request, response):
        
        return response
        