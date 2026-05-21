from herokutl.types import Message
from .. import loader, utils
import os
import re
import yt_dlp

# meta developer: @Nik4mnost #2347


@loader.tds
class TikTokMod(loader.Module):
    """Модуль для скачивания видео и аудио с ТТ по ссылке"""
    strings = {
        "name": "TikTok",
        "downloading": "⬇️ Скачиваю видео...",
        "downloading_audio": "<tg-emoji emoji-id=5215679757366089921>🥳</tg-emoji>Скачиваю аудио...",
        "uploading": "📤 Загружаю...",
        "uploading_audio": "<tg-emoji emoji-id=5215679757366089921>🥳</tg-emoji>Загружаю аудио...",
        "error": "❌ Ошибка: {}",
        "no_link": "❌ Укажите ссылку на TikTok\nИспользование: ,tt <ссылка> или реплай на сообщение со ссылкой",
        "no_link_audio": "❌ Укажите ссылку на TikTok\nИспользование: ,ttsound <ссылка> или реплай на сообщение со ссылкой",
    }
    strings_ru = {
        "downloading": "⬇️ Скачиваю видео...",
        "downloading_audio": "🎵 Скачиваю аудио...",
        "uploading": "📤 Загружаю...",
        "uploading_audio": "🎵 Загружаю аудио...",
        "error": "❌ Ошибка: {}",
        "no_link": "❌ Укажите ссылку на TikTok\nИспользование: ,tt <ссылка> или реплай на сообщение со ссылкой",
        "no_link_audio": "❌ Укажите ссылку на TikTok\nИспользование: ,ttsound <ссылка> или реплай на сообщение со ссылкой",
    }

    def _sanitize_filename(self, name: str) -> str:
        """Clean filename from invalid characters"""
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = name.strip()
        if len(name) > 100:
            name = name[:100]
        return name if name else "tiktok_audio"

    async def _get_url(self, message: Message) -> str:
        """Get URL from command args or reply"""
        args = utils.get_args_raw(message)
        if args:
            return args.strip()
        
        reply = await message.get_reply_message()
        if reply and reply.text:
            urls = re.findall(r'https?://(?:vt\.|vm\.|www\.)?tiktok\.com/\S+', reply.text)
            if urls:
                return urls[0]
        
        return None

    async def _download(self, url: str, extract_audio: bool = False) -> tuple[str, str]:
        """Download video or audio from TikTok, returns (filename, title)"""
        temp_file = "temp_tiktok"
        
        if extract_audio:
            opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{temp_file}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{temp_file}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if extract_audio:
                filename = filename.rsplit('.', 1)[0] + '.mp3'
                title = info.get('track') or info.get('alt_title') or info.get('title') or 'audio'
                if title.lower() in ['tiktok', 'tiktok video', 'video', '', 'audio']:
                    title = info.get('uploader', '').replace(' TikTok', '') or 'tiktok_audio'
                title = self._sanitize_filename(title)
            else:
                if not filename.endswith('.mp4'):
                    ext = info.get('ext', 'mp4')
                    filename = f"{temp_file}.{ext}"
                title = info.get('title', 'video')
        
        return filename, title

    @loader.command(
        ru_doc="Скачать видео из TikTok ",
        en_doc="Download TikTok video "
    )
    async def tt(self, message: Message):
        """Download TikTok video"""
        url = await self._get_url(message)
        if not url:
            await utils.answer(message, self.strings["no_link"])
            return
        
        status = await utils.answer(message, self.strings["downloading"])
        
        try:
            filename, _ = await self._download(url, extract_audio=False)
            
            await status.edit(self.strings["uploading"])
            
            with open(filename, 'rb') as f:
                await message.client.send_file(
                    message.chat_id,
                    f,
                    caption=f"🎬 TikTok Video\n{url}",
                    reply_to=message.id
                )
            
            os.remove(filename)
            await status.delete()
            
        except Exception as e:
            error_text = self.strings["error"].format(str(e)[:100])
            await utils.answer(status, error_text)

    @loader.command(
        ru_doc="Скачать звук из видео TikTok",
        en_doc="Download audio from TikTok video"
    )
    async def ttsound(self, message: Message):
        """Download TikTok audio"""
        url = await self._get_url(message)
        if not url:
            await utils.answer(message, self.strings["no_link_audio"])
            return
        
        status = await utils.answer(message, self.strings["downloading_audio"])
        
        try:
            filename, title = await self._download(url, extract_audio=True)
            
            await status.edit(self.strings["uploading_audio"])
            
            with open(filename, 'rb') as f:
                await message.client.send_file(
                    message.chat_id,
                    f,
                    caption=None,
                    reply_to=message.id,
                    file_name=f"{title}.mp3"
                )
            
            os.remove(filename)
            await status.delete()
            
        except Exception as e:
            error_text = self.strings["error"].format(str(e)[:100])
            await utils.answer(status, error_text)