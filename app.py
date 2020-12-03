from flask import Flask, render_template, request
from googleapiclient.discovery import build
import os
import re
from datetime import timedelta
from googleapiclient.errors import HttpError


def ConvertSectoDay(n): 
    day = str(int(n // (24 * 3600))) 
    n = n % (24 * 3600) 
    hour = str(int(n // 3600))
    n %= 3600
    minutes = str(int(n // 60))
    n %= 60
    seconds = str(int(n)) 
    if int(day)>1:
        d = " days, "
    else:
        d = " day, "

    if int(hour)>1:
        h = " hours, "
    else:
        h = " hour, "
    if int(minutes)>1:
        m = " minutes, "
    else:
        m = " minute, "
    if int(seconds)>1:
        s = " seconds"
    else:
        s = " second"

    if int(day)>0:
        return day+d+hour+h+minutes+m+seconds+s 
    elif int(hour)>0:
        return hour+h+minutes+m+seconds+s
    elif int(minutes)>0:
        return minutes+m+seconds+s
    else:
        return seconds+s


api_key = 'YOUR_API_KEY_HERE'


youtube = build('youtube', 'v3', developerKey = api_key)


pl_pattern = re.compile('^([\S]+list=)?([\w_-]+)[\S]*$')
minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')
hours_pattern = re.compile(r'(\d+)H')

app = Flask(__name__)

@app.route('/', methods=["GET","POST"])
def index():
    total_seconds = 0
    vid_count = 0
    nextPageToken = None
    if request.method == "POST":
        plist = request.form.get("list-url")
        data = ["Please enter a valid youtube playlist URL"]
        if not plist:
            return render_template('index.html', data=data)

        plist = plist.strip()

        if plist=="" or "'" in plist or " " in plist or "<" in plist or ">" in plist or '"' in plist or '#' in plist or '|' in plist or '@' in plist or '^' in plist:
            return render_template('index.html', data=data)

        m = pl_pattern.match(plist)
        if m:
            m = m.group(2)
        else:
            return render_template("index.html", data=data)
        while True:        
            pl_request = youtube.playlistItems().list(
                part = 'contentDetails',
                playlistId=m,
                maxResults = 50,
                pageToken = nextPageToken
            )
            try:
                pl_response = pl_request.execute()
            except HttpError:
                print("YUPPP")
                return render_template("index.html", data=['Could not find playlist. Please enter the URL again.'])

            vid_ids = []
            for item in pl_response['items']:
                vid_ids.append(item['contentDetails']['videoId'])
                vid_count+=1

            vid_request = youtube.videos().list(
                part="contentDetails",
                id=','.join(vid_ids)
            )

            vid_response = vid_request.execute()

            for item in vid_response['items']:
                duration = item['contentDetails']['duration']

                hours = hours_pattern.search(duration)
                minutes = minutes_pattern.search(duration)
                seconds = seconds_pattern.search(duration)

                hours = int(hours.group(1)) if hours else 0
                minutes = int(minutes.group(1)) if minutes else 0
                seconds = int(seconds.group(1)) if seconds else 0

                video_seconds = timedelta(
                    hours = hours,
                    minutes = minutes,
                    seconds = seconds
                ).total_seconds()

                total_seconds+=video_seconds

            nextPageToken = pl_response.get('nextPageToken')

            if not nextPageToken:
                break
        result = []
        numvids = "Number of videos = "+str(vid_count)
        avg_duration = "Average duration of each video : "+ConvertSectoDay(total_seconds/vid_count)
        at1x = ConvertSectoDay(total_seconds)
        at1x = "Total duration of playlist : "+at1x
        at125x = ConvertSectoDay(total_seconds/1.25)
        at125x = "At 1.25x : "+at125x
        at150x = ConvertSectoDay(total_seconds/1.5)
        at150x = "At 1.5x : "+at150x
        at175x = ConvertSectoDay(total_seconds/1.75)
        at175x = "At 1.75x : "+at175x
        at2x = ConvertSectoDay(total_seconds/2)
        at2x = "At 2x : "+at2x
        result.extend((numvids, avg_duration, at1x, at125x, at150x, at175x, at2x))
        return render_template("index.html", data=result)
    else:
        return render_template('index.html')

if __name__=="__main__":
    app.run()
