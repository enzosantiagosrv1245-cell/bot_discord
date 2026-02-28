import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#                    🤖 DEV BOT - MAIN FILE
# ═══════════════════════════════════════════════════════════════

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

def get_prefix(bot, message):
    """Prefixo dinâmico por servidor"""
    try:
        with open('data/prefixes.json', 'r') as f:
            prefixes = json.load(f)
        return prefixes.get(str(message.guild.id), config['prefix'])
    except:
        return config['prefix']

# Intents necessárias
intents = discord.Intents.all()

# Inicializa o bot
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# ═══════════════════════════════════════════════════════════════
#                         EVENTOS
# ═══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                     🤖 DEV BOT ONLINE                        ║
╠══════════════════════════════════════════════════════════════╣
║  Bot: {bot.user.name}#{bot.user.discriminator}
║  ID: {bot.user.id}
║  Servidores: {len(bot.guilds)}
║  Prefixo: {config['prefix']}
║  Discord.py: {discord.__version__}
╚══════════════════════════════════════════════════════════════╝
    """)
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config['prefix']}help | Tickets"
        ),
        status=discord.Status.online
    )

    # Criar pastas necessárias
    os.makedirs('data', exist_ok=True)
    os.makedirs('cogs', exist_ok=True)
    
    # Criar arquivos de dados se não existirem
    for file in ['tickets.json', 'warnings.json', 'blacklist.json', 'prefixes.json']:
        filepath = f'data/{file}'
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump({}, f)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Sem Permissão",
            description="Você não tem permissão para usar este comando.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Argumento Faltando",
            description=f"Use: `{ctx.prefix}help {ctx.command.name}` para ver como usar.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
    elif isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            title="❌ Apenas Dono",
            description="Apenas o dono do bot pode usar este comando.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
    else:
        print(f"Erro: {error}")

# ═══════════════════════════════════════════════════════════════
#                    CARREGAR COGS
# ═══════════════════════════════════════════════════════════════

async def load_cogs():
    cogs = ['cogs.tickets', 'cogs.moderation', 'cogs.developer', 'cogs.utilities', 'cogs.owner']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog carregada: {cog}")
        except Exception as e:
            print(f"❌ Erro ao carregar {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(config['token'])

if __name__ == "__main__":
    asyncio.run(main())