import os
import json
import random
import discord
from discord import app_commands
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 설정
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
GUILD_ID = os.getenv("GUILD_ID")  # 선택사항 (빠른 테스트용)

# 파일 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOKES_PATH = os.path.join(BASE_DIR, "jokes.json")


def load_jokes():
    """jokes.json에서 농담 로드"""
    try:
        with open(JOKES_PATH, "r", encoding="utf-8") as f:
            jokes = json.load(f)
        if isinstance(jokes, list) and jokes:
            return jokes
    except Exception as e:
        print(f"[ERROR] Failed to load jokes: {e}")
    return ["농담을 불러올 수 없습니다 😢"]


def save_jokes(jokes):
    """농담을 jokes.json에 저장"""
    try:
        with open(JOKES_PATH, "w", encoding="utf-8") as f:
            json.dump(jokes, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save jokes: {e}")
        return False


# 봇 설정
JOKES = load_jokes()
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


@bot.event
async def on_ready():
    """봇 시작 시 슬래시 명령어 동기화"""
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f"[OK] Guild {GUILD_ID} 동기화 완료. 봇: {bot.user}")
        else:
            await tree.sync()
            print(f"[OK] 글로벌 동기화 완료. 봇: {bot.user}")
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")


@tree.command(name="joke", description="랜덤 농담을 들려줍니다 🦉")
async def joke(interaction: discord.Interaction):
    """랜덤 농담 출력"""
    await interaction.response.send_message(f"{random.choice(JOKES)} 🦉")


@tree.command(name="add_joke", description="새로운 농담을 추가합니다 (관리자 전용)")
@app_commands.describe(joke="추가할 농담 내용")
async def add_joke(interaction: discord.Interaction, joke: str):
    """농담 추가 (관리자 전용)"""
    # 권한 체크
    if interaction.user.id != ALLOWED_USER_ID:
        await interaction.response.send_message("❌ 권한이 없습니다!", ephemeral=True)
        return

    joke = joke.strip()
    
    # 유효성 검사
    if len(joke) < 3:
        await interaction.response.send_message("❌ 최소 3글자 이상 입력해주세요.", ephemeral=True)
        return
    
    if joke in JOKES:
        await interaction.response.send_message("❌ 이미 존재하는 농담입니다!", ephemeral=True)
        return

    # 농담 추가 및 저장
    JOKES.append(joke)
    if save_jokes(JOKES):
        await interaction.response.send_message(
            f"✅ 추가 완료!\n**농담:** {joke}\n**전체:** {len(JOKES)}개"
        )
    else:
        JOKES.pop()
        await interaction.response.send_message("❌ 저장 실패. 다시 시도해주세요.", ephemeral=True)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN 환경변수를 설정해주세요!")
    if not ALLOWED_USER_ID:
        raise RuntimeError("ALLOWED_USER_ID 환경변수를 설정해주세요!")
    bot.run(DISCORD_TOKEN)
