import discord
from discord.ext import commands
import json
import traceback
import io
import textwrap
from contextlib import redirect_stdout

# ═══════════════════════════════════════════════════════════════
#                   👑 COMANDOS DO DONO
# ═══════════════════════════════════════════════════════════════

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

class OwnerCog(commands.Cog, name="Dono"):
    """Comandos exclusivos do dono do servidor/bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
    
    def is_owner_check():
        """Verifica se é dono do bot ou do servidor"""
        async def predicate(ctx):
            config = load_config()
            is_bot_owner = ctx.author.id in config.get('owner_ids', [])
            is_guild_owner = ctx.author == ctx.guild.owner
            return is_bot_owner or is_guild_owner
        return commands.check(predicate)
    
    @commands.command(name='falar', aliases=['say', 'speak'])
    @is_owner_check()
    async def falar(self, ctx, canal: discord.TextChannel = None, *, mensagem: str = None):
        """Faz o bot falar uma mensagem"""
        
        # Detectar se primeiro argumento é canal
        if canal is None and mensagem is None:
            await ctx.send("❌ Use: `falar [#canal] <mensagem>`")
            return
        
        if mensagem is None:
            # Não foi especificado canal, usar atual
            mensagem = str(canal.id) if isinstance(canal, discord.TextChannel) else str(canal)
            canal = ctx.channel
            # Reconstruir mensagem
            args = ctx.message.content.split(maxsplit=1)
            if len(args) > 1:
                mensagem = args[1]
        
        # Deletar comando se possível
        try:
            await ctx.message.delete()
        except:
            pass
        
        await canal.send(mensagem)
    
    @commands.command(name='falearembed', aliases=['sayembed'])
    @is_owner_check()
    async def falar_embed(self, ctx, canal: discord.TextChannel = None, *, mensagem: str):
        """Faz o bot falar uma mensagem em embed"""
        
        if canal is None:
            canal = ctx.channel
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        embed = discord.Embed(
            description=mensagem,
            color=discord.Color.blurple()
        )
        
        await canal.send(embed=embed)
    
    @commands.command(name='setprefix')
    @is_owner_check()
    async def set_prefix(self, ctx, novo_prefixo: str):
        """Altera o prefixo do bot"""
        
        if len(novo_prefixo) > 10:
            await ctx.send("❌ Prefixo muito longo! Máximo 10 caracteres.")
            return
        
        # Salvar em prefixes.json por servidor
        try:
            with open('data/prefixes.json', 'r') as f:
                prefixes = json.load(f)
        except:
            prefixes = {}
        
        prefixes[str(ctx.guild.id)] = novo_prefixo
        
        with open('data/prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)
        
        embed = discord.Embed(
            title="✅ Prefixo Alterado",
            description=f"Novo prefixo: `{novo_prefixo}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='eval')
    @commands.is_owner()
    async def eval_code(self, ctx, *, code: str):
        """Executa código Python (apenas dono do bot)"""
        
        # Remover code blocks
        if code.startswith('```') and code.endswith('```'):
            code = code[3:-3]
            if code.startswith('py\n'):
                code = code[3:]
            elif code.startswith('python\n'):
                code = code[7:]
        
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result,
            'discord': discord,
            'commands': commands
        }
        env.update(globals())
        
        stdout = io.StringIO()
        
        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'
        
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
        
        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            
            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
                else:
                    await ctx.message.add_reaction('✅')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')
    
    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        """Recarrega uma cog"""
        
        try:
            await self.bot.reload_extension(f'cogs.{cog}')
            await ctx.send(f"✅ Cog `{cog}` recarregada!")
        except Exception as e:
            await ctx.send(f"❌ Erro: {e}")
    
    @commands.command(name='shutdown', aliases=['desligar'])
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Desliga o bot"""
        
        await ctx.send("👋 Desligando...")
        await self.bot.close()
    
    @commands.command(name='setstatus')
    @is_owner_check()
    async def set_status(self, ctx, tipo: str, *, texto: str):
        """Define o status do bot"""
        
        tipos = {
            'playing': discord.ActivityType.playing,
            'watching': discord.ActivityType.watching,
            'listening': discord.ActivityType.listening,
            'streaming': discord.ActivityType.streaming,
            'competing': discord.ActivityType.competing
        }
        
        tipo_lower = tipo.lower()
        if tipo_lower not in tipos:
            await ctx.send(f"❌ Tipos disponíveis: {', '.join(tipos.keys())}")
            return
        
        activity = discord.Activity(type=tipos[tipo_lower], name=texto)
        await self.bot.change_presence(activity=activity)
        
        await ctx.send(f"✅ Status alterado para: **{tipo}** {texto}")
    
    @commands.command(name='dm')
    @is_owner_check()
    async def dm_user(self, ctx, user: discord.User, *, mensagem: str):
        """Envia DM para um usuário"""
        
        try:
            await user.send(mensagem)
            await ctx.send(f"✅ Mensagem enviada para {user}!")
        except:
            await ctx.send("❌ Não foi possível enviar DM para este usuário!")
    
    @commands.command(name='announce', aliases=['anunciar'])
    @is_owner_check()
    async def announce(self, ctx, canal: discord.TextChannel, *, mensagem: str):
        """Envia um anúncio em um canal"""
        
        embed = discord.Embed(
            title="📢 Anúncio",
            description=mensagem,
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Por {ctx.author}")
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        await canal.send("@everyone", embed=embed)
        await ctx.send(f"✅ Anúncio enviado em {canal.mention}!", delete_after=5)
    
    @commands.command(name='addowner')
    @commands.is_owner()
    async def add_owner(self, ctx, user: discord.User):
        """Adiciona um dono ao bot"""
        
        config = load_config()
        
        if user.id in config.get('owner_ids', []):
            await ctx.send("❌ Este usuário já é dono!")
            return
        
        if 'owner_ids' not in config:
            config['owner_ids'] = []
        
        config['owner_ids'].append(user.id)
        save_config(config)
        
        await ctx.send(f"✅ {user} foi adicionado como dono!")
    
    @commands.command(name='removeowner')
    @commands.is_owner()
    async def remove_owner(self, ctx, user: discord.User):
        """Remove um dono do bot"""
        
        config = load_config()
        
        if user.id not in config.get('owner_ids', []):
            await ctx.send("❌ Este usuário não é dono!")
            return
        
        config['owner_ids'].remove(user.id)
        save_config(config)
        
        await ctx.send(f"✅ {user} foi removido dos donos!")

# Importar datetime que faltou
from datetime import datetime

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))