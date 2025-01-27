import requests
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def get_ultimate_resolution_url(original_url):
    """Transform URL to get highest possible resolution"""
    parsed = urlparse(original_url)
    
    # 1. Maximize resolution in path (e.g., _1920x1080 -> _UHD)
    new_path = re.sub(r"_\d+x\d+", "_UHD", parsed.path)
    
    # 2. Force maximum resolution parameters
    query = parse_qs(parsed.query)
    query.update({
        'w': ['3840'],  # Base 4K width
        'h': ['2160'],  # Base 4K height
        'rs': ['1'],    # Enable high-quality scaling
        'c': ['4']      # Quality boost parameter
    })
    
    # 3. Special handling for 8K content
    if "_8K" in new_path:
        query.update({'w': ['7680'], 'h': ['4320']})
    
    return urlunparse(parsed._replace(
        path=new_path,
        query=urlencode(query, doseq=True)
    ))

def download_bing_wallpapers(output_dir="bing_wallpapers", days=20):
    api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&n={days}&mkt=en-US"
    
    try:
        response = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()
        
        os.makedirs(output_dir, exist_ok=True)
        success = 0
        
        for img in data['images']:
            base_url = f"https://www.bing.com{img['url']}"
            ultimate_url = get_ultimate_resolution_url(base_url)
            
            # Generate filename
            date = datetime.strptime(img['enddate'], "%Y%m%d").strftime("%Y-%m-%d")
            title = re.sub(r'\W+', '_', img['copyright'].split(' (')[0])
            filename = f"{date}_{title}.jpg"
            
            try:
                # Download with 30s timeout and size validation
                res = requests.get(ultimate_url, stream=True, timeout=30)
                if res.status_code == 200 and int(res.headers.get('Content-Length', 0)) > 100000:
                    with open(os.path.join(output_dir, filename), 'wb') as f:
                        for chunk in res.iter_content(8192):
                            f.write(chunk)
                    success += 1
                    print(f"✓ Downloaded {filename} ({(int(res.headers['Content-Length'])/1024/1024):.1f} MB)")
                else:
                    print(f"✗ Skipped {filename} (small file)")
            except Exception as e:
                print(f"⚠ Error downloading {filename}: {str(e)}")

        print(f"\nSuccess: {success}/{len(data['images'])} wallpapers saved to {output_dir}/")

    except Exception as e:
        print(f"🚨 Critical error: {str(e)}")

if __name__ == "__main__":
    download_bing_wallpapers(days=20)  # Max historical access