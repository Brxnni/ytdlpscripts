import os
import re
import time
import shutil
import pathlib
import urllib3
import requests
import subprocess
import mutagen.id3 as id3

from PIL import Image
from bs4 import BeautifulSoup

print("- Initiating requests session...")

SESSION = requests.Session()
LOCAL = pathlib.Path(__file__).parent

YT_THUMBNAIL_URL = "https://img.youtube.com/vi/%s/%s.jpg"
YT_THUMBNAIL_TYPES = ["maxresdefault", "sddefault", "hqdefault", "mqdefault", "default"]

class COLORS:
	RED = "\033[91m"
	BLUE = "\033[94m"
	BOLD = "\033[1m"
	END = "\033[0m"

# https://stackoverflow.com/a/19271897
def clean_img(img_path) -> None:
	print(f"{COLORS.RED}> Updating image to remove potential black bars...{COLORS.END}")
	img = Image.open(img_path)
	rotated_img = img.rotate(90)

	if img.getpixel((0, 0)) != (0, 0, 0) and rotated_img.getpixel((0, 0)) != (0, 0, 0):
		return

	# Do detect black borders on just the left and right, also check the 90° rotated image
	bounding_box = img.getbbox()
	rotated_bounding_box = rotated_img.getbbox()

	if bounding_box[2:4] != img.size:
		img = img.crop(bounding_box)
	elif rotated_bounding_box[2:4] != img.size:
		img = rotated_img.crop(rotated_bounding_box).rotate(-90)
	
	img.save(img_path)

def download_web_image(url, out) -> bool:
	res = SESSION.get(url, stream=True)

	if res.status_code == 404: return False

	with open(out, "wb") as img_file:
		while True:
			try:
				shutil.copyfileobj(res.raw, img_file)
				return True
			except urllib3.exceptions.SSLError:
				continue

def get_yt_thumbnail(url, cwd) -> None:
	print(f"{COLORS.BLUE}> Downloading thumbnail from {url}...{COLORS.END}")
	video_id = re.findall("=[a-zA-Z0-9-_]{11}", url)[0][1:]

	for thumbnail_type in YT_THUMBNAIL_TYPES:
		print(f"{COLORS.BLUE}  > Attempting type {thumbnail_type}...{COLORS.END}")
		thumbnail_url = YT_THUMBNAIL_URL % (video_id, thumbnail_type)
		if download_web_image(thumbnail_url, cwd / "temp.png"): return

def get_mp3_data(mp3_path) -> dict:
	return id3.ID3(mp3_path)

def update_mp3(mp3_path, new_data) -> None:
	print(f"{COLORS.RED}> Updating ID3 tags {', '.join(new_data.keys())}{COLORS.END}")
	mp3 = id3.ID3(mp3_path)
	mp3.delall("APIC:")
	for k, v in new_data.items():
		mp3.delall(k)
		mp3[k] = v
	mp3.save()

def update_date(mp3_path, mod_time) -> None:
	print(f"{COLORS.RED}> Changing date of file {mp3_path}...{COLORS.END}")
	os.utime(mp3_path, (round(time.time()), mod_time))

def get_genius_lyrics(url) -> str:
	print(f"{COLORS.BLUE}> Getting lyrics for {url}...{COLORS.END}")
	# Using a session is a lot faster after the first time
	content = SESSION.get(url).content
	page = BeautifulSoup(content, "html.parser").find("body")

	lyrics_container = page.find("div", attrs = {"data-lyrics-container": "true"})
	# If the song is an instrumental, the div doesn't have the data-lyrics-container attribtue set
	# If the song doesn't exist, then don't this also fails
	if lyrics_container == None:
		print(f"{COLORS.BLUE}  > This song is an instrumental or doesn't exist{COLORS.END}")
		return ""

	for br in lyrics_container.find_all("br"):
		br.replace_with("\x0a")

	lyrics = lyrics_container.getText()
	print(f"{COLORS.BLUE}  > {lyrics[:25]}{COLORS.END}")
	return lyrics

def get_img_data(path) -> bytes:
	print(f"{COLORS.BLUE}> Getting thumbnail from {path}...{COLORS.END}")
	with open(path, "rb") as file:
		return file.read()

def download_audio(audio_src, cwd, filename=None) -> None:
	print(f"{COLORS.BLUE}> Downloading audio from {audio_src}...{COLORS.END}")
	
	cmd = ["yt-dlp", "--extract-audio", "--audio-format", "mp3", audio_src]
	if filename != None: cmd.extend(["-o", filename])
	print(f"{COLORS.BLUE}> cmd: {' '.join(cmd)}{COLORS.END}")
	
	subprocess.Popen(
		cmd,
		cwd=cwd,
		stdout=subprocess.DEVNULL
	).wait()

def newest_files(path) -> list[str]:
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    return sorted(paths, key=os.path.getctime)
