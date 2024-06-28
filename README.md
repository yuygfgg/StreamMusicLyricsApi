# StreamMusicLyricsApi
Stream music lyrics api from Netease Music with translation support.

- lrc.py returns at most 9 lyrics when searching online, sorted by similarity of title, album name, artist name, in json format.
- lrc_single.py returns the highest similarity one in plain text, **without translation**.

# Usage

### Direct Execution

#### Steps:

1. change lrc path in lrc.py to your .lrc file path
2. run the python script
3. set lyrics api in Stream music ```http://localhost:51232/lyrics```
4. set lyrics confirm api ```http://localhost:51232/lyrics/confirm```

## Docker Deployment

#### Steps:

1. Build the Docker image:

   `docker build . -t stream_music_lyrics_api`

2. Deploy the container:

```shell
docker run -d \
--name stream_music_lyrics_api \
-v /path/to/your/lyrics/folder:/lyrics \
-p 51232:51232 \
stream_music_lyrics_api:latest
```

Make sure to replace `/path/to/your/lyrics/folder` with the actual path to your lyrics folder.

<img width="1289" alt="截屏2024-05-17 20 56 10" src="https://github.com/yuygfgg/StreamMusicLyricsApi/assets/140488233/e4394e83-1678-4bba-928d-29100097bcc1">

<img width="1081" alt="截屏2024-05-25 21 30 18" src="https://github.com/yuygfgg/StreamMusicLyricsApi/assets/140488233/217e6ad1-6eb7-4eb4-9ff0-0e82bf50981d">

<img width="1502" alt="截屏2024-05-17 20 54 50" src="https://github.com/yuygfgg/StreamMusicLyricsApi/assets/140488233/3b9a053d-a809-4ea6-9b74-a6d19f024fc6">
