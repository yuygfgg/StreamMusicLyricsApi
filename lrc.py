from flask import Flask, request, Response
import requests
import re

app = Flask(__name__)

def search_song(keyword):
    api_url = f"https://music.163.com/api/search/get?s={keyword}&type=1&limit=50"
    response = requests.get(api_url)
    if response.status_code != 200:
        return None
    return response.json().get('result')

def download_lyrics(song_id):
    url = "https://music.163.com/api/song/lyric"
    params = {"tv": "-1", "lv": "-1", "kv": "-1", "id": song_id}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None, None
    data = response.json()
    lrc = data.get('lrc', {}).get('lyric', '')
    tlyric = data.get('tlyric', {}).get('lyric', '')
    return lrc, tlyric

def parse_lyrics(lyrics):
    lyrics_dict = {}
    pattern = re.compile(r'(\[\d{2}:\d{2}\.\d{2,3}\])(.*)')
    for line in lyrics.split('\n'):
        match = pattern.match(line)
        if match:
            time_stamp, lyric = match.groups()
            lyrics_dict[time_stamp] = lyric
    return lyrics_dict

def merge_lyrics(lrc_dict, tlyric_dict):
    merged_lyrics = []
    all_time_stamps = sorted(set(lrc_dict.keys()).union(tlyric_dict.keys()))
    for time_stamp in all_time_stamps:
        original_line = lrc_dict.get(time_stamp, '')
        translated_line = tlyric_dict.get(time_stamp, '')
        merged_lyrics.append(f"{time_stamp} {original_line}")
        if translated_line:
            merged_lyrics.append(f"{time_stamp} {translated_line}")
    return '\n'.join(merged_lyrics)

def attempt_to_download_lyrics_from_songs(songs):
    for song in songs:
        lyrics_content, trans_lyrics_content = download_lyrics(song['id'])
        if lyrics_content:
            return lyrics_content, trans_lyrics_content
    return None, None

def get_aligned_lyrics(title, artist, duration):
    keyword = f"{artist} - {title}" if duration >= 600 else title
    search_result = search_song(keyword)
    
    if not search_result:
        return None
    
    songs = search_result.get('songs', [])
    if duration < 600:
        songs = [song for song in songs if abs(song['duration'] / 1000 - duration) <= 3]
    
    lyrics_content, trans_lyrics_content = attempt_to_download_lyrics_from_songs(songs)
    
    if lyrics_content:
        lrc_dict = parse_lyrics(lyrics_content)
        tlyric_dict = parse_lyrics(trans_lyrics_content if trans_lyrics_content else '')
        return merge_lyrics(lrc_dict, tlyric_dict)
    else:
        return None

@app.route('/lyrics', methods=['GET'])
def lyrics():
    title = request.args.get('title')
    artist = request.args.get('artist')
    duration = request.args.get('duration', type=float, default=0)
    
    if not title or not artist:
        response = "Title and artist are required"
        print(response)
        return Response(response, status=400, mimetype='text/plain')
    
    aligned_lyrics = get_aligned_lyrics(title, artist, duration)
    
    if aligned_lyrics:
        print(aligned_lyrics)
        return Response(aligned_lyrics, mimetype='text/plain')
    else:
        response = ""
        print("No lyrics found")
        return Response(response, status=404, mimetype='text/plain')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 51232))
    app.run(host='0.0.0.0', port=port)
