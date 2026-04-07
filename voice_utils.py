import asyncio
import edge_tts
import pygame
import os

async def speak(text):
    """将文字转为语音并播放"""
    output_file = "response.mp3"
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(output_file)

    pygame.mixer.init()
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(1)
    
    pygame.mixer.quit()
