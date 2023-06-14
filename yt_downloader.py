from pytube import YouTube

url = input("URL: ")
type_obj = input('mp3, mp4: ')
yt = YouTube(url)
if type_obj == "mp4":
    yt.streams.filter(file_extension='mp4').first().download('video', f'{yt.title}.mp4')
elif type_obj == "mp3":
    yt.streams.filter(only_audio=True).first().download('audio', f'{yt.title}.mp3')
print("Скачано")