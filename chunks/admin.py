from django.contrib import admin
from models import Chunk, InlineChunk


class ChunkAdmin(admin.ModelAdmin):
    list_display = ('desc', 'key',)
    search_fields = ('desc', 'key', 'content')


class InlineChunkAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'key')
    search_fields = ('desc', 'key', 'content')


admin.site.register(Chunk, ChunkAdmin)
admin.site.register(InlineChunk, InlineChunkAdmin)
