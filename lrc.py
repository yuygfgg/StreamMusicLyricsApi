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
    unformatted_lines = []  # List to store lines that do not match the pattern
    # Update pattern to match all three formats
    pattern = re.compile(r'\[(\d{2}):(\d{2})([.:]\d{2,3})?\](.*)')
    for line in lyrics.split('\n'):
        match = pattern.match(line)
        if match:
            minute, second, millisecond, lyric = match.groups()
            # Normalize time stamp format
            millisecond = millisecond if millisecond else '.000'  # Default to '.000' if millisecond part is missing
            millisecond = millisecond.replace(':', '.')  # Replace ':' with '.' if needed
            time_stamp = f"[{minute}:{second}{millisecond}]"
            lyrics_dict[time_stamp] = lyric
        else:
            unformatted_lines.append(line)  # Collect lines that do not match
    return lyrics_dict, unformatted_lines

def merge_lyrics(lrc_dict, tlyric_dict, unformatted_lines):
    merged_lyrics = unformatted_lines  # Start with unformatted lines
    all_time_stamps = sorted(set(lrc_dict.keys()).union(tlyric_dict.keys()))
    for time_stamp in all_time_stamps:
        original_line = lrc_dict.get(time_stamp, '')
        translated_line = tlyric_dict.get(time_stamp, '')
        merged_lyrics.append(f"{time_stamp} {original_line}")
        if translated_line:
            merged_lyrics.append(f"{time_stamp} {translated_line}")
    return '\n'.join(merged_lyrics)

def attempt_to_download_lyrics_from_songs(songs):
    print("Starting to attempt to download lyrics for songs list:")
    print(songs)
    for index, song in enumerate(songs):
        print(f"Trying song {index + 1}/{len(songs)} with id {song['id']}")
        try:
            lyrics_content, trans_lyrics_content = download_lyrics(song['id'])
            if lyrics_content:
                # calculate lyrics line number
                lines = lyrics_content.count('\n') + 1
                if lines > 5:
                    print(f"Lyrics with more than 5 lines found for song with id {song['id']}")
                    print(lyrics_content)
                    return lyrics_content, trans_lyrics_content
                else:
                    print(f"Lyrics found for song with id {song['id']} but less than 6 lines")
            else:
                print(f"No lyrics found for song with id {song['id']}")
        except Exception as e:
            print(f"Error downloading lyrics for song with id {song['id']}: {e}")
    
    print("No suitable lyrics found for any songs in the list.")
    return None, None

def get_aligned_lyrics(title, artist, album, duration):
    keyword = f"{album} - {title}"
    search_result = search_song(keyword)
    
    if not search_result:
        return None
    
    songs = search_result.get('songs', [])
    songs = [song for song in songs if abs(song['duration'] / 1000 - duration) <= 3]
    
    if not songs:
        return None
    
    lyrics_content, trans_lyrics_content = attempt_to_download_lyrics_from_songs(songs)
    
    if lyrics_content:
        lrc_dict, unformatted_lines = parse_lyrics(lyrics_content)
        if len(lrc_dict) < 5:  # Check if there are less than 5 formatted lines
            return None
        tlyric_dict, _ = parse_lyrics(trans_lyrics_content if trans_lyrics_content else '')
        merged = merge_lyrics(lrc_dict, tlyric_dict, unformatted_lines)
        print("merged")
        print(merged)
        return merged
    else:
        return None

@app.route('/lyrics', methods=['GET'])
def lyrics():
    title = request.args.get('title')
    artist = request.args.get('artist')
    album = request.args.get('album')
    duration = request.args.get('duration', type=float, default=0)
    
    if not title or not artist:
        response = "Title and artist are required"
        return Response(response, status=400, mimetype='text/plain')
    
    aligned_lyrics = get_aligned_lyrics(title, artist, album, duration)
    
    if aligned_lyrics:
        return Response(aligned_lyrics, mimetype='text/plain')
    else:
        response = "No lyrics found"
        return Response(response, status=404, mimetype='text/plain')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 51232))
    app.run(host='0.0.0.0', port=port)
