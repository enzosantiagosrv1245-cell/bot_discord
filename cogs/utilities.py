import discord
from discord.ext import commands
from discord import ui
from datetime import datetime
import asyncio
import random

# ═══════════════════════════════════════════════════════════════
#                   📊 UTILIDADES GERAIS
# ═══════════════════════════════════════════════════════════════

class EmbedModal(ui.Modal, title="Criar Embed"):
    titulo = ui.TextInput(label="Título", placeholder="Título da embed", required=False)
    descricao = ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, required=True)
    cor = ui.TextInput(label="Cor (hex)", placeholder="#5865F2", required=False, max_length=7)
    imagem = ui.TextInput(label="URL da Imagem", required=False)
    thumbnail = ui.TextInput(label="URL do Thumbnail", required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            color = int(self.cor.value.strip('#'), 16) if self.cor.value else 0x5865F2
        except:
            color = 0x5865F2
        
        embed = discord.Embed(
            title=self.titulo.value or None,
            description=self.descricao.value,
            color=discord.Color(color)
        )
        
        if self.imagem.value:
            embed.set_image(url=self.imagem.value)
        if self.thumbnail.value:
            embed.set_thumbnail(url=self.thumbnail.value)
        
        await interaction.response.send_message(embed=embed)

class UtilitiesCog(commands.Cog, name="Utilidades"):
    """Comandos utilitários gerais"""
    
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Verificar se mencionou alguém AFK
        for mention in message.mentions:
            if mention.id in self.afk_users:
                data = self.afk_users[mention.id]
                await message.channel.send(
                    f"💤 {mention.name} está AFK: {data['reason']}\n"
                    f"*Desde: <t:{int(data['since'].timestamp())}:R>*",
                    delete_after=10
                )
        
        # Verificar se o autor estava AFK
        if message.author.id in self.afk_users:
            del self.afk_users[message.author.id]
            await message.channel.send(
                f"👋 Bem-vindo de volta, {message.author.mention}! Seu AFK foi removido.",
                delete_after=5
            )
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Mostra a latência do bot"""
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latência: **{round(self.bot.latency * 1000)}ms**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo', aliases=['si'])
    async def serverinfo(self, ctx):
        """Informações do servidor"""
        
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            description=guild.description or "Sem descrição",
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 Criado em", value=guild.created_at.strftime('%d/%m/%Y'), inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        
        embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Canais", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Cargos", value=len(guild.roles), inline=True)
        
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="🎨 Stickers", value=len(guild.stickers), inline=True)
        embed.add_field(name="🔊 Boost Level", value=guild.premium_tier, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['ui', 'whois'])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Informações de um usuário"""
        
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member}",
            color=member.top_role.color,
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📛 Nick", value=member.nick or "Nenhum", inline=True)
        embed.add_field(name="🤖 Bot", value="Sim" if member.bot else "Não", inline=True)
        
        embed.add_field(
            name="📅 Conta Criada",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="📥 Entrou no Servidor",
            value=f"<t:{int(member.joined_at.timestamp())}:R>",
            inline=True
        )
        
        roles = [r.mention for r in member.roles[1:][:10]]
        embed.add_field(
            name=f"🎭 Cargos [{len(member.roles) - 1}]",
            value=" ".join(roles) if roles else "Nenhum",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='avatar', aliases=['av'])
    async def avatar(self, ctx, member: discord.Member = None):
        """Mostra o avatar de um usuário"""
        
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ Avatar de {member.name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=member.display_avatar.url)
        
        # Botões com diferentes formatos
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="PNG", url=member.display_avatar.with_format('png').url))
        view.add_item(discord.ui.Button(label="JPG", url=member.display_avatar.with_format('jpg').url))
        view.add_item(discord.ui.Button(label="WEBP", url=member.display_avatar.with_format('webp').url))
        
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='banner')
    async def banner(self, ctx, member: discord.Member = None):
        """Mostra o banner de um usuário"""
        
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        
        if not user.banner:
            await ctx.send("❌ Este usuário não tem banner!")
            return
        
        embed = discord.Embed(
            title=f"🖼️ Banner de {member.name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=user.banner.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roleinfo', aliases=['ri'])
    async def roleinfo(self, ctx, role: discord.Role):
        """Informações de um cargo"""
        
        embed = discord.Embed(
            title=f"🎭 {role.name}",
            color=role.color
        )
        
        embed.add_field(name="🆔 ID", value=role.id, inline=True)
        embed.add_field(name="🎨 Cor", value=str(role.color), inline=True)
        embed.add_field(name="📍 Posição", value=role.position, inline=True)
        embed.add_field(name="👥 Membros", value=len(role.members), inline=True)
        embed.add_field(name="📢 Mencionável", value="Sim" if role.mentionable else "Não", inline=True)
        embed.add_field(name="🔝 Destacado", value="Sim" if role.hoist else "Não", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='embed')
    async def create_embed(self, ctx):
        """Cria uma embed customizada (abre modal)"""
        
        modal = EmbedModal()
        # Note: Modal precisa de interaction, vamos usar um botão
        
        view = discord.ui.View()
        button = discord.ui.Button(label="Criar Embed", style=discord.ButtonStyle.primary)
        
        async def button_callback(interaction):
            await interaction.response.send_modal(modal)
        
        button.callback = button_callback
        view.add_item(button)
        
        await ctx.send("Clique no botão para criar uma embed:", view=view)
    
    @commands.command(name='poll', aliases=['enquete'])
    async def poll(self, ctx, *, pergunta: str):
        """Cria uma enquete"""
        
        embed = discord.Embed(
            title="📊 Enquete",
            description=pergunta,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Enquete por {ctx.author}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await msg.add_reaction("🤷")
    
    @commands.command(name='giveaway', aliases=['sorteio'])
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, tempo: str, *, premio: str):
        """Cria um sorteio"""
        
        import re
        time_match = re.match(r'(\d+)([smhd])', tempo)
        if not time_match:
            await ctx.send("❌ Formato de tempo inválido! Use: 10s, 10m, 1h, 1d")
            return
        
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = amount * units[unit]
        
        end_time = int((datetime.now().timestamp()) + seconds)
        
        embed = discord.Embed(
            title="🎉 SORTEIO!",
            description=f"**Prêmio:** {premio}\n\nReaja com 🎉 para participar!\n\n⏰ Termina: <t:{end_time}:R>",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Criado por {ctx.author}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")
        
        await asyncio.sleep(seconds)
        
        # Buscar mensagem atualizada
        msg = await ctx.channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        
        if reaction and reaction.count > 1:
            users = [user async for user in reaction.users() if not user.bot]
            if users:
                winner = random.choice(users)
                
                embed = discord.Embed(
                    title="🎉 SORTEIO ENCERRADO!",
                    description=f"**Prêmio:** {premio}\n\n🏆 **Vencedor:** {winner.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
        
        await ctx.send("❌ Sorteio cancelado - sem participantes suficientes!")
    
    @commands.command(name='remind', aliases=['lembrete'])
    async def remind(self, ctx, tempo: str, *, mensagem: str):
        """Define um lembrete"""
        
        import re
        time_match = re.match(r'(\d+)([smhd])', tempo)
        if not time_match:
            await ctx.send("❌ Formato de tempo inválido! Use: 10s, 10m, 1h, 1d")
            return
        
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = amount * units[unit]
        
        await ctx.send(f"✅ Lembrete definido para **{tempo}**!")
        
        await asyncio.sleep(seconds)
        await ctx.author.send(f"⏰ **Lembrete:** {mensagem}")
        await ctx.channel.send(f"⏰ {ctx.author.mention}, lembrete: **{mensagem}**")
    
    @commands.command(name='afk')
    async def afk(self, ctx, *, motivo: str = "AFK"):
        """Define status AFK"""
        
        self.afk_users[ctx.author.id] = {
            'reason': motivo,
            'since': datetime.now()
        }
        
        await ctx.send(f"💤 {ctx.author.mention} está agora AFK: **{motivo}**")
    
    @commands.command(name='botinfo')
    async def botinfo(self, ctx):
        """Informações do bot"""
        
        embed = discord.Embed(
            title="🤖 DevBot Info",
            description="Bot de tickets e utilidades para desenvolvedores",
            color=discord.Color.blurple(),
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name="📊 Servidores", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 Usuários", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.add_field(name="🏓 Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        embed.add_field(name="💻 Discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="🔧 Python", value="3.11+", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='invite', aliases=['convite'])
    async def invite(self, ctx):
        """Link de convite do bot"""
        
        link = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        
        embed = discord.Embed(
            title="🔗 Convite do Bot",
            description=f"[Clique aqui para me adicionar!]({link})",
            color=discord.Color.blurple()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilitiesCog(bot))