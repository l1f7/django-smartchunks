from django.contrib import admin
from models import Chunk, InlineChunk


class ChunkAdmin(admin.ModelAdmin):
    list_display = ('description', 'key',)
    search_fields = ('description', 'key', 'content')


class InlineChunkAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'key')
    search_fields = ('description', 'key', 'content')


admin.site.register(Chunk, ChunkAdmin)
admin.site.register(InlineChunk, InlineChunkAdmin)
