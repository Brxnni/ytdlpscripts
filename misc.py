import os
import pathlib
import mutagen.id3 as id3

from lib import COLORS, download_audio, get_yt_thumbnail, get_img_data, update_mp3, download_web_image

LOCAL = pathlib.Path(__file__).parent / "Misc"

YT_URL = "https://www.youtube.com/watch?v=cpEkXk6u_b4"
COVER_SRC = ""
LYRICS = """Few will stop to he-hear
Cured notion
You fall
With tears to the sound
Of no one
Who's to stop me feeling
Healing emotions
Who knew
We have
No one

Few will stop to he-hear
Cured notion
You fall
With tears to the sound
Of no one
Who's to stop me feeling
Healing emotions
Who knew
We have
No one"""
ALBUM = "Stay Ugly"
ARTIST = "CRIM3S"
SONG = "lost"

def main():
	filename = f"{SONG}.mp3"
	download_audio(YT_URL, LOCAL, filename)
	print(COLORS.BOLD + filename + COLORS.END)

	if not COVER_SRC:	get_yt_thumbnail(YT_URL, LOCAL)
	else:				download_web_image(COVER_SRC, LOCAL / "temp.png")
	
	coverimg = get_img_data(LOCAL / "temp.png")

	updateProps = {}
	if coverimg: updateProps["APIC:"] = id3.APIC(mime="image/png", type=3, desc="Cover", data=coverimg, encoding=id3.Encoding.LATIN1)
	if ARTIST: updateProps["TPE1"] = id3.TPE1(text=ARTIST, encoding=id3.Encoding.UTF8)
	# I'm afraid to mess with the default encoding because I need Russian and other non-ascii letters in my lyrics
	if LYRICS: updateProps["USLT"] = id3.USLT(text=LYRICS, lang="eng")
	if ALBUM: updateProps["TALB"] = id3.TALB(text=ALBUM, encoding=id3.Encoding.UTF8)
	if SONG: updateProps["TIT2"] = id3.TIT2(text=SONG, encoding=id3.Encoding.UTF8)

	update_mp3(LOCAL / filename, updateProps)

	os.remove(LOCAL / "temp.png")

if __name__ == "__main__": main()

def fleece():
	from PIL import Image
	from lib import get_mp3_data

	temp_path = LOCAL / "temp.png"

	fleece_data = get_mp3_data(LOCAL / ".." / "Crystal Castles" / "Crystal Castles (Amnesty I) - Fleece.mp3")
	fleece_cover = fleece_data["APIC:Cover"]

	fleece_data.pop("APIC:Cover")
	update_mp3(
		LOCAL / "Fleece (Instrumental).mp3",
		fleece_data
	)

	with open(temp_path, "wb+") as file:
		file.write(fleece_cover.data)

	fleece_img = Image.open(temp_path)
	fleece_img = fleece_img.convert("1")
	fleece_img.save(temp_path)

	with open(temp_path, "rb") as file:
		update_mp3(
			LOCAL / "Fleece (Instrumental).mp3",
			{"APIC:Cover": id3.APIC(encoding=0, mime="image/png", type=3, desc="Cover", data=file.read())}
		)

# fleece()
