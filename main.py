import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from aiohttp import web

# ═══════════════════════════════════════════════════════════════
#                    🤖 DEV BOT - MAIN FILE
#                   Sistema de Tickets com IA
# ═══════════════════════════════════════════════════════════════

# Carregar variáveis de ambiente
load_dotenv()

def load_config():
    """Carrega configuração com suporte a variáveis de ambiente"""
    config = {
        "token": os.getenv('DISCORD_TOKEN'),
        "prefix": os.getenv('BOT_PREFIX', 'dev!'),
        "owner_ids": [],
        "staff_role_id": None,
        "log_channel_id": None,
        "ticket_category_id": None,
        "ai_enabled": os.getenv('AI_ENABLED', 'true').lower() == 'true',
        "auto_close_minutes": int(os.getenv('AUTO_CLOSE_MINUTES', '60'))
    }
    
    # Owner IDs (separados por vírgula)
    owner_ids_env = os.getenv('OWNER_IDS', '')
    if owner_ids_env:
        try:
            config['owner_ids'] = [int(id.strip()) for id in owner_ids_env.split(',') if id.strip()]
        except ValueError:
            print("⚠️  OWNER_IDS inválido, usando padrão")
            config['owner_ids'] = []
    
    # Tentar carregar do arquivo local (para desenvolvimento)
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Variáveis de ambiente têm prioridade
                if not config['token']:
                    config['token'] = file_config.get('token')
                if not config['owner_ids']:
                    config['owner_ids'] = file_config.get('owner_ids', [])
                # Outras configs do arquivo
                for key in ['staff_role_id', 'log_channel_id', 'ticket_category_id']:
                    if key in file_config and file_config[key]:
                        config[key] = file_config[key]
        except Exception as e:
            print(f"⚠️  Erro ao carregar config.json: {e}")
    
    # Validar token
    if not config['token']:
        raise ValueError(
            "❌ Token do Discord não encontrado!\n"
            "Configure DISCORD_TOKEN nas variáveis de ambiente ou em config.json"
        )
    
    return config

def save_config(config):
    """Salva configuração no arquivo JSON (apenas local)"""
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Erro ao salvar config.json: {e}")

config = load_config()

def get_prefix(bot, message):
    """Prefixo dinâmico por servidor"""
    if not message.guild:
        return config['prefix']
    
    try:
        with open('data/prefixes.json', 'r', encoding='utf-8') as f:
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
#                    HEALTH CHECK SERVER (RENDER)
# ═══════════════════════════════════════════════════════════════

async def health_check(request):
    """Endpoint de health check para manter o bot ativo"""
    uptime = datetime.now() - bot.start_time if hasattr(bot, 'start_time') else 'N/A'
    return web.json_response({
        'status': 'online',
        'bot': bot.user.name if bot.user else 'Not ready',
        'uptime': str(uptime),
        'guilds': len(bot.guilds),
        'latency': round(bot.latency * 1000, 2)
    })

async def start_health_server():
    """Inicia servidor HTTP para health checks"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.getenv('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Health check server running on port {port}")

# ═══════════════════════════════════════════════════════════════
#                         KEEP ALIVE TASK
# ═══════════════════════════════════════════════════════════════

@tasks.loop(minutes=10)
async def keep_alive():
    """Mantém o bot ativo com ping periódico"""
    print(f"🔄 Keep alive ping - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Latency: {round(bot.latency * 1000)}ms")

@keep_alive.before_loop
async def before_keep_alive():
    """Aguarda o bot estar pronto antes de iniciar keep alive"""
    await bot.wait_until_ready()

# ═══════════════════════════════════════════════════════════════
#                         EVENTOS
# ═══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    """Evento quando o bot está pronto"""
    bot.start_time = datetime.now()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                     🤖 DEV BOT ONLINE                        ║
╠══════════════════════════════════════════════════════════════╣
║  Bot: {bot.user.name}#{bot.user.discriminator}
║  ID: {bot.user.id}
║  Servidores: {len(bot.guilds)}
║  Usuários: {sum(g.member_count for g in bot.guilds)}
║  Prefixo: {config['prefix']}
║  Discord.py: {discord.__version__}
║  Ambiente: {'PRODUÇÃO' if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER') else 'LOCAL'}
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Definir status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config['prefix']}help | {len(bot.guilds)} servidores"
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
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print(f"✅ Criado: {filepath}")
    
    # Iniciar health check server (para Render/Railway)
    if os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT'):
        asyncio.create_task(start_health_server())
        print("🌐 Health check server iniciado")
    
    # Iniciar keep alive task
    if not keep_alive.is_running():
        keep_alive.start()
        print("🔄 Keep alive task iniciado")
    
    print(f"\n✅ Bot pronto e operacional!")
    print(f"🌍 Convite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands\n")

@bot.event
async def on_guild_join(guild):
    """Evento quando o bot entra em um servidor"""
    print(f"➕ Entrei no servidor: {guild.name} (ID: {guild.id}) - {guild.member_count} membros")
    
    # Atualizar status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config['prefix']}help | {len(bot.guilds)} servidores"
        )
    )
    
    # Enviar mensagem de boas-vindas
    try:
        # Tentar encontrar canal de sistema
        channel = guild.system_channel or guild.text_channels[0]
        
        embed = discord.Embed(
            title="👋 Obrigado por me adicionar!",
            description=f"""
