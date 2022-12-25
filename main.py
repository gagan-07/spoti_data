import spotipy.util as util
import requests
from dateutil import parser
import time
import datetime
import traceback
import threading
import itertools
import pyrebase
import sys 
import credentials



firebaseConfig = credentials.firebaseConfig
error = False
firebase= pyrebase.initialize_app(firebaseConfig)
db = firebase.database()


username = credentials.username
client_id = credentials.client_id
client_secret = credentials.client_secret
redirect_uri = 'http://localhost:7777/callback'



scope = 'user-read-recently-played  user-read-currently-playing user-top-read '

#ask user for permission to use data
access_token = util.prompt_for_user_token(username=username, 
                                   scope=scope, 
                                   client_id=client_id,   
                                   client_secret=client_secret,     
                                   redirect_uri=redirect_uri)

headers = {
    "Authorization": f"Bearer {access_token}"
}
info_dict = {}


# def get_recently_played(limit=50):
#     # global info_dict
#     played_tracks = []
#     for item in requests.get(f'https://api.spotify.com/v1/me/player/recently-played?limit={limit}',headers=headers).json()["items"]:

#         #this part gets the duration of the song played
#         played_tracks.append(item['track']['name'])
#         duration_ms = item['track']["duration_ms"] // 1_000
#         # info_dict[track_name] = duration_ms
#         track_URI = item['track']['uri']
#         track_artist = item['track']['artists'][0]['name']
#         #this part gets the time when the song was played
#         ####################
#         ###FUCK SPOTIFY#####
#         ####################
#         #####:(#############


# def get_top_tracks_artists(choice = "tracks"):
#     timerange_list = ["short_term","long_term","medium_term"]

#     #this part gets the top artists of the user(short term)
#     top_things = {}
#     if choice == "artists" or "tracks":
#         for time in timerange_list:
#             sub_time_top = []
#             for item in requests.get(f'https://api.spotify.com/v1/me/top/{choice}?time_range={time}&limit=50',headers=headers).json()["items"]:
#                 sub_time_top.append(item['name'])
#             top_things[time] = sub_time_top
#     else:
#         return "INVALID REQUEST"
            
    # return top_things


#get currently playing song
def get_currently_playing(items="all"):
    global error
    while True:
            try:
                response = requests.get("https://api.spotify.com/v1/me/player/currently-playing",headers=headers).json()
                track_name = response['item']['name']
                track_artist = response['item']['artists'][0]['name']
                track_duration_seconds = response['item']['duration_ms'] / 1000
                track_progress_seconds = response['progress_ms'] / 1000
                track_uri = response['item']['uri']
                is_playing = response['is_playing']
                spotify_con = True
                error = False
                if items == "all":
                    return track_name,track_duration_seconds,track_progress_seconds,track_artist,is_playing,track_uri
                elif items == "progress":
                    return track_progress_seconds
            except Exception as e:
                if e is KeyError:
                    print(requests.get("https://api.spotify.com/v1/me/player/currently-playing",headers=headers).json())
                print("\rCONNECTION WITH SPOTIFY FAILED! retrying...",end="")
                traceback.print_exc()
                time.sleep(1)
                error = True

#program to check if computer is connected to internet


restart_n = 0
def remove_special(string):
  # Use the replace() method to remove full stops and commas
  return string.replace('.', '').replace(":","").replace("/","").replace("//","")


branch = "tracks"
db.child(branch).set(access_token, access_token)
prev_song = None
start_time = None
buffer_time = None
while True:
    try:

        track_name, song_duration, track_progress,track_artist,is_playing,track_URI = get_currently_playing()
        track_name = remove_special(track_name)
              

        if db.child(branch).child(track_name).get().val() is not None:
            total_time = db.child(branch).child(track_name).get().val()['total_time_played']
            db.child(branch).child(track_name).update({"prev_time":total_time}) 
        else:
            time_now = datetime.datetime.now()
            data ={"duration":song_duration,
            "no_of_times_played":1,
            "time_played_at":time_now.strftime('%Y-%m-%d %H:%M:%S'),
            "time_played_at_list":[time_now.strftime('%Y-%m-%d %H:%M:%S')],
            "total_time_played":0,
            "artist":track_artist,
            "track_URI":track_URI,
            "buffer_time":0,
            "prev_time":0}
            db.child(branch).child(track_name).set(data)
            print(f"\rNEW SONG ADDED!({track_name})")
            sys.stdout.flush()


        
        #WORKING ANIMATION
        anitons = ['|', '/', '-', '\\']
        def animate():
            for c in itertools.cycle(anitons):
                if error:
                    break
                print("\rWORKING " +c + "                                                                               ",end="")                    
                sys.stdout.flush()
                time.sleep(0.1)
        t = threading.Thread(target=animate)
        t.daemon = True
        t.start()



        if is_playing:
            if start_time is None:
                start_time = datetime.datetime.now()
                current_progress = get_currently_playing('progress')
                time_now = datetime.datetime.now()
                fire_time = db.child(branch).child(track_name).get().val()['time_played_at_list']
                fire_time_formatted = datetime.datetime.strptime(fire_time[-1],"%Y-%m-%d %H:%M:%S")
                condition_secs = (time_now - fire_time_formatted).total_seconds()
                # print(f"thiese are the condition secs {condition_secs}")
                if current_progress <= song_duration*0.08 and  condition_secs>= song_duration*0.6:
                    
                    db.child(branch).child(track_name).update({"time_played_at_list":fire_time+[time_now.strftime('%Y-%m-%d %H:%M:%S')]})
                    fire_no = db.child(branch).child(track_name).get().val()['no_of_times_played']
                    db.child(branch).child(track_name).update({'no_of_times_played':fire_no+1})
            if track_name != prev_song and prev_song != None:
                # prev_song = track_name
                elapsed_time = datetime.datetime.now() - start_time
                prev_songbuffer =db.child(branch).child(prev_song).get().val()['buffer_time']
                prev_songtime = db.child(branch).child(prev_song).get().val()['prev_time']
                # print(f"buffer time of {prev_song} is {prev_songbuffer}seconds and elapsed time is {elapsed_time} seconds and previously played time is {prev_songtime}")
                db.child(branch).child(prev_song).update({'total_time_played':elapsed_time.total_seconds()+prev_songtime+prev_songbuffer+7})
                start_time = None
                print(f"\rSONG UPDATED!({prev_song})")
                sys.stdout.flush()
        else:
            if start_time is not None:
                elapsed_time = datetime.datetime.now() - start_time
                db.child(branch).child(track_name).update({"buffer_time": elapsed_time.total_seconds()})
                start_time = None  
        prev_song = track_name
        # print(db.child(branch).child(track_name).get().val())
        error = False
        time.sleep(1)
    except Exception as e:
            error = True
            # print(e)
            # if not is_connected():
            #     print("\rInternet Unavailable!",end="")
            # else:
                # logging.error(e)
            traceback.print_exc()
            
            print("\rRetyring in 5s")
            time.sleep(5)
