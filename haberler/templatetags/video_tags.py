from django import template
import re

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
        url = match.group(1).strip()
        video_id = None
        
        # 1. SHORTS Linki Kontrolü
        if "shorts/" in url:
            try:
                video_id = url.split("shorts/")[1].split("?")[0]
            except: pass
            
        # 2. Normal Link (watch?v=) Kontrolü
        elif "youtube.com" in url and "v=" in url:
            try:
                video_id = url.split("v=")[1].split("&")[0]
            except: pass
            
        # 3. Kısaltılmış Link (youtu.be) Kontrolü
        elif "youtu.be" in url:
            try:
                video_id = url.split("/")[-1].split("?")[0]
            except: pass
            
        if video_id:
            return f'''
            <div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; margin: 30px 0; border-radius: 8px; border: 1px solid #eee; background-color: #000;">
                <iframe 
                    src="https://www.youtube.com/embed/{video_id}" 
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
            '''
        return "" 

    return pattern.sub(cevirici, value)