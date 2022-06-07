import os
from time import sleep
from pyrogram import Client, filters
from bot.helpers.sql_helper import gDriveDB, idsDB
from bot.helpers.utils import CustomFilters, humanbytes
from bot.helpers.downloader import download_file
from bot.helpers.gdrive_utils import GoogleDrive 
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.config import Messages, BotCommands
from pyrogram.errors import FloodWait, RPCError

@app.on_message(filters.command(['m3u8', 'cevir']))
async def convert(client, message):
    try:
        args = message.text.split(' ', 1)[1]
        link = args.split('||')[0].replace(' ', '')
        filename = args.split('||')[1].replace(' ', '')
    except:
        print_exc()
        return await message.reply(f'''Kullanım: `/convert m3u8_link||dosya_ismi`
Admin : [Click to go.](https://t.me/lordzedix)
''')
    _info = await message.reply('PleaseWait...')
    
    proc = await asyncio.create_subprocess_shell(
        f'ffmpeg -i "{link}" -c copy -bsf:a aac_adtstoasc {filename}.mp4',
        stdout=PIPE,
        stderr=PIPE
    )
    await _info.edit("Converting file to mp4...")
    out, err = await proc.communicate()
    await _info.edit('File successfully Convert.')
    print('\n\n\n', out, err, sep='\n')
    try: 
        await _info.edit('Adding Thumbnails...')
        proc2 = await asyncio.create_subprocess_shell(
            f'ffmpeg -i {filename}.mp4 -ss 00:02:00.000 -vframes 5 {filename}.jpg',
            stdout=PIPE,
            stderr=PIPE
        )
        await proc2.communicate()
        await _info.edit('shooting duration')
        proc3 = await asyncio.create_subprocess_shell(
            f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {filename}.mp4',
            stdout=PIPE,
            stderr=STDOUT
        )
        duration, _ = await proc3.communicate()
        await _info.edit('uploading to telegram')

        await _info.edit("File uploading to Telegram...")
        def progress(current, total):
            print(message.from_user.first_name, ' -> ', current, '/', total, sep='')
        await client.send_video(message.chat.id, f'{filename}.mp4', duration=int(float(duration.decode())), thumb=f'{filename}.jpg', file_name=f'{filename}.mp4', progress=progress)
        os.remove(f'{filename}.mp4')
        os.remove(f'{IMG_20211110_010456_911.png}')
    except:
        print_exc()
        return await _info.edit('`Something went wrong..`')


@Client.on_message(filters.private & filters.incoming & filters.text & (filters.command(BotCommands.Download) | filters.regex('^(ht|f)tp*')) & CustomFilters.auth_users)
def _download(client, message):
  user_id = message.from_user.id
  if not message.media:
    sent_message = message.reply_text('🕵️**..ဖိုင်လင့်ကိုစစ်ဆေးနေပါသည်...**', quote=True)
    if message.command:
      link = message.command[1]
    else:
      link = message.text
    if 'drive.google.com' in link:
      sent_message.edit(Messages.CLONING.format(link))
      LOGGER.info(f'Copy:{user_id}: {link}')
      msg = GoogleDrive(user_id).clone(link)
      sent_message.reply_text(msg)
    else:
      if '|' in link:
        link, filename = link.split('|')
        link = link.strip()
        filename.strip()
        dl_path = os.path.join(f'{DOWNLOAD_DIRECTORY}/{filename}')
      else:
        link = link.strip()
        filename = os.path.basename(link)
        dl_path = DOWNLOAD_DIRECTORY
      LOGGER.info(f'Download:{user_id}: {link}')
      sent_message.edit(Messages.DOWNLOADING.format(link))
      result, file_path = download_file(link, dl_path)
      if result == True:
        sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
        msg = GoogleDrive(user_id).upload_file(file_path)
        sent_message.reply_text(msg)
        LOGGER.info(f'Deleteing: {file_path}')
        os.remove(file_path)
      else:
        sent_message.edit(Messages.DOWNLOAD_ERROR.format(file_path, link))


@Client.on_message(filters.private & filters.incoming & (filters.document | filters.audio | filters.video) & CustomFilters.auth_users)
def _telegram_file(client, message):
  user_id = message.from_user.id
  sent_message = message.reply_text('🕵️**.ဖိုင်လင့်ကိုစစ်ဆေးနေပါသည်...**', quote=True)
  if message.document:
    file = message.document
  elif message.video:
    file = message.video
  elif message.audio:
    file = message.audio
  sent_message.edit(Messages.DOWNLOAD_TG_FILE.format(file.file_name, humanbytes(file.file_size), file.mime_type))
  LOGGER.info(f'Download:{user_id}: {file.file_id}')
  try:
    file_path = message.download(file_name=DOWNLOAD_DIRECTORY)
    sent_message.edit(Messages.DOWNLOADED_SUCCESSFULLY.format(os.path.basename(file_path), humanbytes(os.path.getsize(file_path))))
    msg = GoogleDrive(user_id).upload_file(file_path, file.mime_type)
    sent_message.reply_text(msg)
  except RPCError:
    sent_message.edit(Messages.WENT_WRONG)
  LOGGER.info(f'Deleteing: {file_path}')
  os.remove(file_path)
