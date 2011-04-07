

class ChunkBuilder(object):
    chunk_names = None
    ident = u'base'
    title = u'Basic chunks builder'
    
    @property
    def id(self):
        return u'chunk=%s' % self.ident

    def appropriate_key(self, name, chunk=None, obj=None):
        """This method may be overrided by builder to work with
        custom names of chunks.
        if self.chunk_names set to None then builder will be default
        for all InlineChunks.
        """
        if self.chunk_names == None or name in self.chunk_names:
            return True
        return False

    def render(self, request, chunk, parent=None, context={}):
        """This method should be overriden by custom builder to generate or
        process content"""
        return chunk.content
