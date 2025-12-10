import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
import json

# --- Sayfa Yapılandırması ---
st.set_page_config(layout="wide", page_title="Artvin Turizm Haritası")

# --- Veri Seti (Turistik Noktalar) ---
# Buraya kendi verilerini ekleyebilirsin. Örnek olarak doldurdum.
data = [
    {"ad": "Mençuna Şelalesi", "ilce": "Arhavi", "lat": 41.3325, "lon": 41.3856, "tip": "Doğa"},
    {"ad": "Artvin Kalesi", "ilce": "Merkez", "lat": 41.1812, "lon": 41.8208, "tip": "Tarih"},
    {"ad": "Atatepe", "ilce": "Merkez", "lat": 41.1715, "lon": 41.8350, "tip": "Manzara"}, # Koordinatlar örnektir
    {"ad": "Karagöl", "ilce": "Borçka", "lat": 41.3892, "lon": 41.8544, "tip": "Doğa"},
    {"ad": "Maral Şelalesi", "ilce": "Borçka", "lat": 41.4722, "lon": 41.9761, "tip": "Doğa"}
]
df = pd.DataFrame(data)

# --- İlçe Koordinatları (Zoom için merkez noktalar) ---
ilce_merkezleri = {
    "Merkez": [41.1828, 41.8183],
    "Arhavi": [41.3478, 41.3066],
    "Borçka": [41.3606, 41.6781],
    "Hopa": [41.4061, 41.4225],
    "Şavşat": [41.2444, 42.4222],
    "Yusufeli": [40.8222, 41.5472],
    "Murgul": [41.2650, 41.5606],
    "Ardanuç": [41.1250, 42.0472],
    "Kemalpaşa": [41.4800, 41.5100]
}

# --- Kenar Çubuğu (Sidebar) Filtreleme ---
st.sidebar.title("🌲 Artvin Keşif Rehberi")

# Şık Dropdown Menü
ilceler_listesi = ["Tümü"] + sorted(list(df['ilce'].unique()))
secilen_ilce = st.sidebar.selectbox(
    "📍 Bölge Seçiniz",
    options=ilceler_listesi,
    index=0  # Varsayılan olarak "Tümü" seçili
)

# Filtreleme Mantığı
if secilen_ilce == "Tümü":
    harita_merkezi = [41.1828, 41.8183] # Artvin Genel Merkez
    zoom_level = 9
    gosterilecek_veri = df
else:
    harita_merkezi = ilce_merkezleri.get(secilen_ilce, [41.1828, 41.8183])
    zoom_level = 11 # İlçeye yaklaştık
    gosterilecek_veri = df[df['ilce'] == secilen_ilce]

# --- Harita Oluşturma ---
# tiles='Esri.WorldImagery' -> Uydu Görüntüsü sağlar
m = folium.Map(location=harita_merkezi, zoom_start=zoom_level, tiles='Esri.WorldImagery')

# --- Artvin Sınırını Ekleme (GeoJSON) ---
@st.cache_data
def get_geojson():
    # Türkiye İlleri GeoJSON verisi (GitHub raw url)
    url = "https://raw.githubusercontent.com/fatiherikli/turkey-geojson-cities/master/cities.json"
    r = requests.get(url)
    return r.json()

try:
    geo_data = get_geojson()
    # Sadece Artvin'i filtrele (Plaka 08 veya isimle)
    artvin_feature = [feature for feature in geo_data['features'] if feature['properties']['name'] == 'Artvin']
    
    if artvin_feature:
        artvin_geojson = {
            "type": "FeatureCollection",
            "features": artvin_feature
        }
        
        folium.GeoJson(
            artvin_geojson,
            name="Artvin Sınırı",
            style_function=lambda x: {
                'fillColor': '#00000000', # İçi şeffaf
                'color': '#ffb703',       # Sınır rengi (Sarı tonu)
                'weight': 3,              # Çizgi kalınlığı
                'dashArray': '5, 5'       # Kesik çizgi efekti
            }
        ).add_to(m)
except Exception as e:
    st.error(f"Sınır verisi yüklenirken hata oluştu: {e}")

# --- Noktaları Haritaya Ekleme ---
for index, row in gosterilecek_veri.iterrows():
    # CircleMarker kullanarak hepsinin tam daire olmasını garantiliyoruz
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=8,
        popup=f"<b>{row['ad']}</b><br>{row['ilce']}",
        tooltip=row['ad'],
        color="white",      # Çerçeve rengi
        fill=True,
        fill_color="#d00000", # İç renk (Kırmızı)
        fill_opacity=0.9
    ).add_to(m)

# --- Arayüz Düzeni (Harita ve Sağ Panel) ---
col1, col2 = st.columns([3, 1]) # Harita geniş, panel dar

with col1:
    st_folium(m, width="100%", height=600)

with col2:
    st.subheader(f"{secilen_ilce} Noktaları")
    
    # Listeyi gösterirken "Oval" sorununu çözmek için CSS stil
    # Görselleri kare kutuya zorlar ve yuvarlar
    st.markdown("""
    <style>
    .round-img {
        width: 80px;
        height: 80px;
        border-radius: 50%; /* Tam daire yapar */
        object-fit: cover; /* Resmi sıkıştırmaz, kırparak doldurur */
        margin-bottom: 10px;
        border: 2px solid #ddd;
    }
    .location-card {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    for index, row in gosterilecek_veri.iterrows():
        # Örnek resim placeholder (gerçek url'lerini buraya koymalısın)
        img_url = "https://via.placeholder.com/150" 
        
        st.markdown(f"""
        <div class="location-card">
            <img src="{img_url}" class="round-img">
            <div style="font-weight: bold; margin-top:5px;">{row['ad']}</div>
            <div style="color: grey; font-size: 0.9em;">{row['ilce']}</div>
        </div>
        """, unsafe_allow_html=True)