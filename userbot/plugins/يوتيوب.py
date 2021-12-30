import re
import random
import json
from pathlib import Path
import asyncio
import math
import os
import time
from telethon.tl.types import DocumentAttributeAudio
from userbot import iqthon
from ..core.managers import edit_delete, edit_or_reply
from youtube_search import YoutubeSearch
from youtube_dl import YoutubeDL
from youtube_dl.utils import ContentTooShortError,    DownloadError,    ExtractorError,    GeoRestrictedError,    MaxDownloadsReached,    PostProcessingError,    UnavailableVideoError,    XAttrMetadataError


async def progress(current, total, event, start, type_of_ps, file_name=None):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion
        progress_str = "{0}{1} {2}%\n".format(            "".join(["▰" for i in range(math.floor(percentage / 10))]),            "".join(["▱" for i in range(10 - math.floor(percentage / 10))]),            round(percentage, 2),        )
        tmp = progress_str + "{0} of {1}\nETA: {2}".format(            humanbytes(current), humanbytes(total), time_formatter(estimated_total_time)        )
        if file_name:
            await event.edit(                "{}\nاسم الفايل: `{}`\n{}".format(type_of_ps, file_name, tmp)            )
        else:
            await event.edit("{}\n{}".format(type_of_ps, tmp))


def humanbytes(size):
    if not size:
        return ""
    # 2 ** 10 = 1024
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (        ((str(days) + " day(s), ") if days else "")        + ((str(hours) + " hour(s), ") if hours else "")        + ((str(minutes) + " minute(s), ") if minutes else "")        + ((str(seconds) + " second(s), ") if seconds else "")        + ((str(milliseconds) + " millisecond(s), ") if milliseconds else "")    )
    return tmp[:-2]


@iqthon.on(admin_cmd(pattern="تنزيل( فيديو| صوت) (.*)"))
@iqthon.on(sudo_cmd(pattern="تنزيل( فيديو| صوت) (.*)", allow_sudo=True))
async def download_video(v_url):
    if v_url.fwd_from:
        return
    url = v_url.pattern_match.group(2)
    type = v_url.pattern_match.group(1).lower()

    await edit_or_reply(v_url, "جاري البحث")

    if type == "صوت":
        opts = {            "format": "bestaudio",            "addmetadata": True,            "key": "FFmpegMetadata",            "writethumbnail": True,            "prefer_ffmpeg": True,            "geo_bypass": True,            "nocheckcertificate": True,            "postprocessors": [                {                    "key": "FFmpegExtractAudio",                    "preferredcodec": "mp3",                    "preferredquality": "480",                }            ],            "outtmpl": "%(id)s.mp3",            "quiet": True,            "logtostderr": False,       }
        video = False
        song = True

    elif type == "فيديو":
        opts = {            "format": "best",            "addmetadata": True,            "key": "FFmpegMetadata",            "prefer_ffmpeg": True,            "geo_bypass": True,            "nocheckcertificate": True,            "postprocessors": [                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}            ],            "outtmpl": "%(id)s.mp4",            "logtostderr": False,            "quiet": True,        }
        song = False
        video = True

    try:
        await edit_or_reply(v_url, "إحضار البيانات ، يرجى الانتظار")
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(url)
    except DownloadError as DE:
        await edit_or_reply(v_url, f"`{str(DE)}`")
        return
    except ContentTooShortError:
        await edit_or_reply(v_url, "كان محتوى التنزيل قصيرًا جدًا")
        return
    except GeoRestrictedError:
        await edit_or_reply(v_url,             "الفيديو غير متاح من موقعك الجغرافي بسبب القيود الجغرافية التي يفرضها موقع الويب"        )
        return
    except MaxDownloadsReached:
        await edit_or_reply(v_url, "تم الوصول إلى الحد الأقصى لعدد التنزيلات")
        return
    except PostProcessingError:
        await edit_or_reply(v_url, "حدث خطأ أثناء معالجة ما بعد.")
        return
    except UnavailableVideoError:
        await edit_or_reply(v_url, "الوسائط غير متوفرة بالتنسيق المطلوب.")
        return
    except XAttrMetadataError as XAME:
        await edit_or_reply(v_url, f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
        return
    except ExtractorError:
        await edit_or_reply(v_url, "حدث خطأ أثناء استخراج المعلومات ")
        return
    except Exception as e:
        await edit_or_reply(v_url, f"{str(type(e)): {str(e)}}")
        return
    c_time = time.time()
    if song:
        await edit_or_reply(v_url, 
            f"التحضير لتحميل الاغنيه:\n**{ytdl_data['title']}**\nمن *{ytdl_data['uploader']}*"        )
        await v_url.client.send_file(            v_url.chat_id,            f"{ytdl_data['id']}.mp3",            supports_streaming=True,            attributes=[                DocumentAttributeAudio(                    duration=int(ytdl_data["duration"]),                    title=str(ytdl_data["title"]),                    performer=str(ytdl_data["uploader"]),                )            ],
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(                progress(                    d, t, v_url, c_time, "جاري التحميل ..", f"{ytdl_data['title']}.mp3"                )            ),        )
        os.remove(f"{ytdl_data['id']}.mp3")
        await v_url.delete()
    elif video:
        await edit_or_reply(v_url,             f"التحضير لتحميل الفيديو :\n        \n**{ytdl_data['title']}**        \nمن *{ytdl_data['uploader']}*"        )
        await v_url.client.send_file(            v_url.chat_id,            f"{ytdl_data['id']}.mp4",            supports_streaming=True,            caption=ytdl_data["title"],            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(                progress(                    d, t, v_url, c_time, "Uploading..", f"{ytdl_data['title']}.mp4"                )            ),        )
        os.remove(f"{ytdl_data['id']}.mp4")
        await v_url.delete()


