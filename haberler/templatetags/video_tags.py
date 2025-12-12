from django import template
import re
from haberler.models import get_youtube_embed

register = template.Library()

@register.filter
def youtube_gom(value):
    """
    Yazı içindeki [video=LINK] etiketlerini bulur ve
    YouTube (Normal + Shorts) iframe koduna çevirir.
    """
    if not value:
        return ""

    # [video=...] kalıbını yakalar
    pattern = re.compile(r'\[video=(.*?)\]')

    def cevirici(match):
        embed_url = get_youtube_embed(match.group(1).strip())
        if not embed_url:
            return ""
        return f'''
        <div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; margin: 30px 0; border-radius: 8px; border: 1px solid #eee; background-color: #000;">
            <iframe 
                src="{embed_url}" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                frameborder="0" loading="lazy"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerpolicy="strict-origin-when-cross-origin"
                allowfullscreen>
            </iframe>
        </div>
        '''

    return pattern.sub(cevirici, value)
