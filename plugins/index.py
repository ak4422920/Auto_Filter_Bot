import asyncio
import time
from pyrogram import Client, filters, enums
from vars import *
from Database.maindb import mdb
from pyrogram.errors import FloodWait
from math import ceil

@Client.on_message(filters.command("index") & filters.user(ADMIN_ID))
async def manual_index(client, message):
    if len(message.command) < 3:
        return await message.reply("❌ **Usage:** `/index [limit] [category]`\nExample: `/index 3000 indian`")
    
    try:
        limit = int(message.command[1])
        cat = message.command[2].lower()
        if cat not in ["indian", "foreign", "animal"]:
            return await message.reply("❌ Category galat hai!")

        target_chat = INDIAN_CHANNEL if cat == "indian" else FOREIGN_CHANNEL if cat == "foreign" else ANIMAL_CHANNEL
        
        # Pehle channel ka sabse naya message ID nikalte hain
        status = await message.reply("🔍 Channel scan kar raha hoon...")
        last_msgs = await client.get_messages(target_chat, await client.get_chat_history_count(target_chat))
        # Agar history count kaam na kare toh 1 message fetch karke ID lenge
        if not last_msgs:
            async for m in client.get_chat_history(target_chat, limit=1):
                last_msg_id = m.id
        else:
            last_msg_id = last_msgs.id

        await status.edit(f"🚀 **Batch Indexing Started...**\nTarget: `{cat.upper()}`\nLimit: `{limit}`")
        
        count = 0
        BATCH_SIZE = 200 # Ek baar mein 200 messages mangwayenge
        
        # Ulta chalenge (Naye se purane ki taraf)
        for i in range(last_msg_id, max(0, last_msg_id - limit), -BATCH_SIZE):
            # Batch IDs taiyar karna
            stop_id = max(0, i - BATCH_SIZE)
            msg_ids = list(range(i, stop_id, -1))
            
            try:
                # get_messages bots ke liye 100% working hai
                messages = await client.get_messages(target_chat, msg_ids)
                
                for m in messages:
                    if m.video:
                        await mdb.save_video(m.id, m.video.duration, target_chat, cat)
                        count += 1
                
                # Progress update
                await status.edit(f"⏳ **Indexing...**\nProcessed: `{last_msg_id - i}`\nSaved Videos: `{count}`")
                
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                print(f"Batch Error: {e}")
                continue
            
            await asyncio.sleep(1) # Safety delay

        await status.edit(f"✅ **Mission Accomplished!**\nTotal `{count}` videos indexed in **{cat}**.")
        
    except Exception as e:
        await message.reply(f"❌ Index Fatal Error: {str(e)}")

# --- AUTO INDEXING ---
@Client.on_message(filters.chat([INDIAN_CHANNEL, FOREIGN_CHANNEL, ANIMAL_CHANNEL]) & filters.video)
async def auto_save_video(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        cat = "indian" if chat_id == INDIAN_CHANNEL else "foreign" if chat_id == FOREIGN_CHANNEL else "animal"
        await mdb.save_video(message.id, message.video.duration, chat_id, cat)
    except: pass
