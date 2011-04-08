

def clear_chunks_cache(sender, instance, *args, **kwargs):
    """Cleanup chunks cache if necessary.
    Connect this listener to appropriate model which inherited from
    `chunks.models.ChunksModel` class
    """
    instance.clear_chunks_cache()


def clear_plain_chunk_cache(sender, instance, *args, **kwargs):
    """Cleanup simple chunk cache when chunk is updated"""
    instance.clear_cache()
