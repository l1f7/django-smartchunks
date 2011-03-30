

class ChunkBuilder(object):
    chunk_names = None

    def appropriate_key(self, name):
        """This method may be overrided by builder to work with
        custom names of chunks.
        if self.chunk_names set to None then builder will be default
        for all InlineChunks.
        """
        if self.chunk_names == None or name in self.chunk_names:
            return True
        return False

    def render(self, request, chunk, parent=None, context={}):
        return chunk.content
