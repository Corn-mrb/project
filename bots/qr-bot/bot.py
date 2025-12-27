import discord
from discord.ext import commands
from discord import app_commands
import secrets
import os
import json
from datetime import datetime

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 매장 관리 권한이 있는 역할 리스트
ALLOWED_ROLES = [
    "Helper",
    "비트코인 기업 (Bitcoin Corporation)",
    "비트코인 경제매장 (Sea of Corea)"
]

# 역할 권한 확인 함수
def has_allowed_role(interaction: discord.Interaction) -> bool:
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in ALLOWED_ROLES for role in user_roles)

# 데이터 저장 폴더
DATA_DIR = "data"
QR_DIR = "qr_codes"
STORES_FILE = os.path.join(DATA_DIR, "stores.json")

# 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

# 매장 데이터 로드/저장 함수
def load_stores():
    if os.path.exists(STORES_FILE):
        with open(STORES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_stores(stores):
    with open(STORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(stores, f, ensure_ascii=False, indent=2)

# 전역 변수
stores = load_stores()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ {bot.user} 봇이 준비되었습니다!')
    print(f'서버 수: {len(bot.guilds)}')
    print(f'로드된 매장 수: {len(stores)}')

# 1. 매장 등록
@bot.tree.command(name="매장등록", description="매장 입장용 QR 생성")
@app_commands.describe(
    매장명="매장 또는 이벤트 이름",
    최소역할="입장 가능한 최소 역할 (선택사항)",
    부여역할="입장 승인 시 자동 부여할 역할 (선택사항)",
    암구호="오늘의 암구호 (선택사항)"
)
async def create_store(
    interaction: discord.Interaction,
    매장명: str,
    최소역할: discord.Role = None,
    부여역할: discord.Role = None,
    암구호: str = None
):
    # 권한 확인
    if not has_allowed_role(interaction):
        await interaction.response.send_message(
            "❌ 권한이 없습니다.\n**허용된 역할:** Helper, 비트코인 기업, 비트코인 경제매장",
            ephemeral=True
        )
        return
    # 세션 ID 생성 (숫자 2자리: 01~99)
    import random
    
    # 중복 방지를 위해 기존 코드와 겹치지 않을 때까지 생성
    while True:
        session_id = f"{random.randint(1, 99):02d}"  # 01, 02, ..., 99
        
        # 중복 확인
        if session_id not in stores:
            break
    
    # 매장 정보 저장
    stores[session_id] = {
        "store_name": 매장명,
        "min_role_id": 최소역할.id if 최소역할 else None,
        "grant_role_id": 부여역할.id if 부여역할 else None,
        "passphrase": 암구호,
        "owner_id": interaction.user.id,
        "guild_id": interaction.guild_id,
        "created_at": datetime.now().isoformat(),
        "approved_users": []  # 승인된 사용자 목록
    }
    save_stores(stores)
    
    # 응답 메시지 (QR 없이 텍스트만)
    embed = discord.Embed(
        title=f"🏪 {매장명} - 매장 등록 완료",
        description=f"## 매장 코드\n# **`{session_id}`**\n\n방문자는 `/입장 {session_id}` 명령어를 사용하세요.",
        color=discord.Color.blue()
    )
    if 최소역할:
        embed.add_field(name="최소 역할", value=최소역할.mention, inline=True)
    else:
        embed.add_field(name="최소 역할", value="없음 (모두 입장 가능)", inline=True)
    if 부여역할:
        embed.add_field(name="부여 역할", value=부여역할.mention, inline=True)
    if 암구호:
        embed.add_field(name="암구호 설정", value="✅ 설정됨", inline=True)
    else:
        embed.add_field(name="암구호 설정", value="❌ 없음", inline=True)
    
    embed.add_field(
        name="💡 사용 방법",
        value="• 매장 코드를 방문자에게 공유하세요\n• 방문자가 `/입장 코드`를 입력하면 자동 검증됩니다\n• `/매장수정`으로 조건 변경 가능",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 2. 매장 수정
@bot.tree.command(name="매장수정", description="매장 정보 수정")
@app_commands.describe(
    매장코드="수정할 매장의 코드",
    매장명="새 매장명 (선택사항)",
    최소역할="새 최소 역할 (선택사항)",
    부여역할="새 부여 역할 (선택사항)",
    암구호="새 암구호 (선택사항)"
)
async def update_store(
    interaction: discord.Interaction,
    매장코드: str,
    매장명: str = None,
    최소역할: discord.Role = None,
    부여역할: discord.Role = None,
    암구호: str = None
):
    # 권한 확인
    if not has_allowed_role(interaction):
        await interaction.response.send_message(
            "❌ 권한이 없습니다.\n**허용된 역할:** Helper, 비트코인 기업, 비트코인 경제매장",
            ephemeral=True
        )
        return
    # 매장 존재 확인
    if 매장코드 not in stores:
        await interaction.response.send_message("❌ 존재하지 않는 매장 코드입니다.", ephemeral=True)
        return
    
    # 권한 확인
    if stores[매장코드]['owner_id'] != interaction.user.id:
        await interaction.response.send_message("❌ 본인이 생성한 매장만 수정할 수 있습니다.", ephemeral=True)
        return
    
    store = stores[매장코드]
    changes = []
    
    # 변경사항 적용
    if 매장명:
        store['store_name'] = 매장명
        changes.append(f"매장명: {매장명}")
    
    if 최소역할:
        store['min_role_id'] = 최소역할.id
        changes.append(f"최소역할: {최소역할.mention}")
    
    if 부여역할:
        store['grant_role_id'] = 부여역할.id
        changes.append(f"부여역할: {부여역할.mention}")
    
    if 암구호 is not None:
        if 암구호 == "":
            store['passphrase'] = None
            changes.append("암구호: 제거됨")
        else:
            store['passphrase'] = 암구호
            changes.append("암구호: 변경됨")
    
    if not changes:
        await interaction.response.send_message("❌ 변경할 내용이 없습니다.", ephemeral=True)
        return
    
    store['updated_at'] = datetime.now().isoformat()
    save_stores(stores)
    
    embed = discord.Embed(
        title="✅ 매장 정보 수정 완료",
        description=f"**매장**: {store['store_name']}\n**코드**: `{매장코드}`",
        color=discord.Color.green()
    )
    embed.add_field(name="변경사항", value="\n".join(changes), inline=False)
    embed.set_footer(text="QR 코드는 그대로 유지되며, 다음 인증부터 새 조건이 적용됩니다.")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 암구호 대기 상태 저장
passphrase_waiting = {}

# 3. 입장 인증 (방문자용)
@bot.tree.command(name="입장", description="매장 입장 인증")
@app_commands.describe(매장코드="QR 코드의 매장 코드")
async def verify_entry(interaction: discord.Interaction, 매장코드: str):
    # 매장 존재 확인
    if 매장코드 not in stores:
        embed = discord.Embed(
            title="❌ 입장 불가",
            description="유효하지 않은 매장 코드입니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    store = stores[매장코드]
    guild = bot.get_guild(store['guild_id'])
    
    # 중복 입장 체크
    if 'approved_users' not in store:
        store['approved_users'] = []
    
    if interaction.user.id in store['approved_users']:
        embed = discord.Embed(
            title="✅ 이미 입장 처리가 완료되었습니다",
            description=f"**{store['store_name']}**\n\n이미 입장 승인을 받으셨습니다.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # 서버 가입 확인
    member = guild.get_member(interaction.user.id)
    if not member:
        embed = discord.Embed(
            title="❌ 입장 불가",
            description=f"**{store['store_name']}**\n\n디스코드 서버에 먼저 가입해주세요.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 매장주에게 알림
        try:
            owner = await bot.fetch_user(store['owner_id'])
            notify_embed = discord.Embed(
                title="⚠️ 입장 거부",
                description=f"**매장**: {store['store_name']}\n**시도자**: {interaction.user.name}",
                color=discord.Color.orange()
            )
            notify_embed.add_field(name="사유", value="서버 미가입")
            await owner.send(embed=notify_embed)
        except:
            pass
        
        return
    
    # 역할 확인
    if store['min_role_id']:
        min_role = guild.get_role(store['min_role_id'])
        has_role = any(role >= min_role for role in member.roles)
    else:
        # 최소 역할이 없으면 모두 통과
        has_role = True
        min_role = None
    
    # 사용자 역할 목록
    user_roles = [role.name for role in member.roles if role.name != "@everyone"]
    
    # 역할 미달이면 무조건 거부 (최소 역할이 설정된 경우만)
    if store['min_role_id'] and not has_role:
        embed = discord.Embed(
            title="❌ 입장 거부",
            description=f"**{store['store_name']}**\n\n입장이 거부되었습니다.",
            color=discord.Color.red()
        )
        embed.add_field(name="거부 사유", value="역할 미달", inline=False)
        embed.add_field(name="필요 조건", value=f"{min_role.name} 이상 역할 필수", inline=False)
        if user_roles:
            embed.add_field(name="현재 보유 역할", value=", ".join(user_roles), inline=False)
        else:
            embed.add_field(name="현재 보유 역할", value="없음", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 매장주에게 알림
        try:
            owner = await bot.fetch_user(store['owner_id'])
            notify_embed = discord.Embed(
                title="⚠️ 입장 거부",
                description=f"**매장**: {store['store_name']}\n**시도자**: {interaction.user.name}",
                color=discord.Color.orange()
            )
            notify_embed.add_field(name="거부 사유", value="역할 미달", inline=False)
            if user_roles:
                notify_embed.add_field(name="보유 역할", value=", ".join(user_roles), inline=False)
            else:
                notify_embed.add_field(name="보유 역할", value="없음", inline=False)
            await owner.send(embed=notify_embed)
        except:
            pass
        
        return
    
    # 역할 충족 ✅
    # 암구호 없으면 바로 승인
    if not store['passphrase']:
        # ✅ 바로 승인
        role_granted = False
        if store['grant_role_id']:
            grant_role = guild.get_role(store['grant_role_id'])
            if grant_role and grant_role not in member.roles:
                try:
                    await member.add_roles(grant_role)
                    role_granted = True
                except:
                    pass
        
        embed = discord.Embed(
            title="✅ 입장 승인",
            description=f"**{store['store_name']}**\n\n입장이 승인되었습니다!",
            color=discord.Color.green()
        )
        embed.add_field(name="승인 사유", value="역할 조건 충족", inline=False)
        if role_granted:
            embed.add_field(name="역할 부여", value=f"{grant_role.mention} 역할이 부여되었습니다", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 승인된 사용자 목록에 추가
        if 'approved_users' not in store:
            store['approved_users'] = []
        store['approved_users'].append(interaction.user.id)
        save_stores(stores)
        
        # 매장주에게 알림
        try:
            owner = await bot.fetch_user(store['owner_id'])
            notify_embed = discord.Embed(
                title="✅ 입장 승인",
                description=f"**매장**: {store['store_name']}\n**방문자**: {interaction.user.name}",
                color=discord.Color.green()
            )
            notify_embed.add_field(name="승인 경로", value="역할 조건 충족 (암구호 없음)", inline=False)
            if user_roles:
                notify_embed.add_field(name="보유 역할", value=", ".join(user_roles), inline=False)
            if role_granted:
                notify_embed.add_field(name="역할 부여", value=f"{grant_role.name} 부여됨", inline=False)
            await owner.send(embed=notify_embed)
        except:
            pass
        
        return
    
    # 역할 있고 + 암구호 설정됨 → DM으로 암구호 요청
    # 대기 상태 저장
    passphrase_waiting[interaction.user.id] = {
        'store_code': 매장코드,
        'has_role': has_role,
        'user_roles': user_roles
    }
    
    # 서버 채널에 응답
    embed = discord.Embed(
        title="🔐 암구호 입력 필요",
        description=f"**{store['store_name']}**\n\nDM으로 암구호 입력 요청을 보냈습니다.\nDM을 확인해주세요.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # DM 전송
    try:
        dm_embed = discord.Embed(
            title=f"🔐 {store['store_name']} - 암구호 입력",
            description="역할 조건을 충족했습니다.\n\n마지막으로 암구호를 입력해주세요.\n암구호를 일반 메시지로 보내주시면 됩니다.",
            color=discord.Color.blue()
        )
        
        await interaction.user.send(embed=dm_embed)
    except discord.Forbidden:
        # DM 차단된 경우
        error_embed = discord.Embed(
            title="❌ DM 전송 실패",
            description="DM이 차단되어 있습니다.\n디스코드 설정에서 DM을 허용해주세요.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)
        del passphrase_waiting[interaction.user.id]

# DM 메시지 처리
@bot.event
async def on_message(message):
    # 봇 자신의 메시지 무시
    if message.author.bot:
        return
    
    # DM이 아니면 무시
    if message.guild is not None:
        return
    
    # 암구호 대기 중인 사용자인지 확인
    if message.author.id not in passphrase_waiting:
        return
    
    waiting_data = passphrase_waiting[message.author.id]
    store_code = waiting_data['store_code']
    has_role = waiting_data['has_role']
    user_roles = waiting_data['user_roles']
    
    # 매장 정보 가져오기
    if store_code not in stores:
        await message.reply("❌ 매장 정보를 찾을 수 없습니다. 다시 시도해주세요.")
        del passphrase_waiting[message.author.id]
        return
    
    store = stores[store_code]
    guild = bot.get_guild(store['guild_id'])
    member = guild.get_member(message.author.id)
    
    # 암구호 확인 (역할 있는 경우만 이 단계까지 옴)
    passphrase_correct = (message.content == store['passphrase'])
    
    if passphrase_correct:
        # ✅ 승인 (역할 있고 암구호 일치)
        # 부여 역할 처리
        role_granted = False
        if store['grant_role_id']:
            grant_role = guild.get_role(store['grant_role_id'])
            if grant_role and grant_role not in member.roles:
                try:
                    await member.add_roles(grant_role)
                    role_granted = True
                except:
                    pass
        
        # 방문자에게 메시지
        embed = discord.Embed(
            title="✅ 입장 승인",
            description=f"**{store['store_name']}**\n\n입장이 승인되었습니다!",
            color=discord.Color.green()
        )
        embed.add_field(name="승인 사유", value="역할 조건 충족 & 암구호 정답", inline=False)
        if role_granted:
            embed.add_field(name="역할 부여", value=f"{grant_role.name} 역할이 부여되었습니다", inline=False)
        
        await message.reply(embed=embed)
        
        # 승인된 사용자 목록에 추가
        if 'approved_users' not in store:
            store['approved_users'] = []
        store['approved_users'].append(message.author.id)
        save_stores(stores)
        
        # 매장주에게 알림
        try:
            owner = await bot.fetch_user(store['owner_id'])
            notify_embed = discord.Embed(
                title="✅ 입장 승인",
                description=f"**매장**: {store['store_name']}\n**방문자**: {message.author.name}",
                color=discord.Color.green()
            )
            notify_embed.add_field(name="승인 경로", value="역할 조건 충족 & 암구호 정답", inline=False)
            if user_roles:
                notify_embed.add_field(name="보유 역할", value=", ".join(user_roles), inline=False)
            if role_granted:
                notify_embed.add_field(name="역할 부여", value=f"{grant_role.name} 부여됨", inline=False)
            await owner.send(embed=notify_embed)
        except:
            pass
        
    else:
        # ❌ 거부 (역할 있지만 암구호 불일치)
        embed = discord.Embed(
            title="❌ 입장 거부",
            description=f"**{store['store_name']}**\n\n입장이 거부되었습니다.",
            color=discord.Color.red()
        )
        embed.add_field(name="거부 사유", value="암구호 불일치", inline=False)
        embed.add_field(name="참고", value="역할 조건은 충족했으나 암구호가 일치하지 않습니다.", inline=False)
        
        await message.reply(embed=embed)
        
        # 매장주에게 알림
        try:
            owner = await bot.fetch_user(store['owner_id'])
            notify_embed = discord.Embed(
                title="⚠️ 입장 거부",
                description=f"**매장**: {store['store_name']}\n**시도자**: {message.author.name}",
                color=discord.Color.orange()
            )
            notify_embed.add_field(name="거부 사유", value="암구호 불일치", inline=False)
            if user_roles:
                notify_embed.add_field(name="보유 역할", value=", ".join(user_roles), inline=False)
            await owner.send(embed=notify_embed)
        except:
            pass
    
    # 대기 상태 제거
    del passphrase_waiting[message.author.id]

# 4. 매장 목록
@bot.tree.command(name="매장목록", description="내가 생성한 매장 목록 보기")
async def list_stores(interaction: discord.Interaction):
    # 권한 확인
    if not has_allowed_role(interaction):
        await interaction.response.send_message(
            "❌ 권한이 없습니다.\n**허용된 역할:** Helper, 비트코인 기업, 비트코인 경제매장",
            ephemeral=True
        )
        return
    my_stores = {k: v for k, v in stores.items() if v['owner_id'] == interaction.user.id}
    
    if not my_stores:
        await interaction.response.send_message("생성한 매장이 없습니다.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📋 내 매장 목록",
        color=discord.Color.blue()
    )
    
    for code, store in my_stores.items():
        guild = bot.get_guild(store['guild_id'])
        min_role = guild.get_role(store['min_role_id']) if guild and store['min_role_id'] else None
        grant_role = guild.get_role(store['grant_role_id']) if guild and store['grant_role_id'] else None
        
        value_text = f"**코드**: `{code}`\n"
        if min_role:
            value_text += f"**최소역할**: {min_role.name}\n"
        else:
            value_text += f"**최소역할**: 없음 (모두 입장 가능)\n"
        if grant_role:
            value_text += f"**부여역할**: {grant_role.name}\n"
        if store['passphrase']:
            value_text += f"**암구호**: 설정됨\n"
        
        embed.add_field(
            name=f"🏪 {store['store_name']}",
            value=value_text,
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 5. 매장 삭제
@bot.tree.command(name="매장삭제", description="매장 QR 삭제")
@app_commands.describe(매장코드="삭제할 매장의 코드")
async def delete_store(interaction: discord.Interaction, 매장코드: str):
    # 권한 확인
    if not has_allowed_role(interaction):
        await interaction.response.send_message(
            "❌ 권한이 없습니다.\n**허용된 역할:** Helper, 비트코인 기업, 비트코인 경제매장",
            ephemeral=True
        )
        return
    if 매장코드 not in stores:
        await interaction.response.send_message("❌ 존재하지 않는 매장 코드입니다.", ephemeral=True)
        return
    
    if stores[매장코드]['owner_id'] != interaction.user.id:
        await interaction.response.send_message("❌ 본인이 생성한 매장만 삭제할 수 있습니다.", ephemeral=True)
        return
    
    store_name = stores[매장코드]['store_name']
    
    # QR 이미지 삭제
    qr_path = os.path.join(QR_DIR, f"store_{매장코드}.png")
    if os.path.exists(qr_path):
        os.remove(qr_path)
    
    # 데이터 삭제
    del stores[매장코드]
    save_stores(stores)
    
    await interaction.response.send_message(f"✅ '{store_name}' 매장이 삭제되었습니다.", ephemeral=True)

# 봇 실행
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if not TOKEN:
        print("❌ .env 파일에 DISCORD_TOKEN을 설정해주세요!")
        import sys
        sys.exit(1)
    
    bot.run(TOKEN)
