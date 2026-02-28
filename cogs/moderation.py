import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import asyncio
import re

# ═══════════════════════════════════════════════════════════════
#                   🛡️ SISTEMA DE MODERAÇÃO
# ═══════════════════════════════════════════════════════════════

def load_data(file):
    try:
        with open(f'data/{file}', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(file, data):
    with open(f'data/{file}', 'w') as f:
        json.dump(data, f, indent=4)

class ModerationCog(commands.Cog, name="Moderação"):
    """Comandos de moderação do servidor"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, motivo: str = "Não especificado"):
        """Bane um usuário do servidor"""
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Você não pode banir alguém com cargo igual ou superior!")
            return
        
        try:
            await member.send(f"🔨 Você foi banido de **{ctx.guild.name}**\n**Motivo:** {motivo}")
        except:
            pass
        
        await member.ban(reason=f"{ctx.author}: {motivo}")
        
        embed = discord.Embed(
            title="🔨 Usuário Banido",
            description=f"{member.mention} foi banido do servidor.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Desbane um usuário pelo ID"""
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            
            embed = discord.Embed(
                title="✅ Usuário Desbanido",
                description=f"**{user}** foi desbanido do servidor.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ Usuário não está banido ou ID inválido!")
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, motivo: str = "Não especificado"):
        """Expulsa um usuário do servidor"""
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Você não pode expulsar alguém com cargo igual ou superior!")
            return
        
        try:
            await member.send(f"👢 Você foi expulso de **{ctx.guild.name}**\n**Motivo:** {motivo}")
        except:
            pass
        
        await member.kick(reason=f"{ctx.author}: {motivo}")
        
        embed = discord.Embed(
            title="👢 Usuário Expulso",
            description=f"{member.mention} foi expulso do servidor.",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mute', aliases=['timeout'])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, tempo: str = "10m", *, motivo: str = "Não especificado"):
        """Silencia um usuário (timeout)"""
        
        # Parse tempo
        time_match = re.match(r'(\d+)([smhd])', tempo)
        if not time_match:
            await ctx.send("❌ Formato de tempo inválido! Use: 10s, 10m, 1h, 1d")
            return
        
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        
        units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
        duration = timedelta(**{units[unit]: amount})
        
        if duration > timedelta(days=28):
            await ctx.send("❌ Timeout máximo é de 28 dias!")
            return
        
        await member.timeout(duration, reason=f"{ctx.author}: {motivo}")
        
        embed = discord.Embed(
            title="🔇 Usuário Silenciado",
            description=f"{member.mention} foi silenciado.",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Duração", value=tempo, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unmute', aliases=['untimeout'])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove o silêncio de um usuário"""
        
        await member.timeout(None)
        
        embed = discord.Embed(
            title="🔊 Silêncio Removido",
            description=f"{member.mention} pode falar novamente.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, motivo: str = "Não especificado"):
        """Adverte um usuário"""
        
        warnings = load_data('warnings.json')
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id not in warnings:
            warnings[guild_id] = {}
        if user_id not in warnings[guild_id]:
            warnings[guild_id][user_id] = []
        
        warn_data = {
            'moderator': ctx.author.id,
            'reason': motivo,
            'timestamp': datetime.now().isoformat()
        }
        
        warnings[guild_id][user_id].append(warn_data)
        save_data('warnings.json', warnings)
        
        warn_count = len(warnings[guild_id][user_id])
        
        embed = discord.Embed(
            title="⚠️ Advertência",
            description=f"{member.mention} foi advertido.",
            color=discord.Color.yellow(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Advertências", value=f"{warn_count}/3", inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        
        await ctx.send(embed=embed)
        
        # Punição automática
        if warn_count >= 3:
            await ctx.send(f"🚨 {member.mention} atingiu 3 advertências e será silenciado!")
            await member.timeout(timedelta(hours=24), reason="3 advertências")
    
    @commands.command(name='warnings', aliases=['warns'])
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """Lista advertências de um usuário"""
        
        warnings = load_data('warnings.json')
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        user_warns = warnings.get(guild_id, {}).get(user_id, [])
        
        if not user_warns:
            await ctx.send(f"✅ {member.mention} não tem advertências!")
            return
        
        embed = discord.Embed(
            title=f"⚠️ Advertências de {member.name}",
            color=discord.Color.yellow()
        )
        
        for i, warn in enumerate(user_warns, 1):
            mod = ctx.guild.get_member(warn['moderator'])
            mod_name = mod.name if mod else "Desconhecido"
            embed.add_field(
                name=f"Advertência #{i}",
                value=f"**Motivo:** {warn['reason']}\n**Moderador:** {mod_name}",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(user_warns)}/3")
        await ctx.send(embed=embed)
    
    @commands.command(name='clearwarns')
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """Limpa advertências de um usuário"""
        
        warnings = load_data('warnings.json')
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id in warnings and user_id in warnings[guild_id]:
            del warnings[guild_id][user_id]
            save_data('warnings.json', warnings)
        
        await ctx.send(f"✅ Advertências de {member.mention} foram limpas!")
    
    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Trava um canal"""
        
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        
        embed = discord.Embed(
            title="🔒 Canal Travado",
            description=f"{channel.mention} foi travado.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Destrava um canal"""
        
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        
        embed = discord.Embed(
            title="🔓 Canal Destravado",
            description=f"{channel.mention} foi destravado.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, quantidade: int):
        """Limpa mensagens do canal"""
        
        if quantidade < 1 or quantidade > 100:
            await ctx.send("❌ Quantidade deve ser entre 1 e 100!")
            return
        
        deleted = await ctx.channel.purge(limit=quantidade + 1)
        
        embed = discord.Embed(
            title="🗑️ Mensagens Limpas",
            description=f"**{len(deleted) - 1}** mensagens foram deletadas.",
            color=discord.Color.green()
        )
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, segundos: int):
        """Define modo lento no canal"""
        
        if segundos < 0 or segundos > 21600:
            await ctx.send("❌ Valor deve ser entre 0 e 21600 segundos!")
            return
        
        await ctx.channel.edit(slowmode_delay=segundos)
        
        if segundos == 0:
            await ctx.send("✅ Modo lento desativado!")
        else:
            await ctx.send(f"✅ Modo lento definido para **{segundos}** segundos!")
    
    @commands.command(name='nuke')
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx):
        """Recria o canal (limpa tudo)"""
        
        embed = discord.Embed(
            title="💣 Confirmar Nuke",
            description="Isso irá deletar e recriar o canal, apagando TODAS as mensagens.\nReaja com ✅ para confirmar.",
            color=discord.Color.red()
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                channel = ctx.channel
                new_channel = await channel.clone(reason=f"Nuke por {ctx.author}")
                await channel.delete()
                
                embed = discord.Embed(
                    title="💣 Canal Nukado",
                    description=f"Canal recriado por {ctx.author.mention}",
                    color=discord.Color.red()
                )
                await new_channel.send(embed=embed)
            else:
                await ctx.send("❌ Nuke cancelado!")
        except asyncio.TimeoutError:
            await ctx.send("❌ Tempo esgotado!")

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))