Olá! Eu sou o **{bot.user.name}**, um bot completo de tickets e moderação para desenvolvedores.

**🚀 Começando:**
• Use `{config['prefix']}help` para ver todos os comandos
• Use `{config['prefix']}setup` para configurar o sistema de tickets
• Configure o cargo de staff com `{config['prefix']}setstaff @cargo`

**📚 Recursos:**
• Sistema de tickets com IA
• Comandos de moderação
• Ferramentas para desenvolvedores
• Utilidades gerais

**🔗 Links Úteis:**
• [Documentação](#) | [Suporte](#) | [Convite](#)
            """,
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(text=f"Prefixo: {config['prefix']}")
        
        await channel.send(embed=embed)
    except:
        pass

@bot.event
async def on_guild_remove(guild):
    """Evento quando o bot sai de um servidor"""
    print(f"➖ Saí do servidor: {guild.name} (ID: {guild.id})")
    
    # Atualizar status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config['prefix']}help | {len(bot.guilds)} servidores"
        )
    )

@bot.event
async def on_command_error(ctx, error):
    """Handler global de erros"""
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
    
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            title="❌ Bot Sem Permissão",
            description=f"Preciso das seguintes permissões:\n{', '.join(error.missing_permissions)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
    
    elif isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏰ Cooldown",
            description=f"Aguarde {error.retry_after:.1f}s antes de usar este comando novamente.",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed, delete_after=10)
    
    else:
        print(f"❌ Erro no comando {ctx.command}: {error}")
        
        embed = discord.Embed(
            title="❌ Erro Inesperado",
            description=f"Ocorreu um erro ao executar o comando.\n```{str(error)[:200]}```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=15)

@bot.event
async def on_error(event, *args, **kwargs):
    """Handler global de erros de eventos"""
    import traceback
    print(f"❌ Erro no evento {event}:")
    traceback.print_exc()

# ═══════════════════════════════════════════════════════════════
#                    COMANDO DE AJUDA CUSTOMIZADO
# ═══════════════════════════════════════════════════════════════

@bot.command(name='help', aliases=['ajuda', 'comandos'])
async def help_command(ctx, comando: str = None):
    """Mostra todos os comandos disponíveis"""
    
    if comando:
        # Ajuda de comando específico
        cmd = bot.get_command(comando)
        if not cmd:
            await ctx.send(f"❌ Comando `{comando}` não encontrado!")
            return
        
        embed = discord.Embed(
            title=f"📖 Comando: {cmd.name}",
            description=cmd.help or "Sem descrição",
            color=discord.Color.blurple()
        )
        
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in cmd.aliases))
        
        usage = f"{ctx.prefix}{cmd.name} {cmd.signature}"
        embed.add_field(name="Uso", value=f"`{usage}`", inline=False)
        
        await ctx.send(embed=embed)
        return
    
    # Lista de comandos
    embed = discord.Embed(
        title="📚 Central de Comandos",
        description=f"Use `{ctx.prefix}help <comando>` para mais informações sobre um comando específico.",
        color=discord.Color.blurple(),
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    # Agrupar comandos por cog
    for cog_name, cog in bot.cogs.items():
        commands_list = [cmd for cmd in cog.get_commands() if not cmd.hidden]
        if commands_list:
            commands_text = ", ".join(f"`{cmd.name}`" for cmd in commands_list[:10])
            if len(commands_list) > 10:
                commands_text += f" *+{len(commands_list) - 10} mais*"
            embed.add_field(
                name=f"{cog_name}",
                value=commands_text,
                inline=False
            )
    
    # Comandos sem cog
    no_cog = [cmd for cmd in bot.commands if not cmd.cog and not cmd.hidden]
    if no_cog:
        commands_text = ", ".join(f"`{cmd.name}`" for cmd in no_cog)
        embed.add_field(name="Outros", value=commands_text, inline=False)
    
    embed.set_footer(text=f"Total de comandos: {len([c for c in bot.commands if not c.hidden])}")
    
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════════════
#                    CARREGAR COGS
# ═══════════════════════════════════════════════════════════════

async def load_cogs():
    """Carrega todas as cogs do bot"""
    cogs = ['tickets', 'moderation', 'developer', 'utilities', 'owner']
    
    for cog in cogs:
        try:
            await bot.load_extension(f'cogs.{cog}')
            print(f"✅ Cog carregada: {cog}")
        except Exception as e:
            print(f"❌ Erro ao carregar {cog}: {e}")
            import traceback
            traceback.print_exc()

# ═══════════════════════════════════════════════════════════════
#                    INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════

async def main():
    """Função principal para iniciar o bot"""
    async with bot:
        # Carregar cogs
        await load_cogs()
        
        # Iniciar bot
        try:
            print("🚀 Iniciando bot...")
            await bot.start(config['token'])
        except discord.LoginFailure:
            print("❌ Token inválido! Verifique DISCORD_TOKEN nas variáveis de ambiente.")
        except Exception as e:
            print(f"❌ Erro ao iniciar bot: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot desligado manualmente")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()