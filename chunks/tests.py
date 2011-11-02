from django.test.testcases import TestCase
from chunks.models import Chunk, codechunk
from django.template.base import Template
from django.template.context import Context
from django.conf import settings

class ChunkTagTestCase(TestCase):
    """
    Tests the template tags
    """
    
#    fixtures = ["chunks_initial_data.json"]
    
    def setUp(self):
        self.chunk1 = Chunk(key='testchunk1',
                            content='I LIKE PIE',
                            description='')
        self.chunk1.save()
        # on production, CHUNKS_WRAP is False
        setattr(settings, 'CHUNKS_WRAP', False)
    
    def test_chunk(self):
        # chunk is rendered
        rendered = render_template('{% load chunks %}{% chunk "testchunk1" %}')
        self.assertEqual(rendered, self.chunk1.content)
        
        # chunk is created and rendered
        rendered = render_template('{% load chunks %}{% chunk "testchunk_not_exists" %}')
        self.assertEqual(rendered, 'testchunk_not_exists')
        self.assertEqual(len(Chunk.objects.all()), 2)
     
    def test_code_chunk(self):
        rendered = codechunk('testchunk1')
        self.assertEqual(rendered, self.chunk1.content)

        rendered = codechunk('testchunk_not_exists_2')
        self.assertEqual(rendered, 'testchunk_not_exists_2')
        self.assertEqual(len(Chunk.objects.all()), 2)
        
    def test_chunk_filter(self):
        # can't test this with a request, but the filter should look like:
        # "xxx"|chunk:request
        # it can't be wrapped yet...
        rendered = render_template('{% load chunks %}{{ "testchunk1"|chunk:0 }}')
        self.assertEqual(rendered, self.chunk1.content)
                        
def render_template(content):
    t = Template(content)
    return t.render(Context({}))
    