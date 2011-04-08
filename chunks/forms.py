from django import forms
from django.utils.translation import ugettext_lazy as _

from models import InlineChunk, CHUNK_BUILDERS


CHUNK_BUILDERS_CHOICES = [('', '')]

for bldr in CHUNK_BUILDERS[:-1]:
    ident = getattr(bldr, u'ident', unicode(bldr.__class__))
    title = getattr(bldr, u'title', unicode(bldr.__class__))
    CHUNK_BUILDERS_CHOICES.append((ident, title))


class InlineChunkForm(forms.ModelForm):
    chunk_type = forms.ChoiceField(label=_(u"Chunk Type"), \
                                   choices=CHUNK_BUILDERS_CHOICES, \
                                   required=False, \
                                   widget=forms.Select(\
                                        attrs={'class': 'chunks-type'}))

    class Meta:
        model = InlineChunk

    class Media:
        js = (
        'js/chunks-admin.js',
        )
