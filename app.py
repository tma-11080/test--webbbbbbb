import streamlit as st
import yt_dlp
import requests
import time
import os
import re
import urllib.parse
from io import BytesIO
from bs4 import BeautifulSoup

# ==========================================
# 1. SYSTEM CONFIG & UI THEME
# ==========================================
SYSTEM_VERSION = "5.0.0-NEON-ULTIMATE"

st.set_page_config(page_title="NEON MULTI-DOWNLOADER", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; font-family: 'Courier New', monospace; }
    .neon-text {
        font-size: clamp(30px, 5vw, 50px); font-weight: 900; color: #fff;
        text-align: center; text-transform: uppercase;
        text-shadow: 0 0 10px #0000ff, 0 0 20px #8a2be2;
        margin-bottom: 20px; border-bottom: 2px solid #8a2be2; padding-bottom: 10px;
    }
    .stTextArea textarea {
        background-color: #0a0a0a !important; color: #00f2ff !important;
        border: 2px solid #8a2be2 !important; border-radius: 8px;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #0000ff, #8a2be2);
        color: white; border: none; font-weight: bold; width: 100%;
        box-shadow: 0 0 15px #0000ff; transition: 0.3s;
    }
    div.stButton > button:hover { box-shadow: 0 0 30px #8a2be2; transform: scale(1.02); }
    .batch-card {
        border: 1px solid #00f2ff; padding: 20px; border-radius: 10px;
        background: rgba(10, 10, 30, 0.9); margin-bottom: 20px;
        border-left: 8px solid #8a2be2;
    }
    .status-tag { font-size: 0.8rem; padding: 2px 8px; border-radius: 4px; background: #333; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CORE LOGIC ENGINE
# ==========================================

class NeonDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_info(self, url):
        """URLのタイプを判別し、メタデータとDL用URLを返す"""
        # 1. YouTube Community Post (Images)
        if "youtube.com/post/" in url or "/community" in url:
            return self._handle_yt_community(url)
        
        # 2. Standard Video (YouTube, X, etc.) via yt-dlp
        return self._handle_video_stream(url)

    def _handle_yt_community(self, url):
        try:
            res = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            meta_img = soup.find("meta", property="og:image")
            if meta_img:
                img_url = re.sub(r'=s\d+.*', '', meta_img["content"])
                return {"type": "image", "preview": img_url, "dl_url": img_url, "title": "YT Community Image"}
        except: pass
        return None

    def _handle_video_stream(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            # X(Twitter)などのクッキーが必要なサイトへの対策
            'http_headers': self.headers
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "type": "video",
                    "preview": info.get('thumbnail'),
                    "dl_url": info.get('url'), # 直リンク
                    "title": info.get('title', 'Untitled Video'),
                    "is_direct": url.split('?')[0].endswith('.mp4') or "po-kaki-to" in url
                }
        except Exception as e:
            # yt-dlp失敗時、.mp4直リンクなら強引に取得を試みる
            if url.split('?')[0].endswith('.mp4'):
                return {"type": "video", "preview": None, "dl_url": url, "title": "Direct MP4 File"}
            return None

# ==========================================
# 3. MAIN UI
# ==========================================

def main():
    st.markdown('<div class="neon-text">NEON MULTI SYSTEM</div>', unsafe_allow_html=True)
    
    downloader = NeonDownloader()

    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        raw_urls = st.text_area("ENTER URLS (YouTube, X, .mp4, po-kaki-to, etc.)", height=120, placeholder="1行に1つのURLを入力...")
        process_btn = st.button("⚡ ANALYZE TARGETS")

        if raw_urls and process_btn:
            urls = [u.strip() for u in raw_urls.split('\n') if u.strip()]
            
            for i, url in enumerate(urls):
                with st.spinner(f'Analyzing: {url[:50]}...'):
                    data = downloader.get_info(url)
                
                # --- CARD UI START ---
                st.markdown(f'<div class="batch-card">', unsafe_allow_html=True)
                
                if data:
                    c1, c2 = st.columns([4, 6])
                    
                    with c1:
                        # サムネイル / プレビュー表示
                        if data["preview"]:
                            st.image(data["preview"], use_container_width=True, caption="PREVIEW / THUMBNAIL")
                        else:
                            st.info("No Preview Available")
                    
                    with c2:
                        st.markdown(f"### {data['title'][:50]}...")
                        st.caption(f"SOURCE: {url[:60]}...")
                        
                        # 種類別の表示
                        if data["type"] == "video":
                            st.video(url) # Streamlit標準プレイヤーで再生
                        
                        # ダウンロード処理
                        try:
                            # ファイル名生成
                            ext = "jpg" if data["type"] == "image" else "mp4"
                            fname = f"neon_{int(time.time())}_{i}.{ext}"
                            
                            # データの取得（ここがDLの肝）
                            btn_label = "💾 DOWNLOAD VIDEO" if data["type"] == "video" else "💾 DOWNLOAD IMAGE"
                            
                            # po-kaki-to等のリファラが必要なサイトへの対応を含めたDL
                            res = requests.get(data["dl_url"], headers=downloader.headers, timeout=20)
                            
                            st.download_button(
                                label=btn_label,
                                data=res.content,
                                file_name=fname,
                                mime=f"video/{ext}" if ext=="mp4" else "image/jpeg",
                                key=f"dl_{i}"
                            )
                        except:
                            st.error("Failed to buffer file for download.")
                else:
                    st.error(f"Unsupported URL or Access Denied: {url}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                # --- CARD UI END ---

    st.markdown("<br><center>NEON BATCH CORE v5.0 | High-Speed Injection</center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
