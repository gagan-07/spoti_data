import plotly.graph_objects as go
import plotly.express as px
import time
import datetime
import pyrebase
import plotly.offline as offline
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import credentials

#firebase credentials
firebaseConfig = credentials.firebaseConfig

print("Initializing Firebase database...")
successful = False
error = False
while not successful:
    try:
        firebase= pyrebase.initialize_app(firebaseConfig)
        db = firebase.database()
        print("Database initialized!")
        successful = True
        error = False
    except Exception as e:
        print(f"UNSUCCESSFUL! ERROR:{e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        error = True
data = db.child('tracks').get().val()

print(data)
date_with_tracks = []
no = 0
duration_by_artist ={}
top_artist_duration = {}
for track in data:
    # if no>5:
    #     break
    
    track_info = data[track]
    try:
        # print(data[track]['artist'])
        artist = track_info['artist']
    except Exception as e:
        print(f"the error was for track {track_info} and the track was {track}")
    duration = track_info['duration']
    no_of_times_played = track_info['no_of_times_played']
    if artist in top_artist_duration:
        top_artist_duration[artist] +=(duration*no_of_times_played)
    else:
        top_artist_duration[artist] = (duration*no_of_times_played)
    # duration_by_artist[track_info['artist']] = {"total_duration":0}

    no+=1
# print(date_with_tracks)


# RESTRICTING ARTISTS TO TOP (x)
sorted_duration = sorted(top_artist_duration.items(), key=lambda x: x[1], reverse=True)
# print(f"top artists are {sorted_duration[:10]}")
top_artists = [artist for artist,duration in sorted_duration[:7]]
new_data = {}
# print(f"top artists are {top_artists}")
for track in data:
    artist = data[track]['artist']
    # print(f"checking for artist {artist} is in top list")
    if data[track]['artist'] in top_artists:
        new_data[track] = data[track]
        for date in data[track]['time_played_at_list']:
            date_with_tracks.append({track:date})
    else:
        pass
# print(f"new data is {new_data}")
data = new_data
dates = [datetime.datetime.strptime(list(track.values())[0], '%Y-%m-%d %H:%M:%S') for track in date_with_tracks]
sorted_dates, sorted_songs = zip(*sorted(zip(dates,date_with_tracks)))
song_len = len(sorted_songs)
i = 0
fig,ax = plt.subplots()
def update_pie(something):
    global i
    if i!=song_len:
        labels = []
        values = []
    if i<song_len:
        artist = data[list(sorted_songs[i].keys())[0]]['artist']
        # print(f"the artist is {artist}")
        if artist in duration_by_artist:
            # print(f"the current duration of the song is {duration_by_artist[artist]}")
            # print(f"the duration of the song to be added is {data[list(sorted_songs[i].keys())[0]]['duration']}")
            duration_by_artist[data[list(sorted_songs[i].keys())[0]]['artist']] += data[list(sorted_songs[i].keys())[0]]['duration']
        else:
            duration_by_artist[artist] = data[list(sorted_songs[i].keys())[0]]['duration']
        for artist in duration_by_artist:
            # print(f"the artist iteme is {artist}")
            labels.append(artist)
            values.append(duration_by_artist[artist])
    # print(f"the labels are {labels} and the value of i is {i}")
    ax.clear()
    ax.pie(values,labels=labels,autopct="%1.1f%%",shadow=True,startangle=90)
    percents= [size/sum(values) for size in values]
    font_sizes = [percent*30 for percent in percents]
    ax.axis('equal')
    # ax.legend(fontsize=font_sizes)
    i += 1
ani=  animation.FuncAnimation(fig,update_pie,frames=60,repeat=True)
plt.show()