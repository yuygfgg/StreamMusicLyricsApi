from flask import Flask, request, Response, jsonify
import requests
import re
import os
from difflib import SequenceMatcher

app = Flask(__name__)

LRC_DIRECTORY = os.environ.get('LRC_DIRECTORY', '/default/path/to/lrcs')

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
    unformatted_lines = []
    pattern = re.compile(r'\[(\d{2}):(\d{2})([.:]\d{2,3})?\](.*)')
    for line in lyrics.split('\n'):
        match = pattern.match(line)
        if match:
            minute, second, millisecond, lyric = match.groups()
            millisecond = millisecond if millisecond else '.000'
            millisecond = millisecond.replace(':', '.')
            time_stamp = f"[{minute}:{second}{millisecond}]"
            lyrics_dict[time_stamp] = lyric
        else:
            unformatted_lines.append(line)
    return lyrics_dict, unformatted_lines

def merge_lyrics(lrc_dict, tlyric_dict, unformatted_lines):
    merged_lyrics = unformatted_lines
    all_time_stamps = sorted(set(lrc_dict.keys()).union(tlyric_dict.keys()))
    for time_stamp in all_time_stamps:
        original_line = lrc_dict.get(time_stamp, '')
        translated_line = tlyric_dict.get(time_stamp, '')
        merged_lyrics.append(f"{time_stamp}{original_line}")
        if translated_line:
            merged_lyrics.append(f"{time_stamp}{translated_line}")
    return '\n'.join(merged_lyrics)

def check_local_lyrics(title):
    for file in os.listdir(LRC_DIRECTORY):
        if file.startswith(title) and file.endswith('.lrc'):
            with open(os.path.join(LRC_DIRECTORY, file), 'r', encoding='utf-8') as f:
                return f.read()
    return None

def get_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_aligned_lyrics(title, artist, album, duration):
    search_keywords = [
        f"{artist} - {album} - {title}",
        f"{album} - {title}",
        f"{artist} - {title}"
    ]

    best_result = None
    highest_similarity = 0

    for keyword in search_keywords:
        search_result = search_song(keyword)
        if not search_result:
            continue

        songs = search_result.get('songs', [])
        songs = [song for song in songs if abs(song['duration'] / 1000 - duration) <= 3]

        for song in songs[:3]:
            lyrics_content, trans_lyrics_content = download_lyrics(song['id'])

            if lyrics_content:
                lrc_dict, unformatted_lines = parse_lyrics(lyrics_content)
                if len(lrc_dict) >= 5:
                    similarity = (
                        get_similarity(title, song['name']) +
                        get_similarity(artist, ', '.join([artist['name'] for artist in song['artists']])) +
                        get_similarity(album, song.get('album', {}).get('name', ''))
                    ) / 3
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_result = lyrics_content

    return best_result

@app.route('/lyrics', methods=['GET'])
def lyrics():
    title = request.args.get('title')
    artist = request.args.get('artist')
    album = request.args.get('album')
    duration = request.args.get('duration', type=float, default=0)

    local_lyrics = check_local_lyrics(title)
    if local_lyrics:
        response = Response(local_lyrics, mimetype='text/plain')
        response.headers['Content-Type'] = 'text/plain'
        return response

    best_lyrics = get_aligned_lyrics(title, artist, album, duration)
    if best_lyrics:
        response = Response(best_lyrics, mimetype='text/plain')
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        response = Response('', status=404)
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/lyrics/confirm', methods=['POST'])
def confirm_lyrics():
    data = request.get_json()
    path = data.get('path')
    lyrics = data.get('lyrics')
    
    if not path or not lyrics:
        response = Response('{"message": "Invalid request data"}', status=400, mimetype='application/json')
        return response

    lrc_path = re.sub(r'\.\w+$', '.lrc', path)

    try:
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        response = Response('{"message": "Lyrics saved successfully"}', status=200, mimetype='application/json')
        return response
    except Exception as e:
        print(f"Error saving lyrics to {lrc_path}: {e}")
        response = Response(f'{{"message": "Error saving lyrics: {e}"}}', status=500, mimetype='application/json')
        return response


if __name__ == '__main__':
    # 端口号现在从环境变量 PORT 中获取，如果没有设置，默认为 51232
    port = int(os.environ.get("PORT", 51232))
    app.run(host='0.0.0.0', port=port)
