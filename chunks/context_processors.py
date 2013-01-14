from chunks.models import Chunk


def chunks(request):
    chunks_dict = {}
    for c in Chunk.objects.all():
        chunks_dict[c.key] = c.content
    return {"CHUNKS": chunks_dict}
