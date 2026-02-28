import discord
from discord.ext import commands
from discord import ui
import json
import asyncio
from datetime import datetime, timedelta
import re

# ═══════════════════════════════════════════════════════════════
#                   🎫 SISTEMA DE TICKETS
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

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

# ═══════════════════════════════════════════════════════════════
#                      IA DE TICKETS
# ═══════════════════════════════════════════════════════════════

class TicketAI:
    """Sistema de IA para análise de mensagens em tickets"""
    
    # Padrões de mensagens inúteis
    USELESS_PATTERNS = [
        r'^[a-z]{1,3}$',                    # Mensagens muito curtas (1-3 letras)
        r'^(.)\1{4,}$',                     # Letras repetidas (aaaaa)
        r'^[!@#$%^&*()]+$',                 # Apenas símbolos
        r'^(oi|ola|hello|hi|hey)$',         # Apenas saudação sem contexto
        r'^(teste|test|testing)$',          # Testes
        r'^(.)$',                           # Apenas 1 caractere
        r'^[\s]+$',                         # Apenas espaços
        r'^(kk+|haha+|rs+|lol+)$',          # Apenas risadas
        r'^(kkkkk|hahaha|rsrsrs)+$',        # Risadas repetidas
        r'(.)\1{7,}',                       # Mais de 7 caracteres iguais seguidos
        r'^[0-9]{1,2}$',                    # Apenas 1-2 números
    ]
    
    # Respostas automáticas para perguntas frequentes
    FAQ_RESPONSES = {
        'como faço parceria': 'Para parcerias, descreva seu servidor/projeto, quantidade de membros e benefícios mútuos. Um staff irá analisar sua proposta.',
        'quanto tempo': 'O tempo de resposta varia. Staff disponível atenderá em breve. Aguarde pacientemente.',
        'ninguém responde': 'Nossa equipe atende quando disponível. Se for urgente, mencione a prioridade do seu ticket.',
        'posso ser staff': 'Vagas de staff são anunciadas quando disponíveis. Fique atento aos anúncios do servidor.',
        'preciso de ajuda': 'Descreva detalhadamente sua dúvida ou problema para que possamos ajudá-lo melhor.',
    }
    
    # Palavras-chave para detectar spam
    SPAM_KEYWORDS = ['free nitro', 'discord nitro grátis', 'clique aqui', 'link suspeito']
    
    @classmethod
    def analyze_message(cls, content: str) -> dict:
        """
        Analisa uma mensagem e retorna informações sobre ela
        Returns: {
            'is_useless': bool,
            'reason': str,
            'auto_response': str or None,
            'should_warn': bool,
            'should_close': bool,
            'spam_score': int
        }
        """
        content_lower = content.lower().strip()
        result = {
            'is_useless': False,
            'reason': None,
            'auto_response': None,
            'should_warn': False,
            'should_close': False,
            'spam_score': 0
        }
        
        # Verificar se é muito curta (menos de 5 caracteres)
        if len(content_lower) < 5:
            result['is_useless'] = True
            result['reason'] = 'Mensagem muito curta'
            result['should_warn'] = True
            return result
        
        # Verificar padrões de mensagens inúteis
        for pattern in cls.USELESS_PATTERNS:
            if re.match(pattern, content_lower, re.IGNORECASE):
                result['is_useless'] = True
                result['reason'] = 'Mensagem detectada como inútil'
                result['should_warn'] = True
                return result
        
        # Verificar spam
        for keyword in cls.SPAM_KEYWORDS:
            if keyword in content_lower:
                result['spam_score'] += 30
        
        if result['spam_score'] >= 30:
            result['is_useless'] = True
            result['reason'] = 'Possível spam detectado'
            result['should_close'] = True
            return result
        
        # Verificar se há resposta automática disponível
        for trigger, response in cls.FAQ_RESPONSES.items():
            if trigger in content_lower:
                result['auto_response'] = response
                break
        
        return result
    
    @classmethod
    def get_warning_message(cls, reason: str) -> str:
        """Retorna mensagem de aviso baseada no motivo"""
        warnings = {
            'Mensagem muito curta': '⚠️ Sua mensagem é muito curta. Por favor, descreva seu problema/dúvida detalhadamente.',
            'Mensagem detectada como inútil': '⚠️ Por favor, envie mensagens relevantes ao seu ticket. Mensagens sem sentido podem resultar no fechamento automático.',
            'Possível spam detectado': '🚫 Spam detectado! Este ticket será fechado automaticamente.',
        }
        return warnings.get(reason, '⚠️ Por favor, envie mensagens apropriadas.')

# ═══════════════════════════════════════════════════════════════
#                   VIEWS E BOTÕES
# ═══════════════════════════════════════════════════════════════

class TicketTypeSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="📢 Denúncia",
                description="Denunciar usuário ou comportamento",
                value="denuncia",
                emoji="📢"
            ),
            discord.SelectOption(
                label="❓ Dúvida",
                description="Tirar dúvidas sobre o servidor",
                value="duvida",
                emoji="❓"
            ),
            discord.SelectOption(
                label="🤝 Parceria",
                description="Proposta de parceria",
                value="parceria",
                emoji="🤝"
            ),
            discord.SelectOption(
                label="💡 Sugestão",
                description="Sugerir melhorias",
                value="sugestao",
                emoji="💡"
            ),
            discord.SelectOption(
                label="🐛 Bug Report",
                description="Reportar bugs/erros",
                value="bug",
                emoji="🐛"
            ),
            discord.SelectOption(
                label="💼 Candidatura Staff",
                description="Aplicar para staff",
                value="staff",
                emoji="💼"
            ),
            discord.SelectOption(
                label="🔧 Suporte Técnico",
                description="Ajuda com problemas técnicos",
                value="suporte",
                emoji="🔧"
            ),
            discord.SelectOption(
                label="📦 Outros",
                description="Outros assuntos",
                value="outros",
                emoji="📦"
            ),
        ]
        super().__init__(
            placeholder="🎫 Selecione o tipo de ticket...",
            options=options,
            custom_id="ticket_type_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await create_ticket(interaction, self.values[0])

class TicketPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

class TicketControlView(ui.View):
    def __init__(self, ticket_id: str):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔒 Fechando Ticket",
            description="Este ticket será fechado em 5 segundos...",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        
        await asyncio.sleep(5)
        await interaction.channel.delete()
    
    @ui.button(label="👤 Atender Ticket", style=discord.ButtonStyle.green, custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: ui.Button):
        config = load_config()
        staff_role_id = config.get('staff_role_id')
        
        # Verificar se tem cargo de staff
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role not in interaction.user.roles:
                await interaction.response.send_message(
                    "❌ Você não tem permissão para atender tickets!",
                    ephemeral=True
                )
                return
        
        tickets = load_data('tickets.json')
        ticket_data = tickets.get(str(interaction.channel.id), {})
        
        if ticket_data.get('claimed_by'):
            await interaction.response.send_message(
                f"❌ Este ticket já está sendo atendido por <@{ticket_data['claimed_by']}>!",
                ephemeral=True
            )
            return
        
        # Atualizar dados do ticket
        ticket_data['claimed_by'] = interaction.user.id
        ticket_data['claimed_at'] = datetime.now().isoformat()
        tickets[str(interaction.channel.id)] = ticket_data
        save_data('tickets.json', tickets)
        
        # Atualizar permissões - apenas quem atendeu pode falar
        await interaction.channel.set_permissions(
            interaction.user,
            send_messages=True,
            read_messages=True,
            manage_channels=True,
            manage_messages=True
        )
        
        # Remover permissão de outros staffs falarem (apenas ler)
        if staff_role_id:
            staff_role = interaction.guild.get_role(staff_role_id)
            if staff_role:
                await interaction.channel.set_permissions(
                    staff_role,
                    send_messages=False,
                    read_messages=True
                )
        
        embed = discord.Embed(
            title="👤 Ticket Atendido",
            description=f"Este ticket está sendo atendido por {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Staff Responsável", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Desabilitar botão de atender
        button.disabled = True
        button.label = f"✅ Atendido por {interaction.user.name}"
        await interaction.message.edit(view=self)
    
    @ui.button(label="📝 Transcrição", style=discord.ButtonStyle.secondary, custom_id="transcript_ticket")
    async def transcript_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        messages = []
        async for message in interaction.channel.history(limit=500, oldest_first=True):
            timestamp = message.created_at.strftime("%d/%m/%Y %H:%M")
            content = message.content or "[Embed/Arquivo]"
            messages.append(f"[{timestamp}] {message.author}: {content}")
        
        transcript = "\n".join(messages)
        
        # Criar arquivo
        filename = f"transcript-{interaction.channel.name}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== TRANSCRIÇÃO DO TICKET ===\n")
            f.write(f"Canal: {interaction.channel.name}\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Total de mensagens: {len(messages)}\n")
            f.write(f"{'='*50}\n\n")
            f.write(transcript)
        
        await interaction.followup.send(
            "📝 Transcrição gerada!",
            file=discord.File(filename),
            ephemeral=True
        )
        
        # Remover arquivo temporário
        import os
        os.remove(filename)

# ═══════════════════════════════════════════════════════════════
#                   FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════

async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    """Cria um novo ticket"""
    
    config = load_config()
    blacklist = load_data('blacklist.json')
    tickets = load_data('tickets.json')
    
    # Verificar blacklist
    if str(interaction.user.id) in blacklist.get(str(interaction.guild.id), []):
        await interaction.response.send_message(
            "❌ Você está bloqueado de abrir tickets!",
            ephemeral=True
        )
        return
    
    # Verificar se já tem ticket aberto
    for channel_id, data in tickets.items():
        if data.get('user_id') == interaction.user.id and data.get('guild_id') == interaction.guild.id:
            channel = interaction.guild.get_channel(int(channel_id))
            if channel:
                await interaction.response.send_message(
                    f"❌ Você já tem um ticket aberto: {channel.mention}",
                    ephemeral=True
                )
                return
    
    await interaction.response.defer(ephemeral=True)
    
    # Tipos de ticket e configurações
    ticket_types = {
        'denuncia': {'emoji': '📢', 'color': discord.Color.red(), 'name': 'Denúncia'},
        'duvida': {'emoji': '❓', 'color': discord.Color.blue(), 'name': 'Dúvida'},
        'parceria': {'emoji': '🤝', 'color': discord.Color.purple(), 'name': 'Parceria'},
        'sugestao': {'emoji': '💡', 'color': discord.Color.gold(), 'name': 'Sugestão'},
        'bug': {'emoji': '🐛', 'color': discord.Color.orange(), 'name': 'Bug Report'},
        'staff': {'emoji': '💼', 'color': discord.Color.green(), 'name': 'Candidatura Staff'},
        'suporte': {'emoji': '🔧', 'color': discord.Color.greyple(), 'name': 'Suporte Técnico'},
        'outros': {'emoji': '📦', 'color': discord.Color.dark_gray(), 'name': 'Outros'},
    }
    
    ticket_config = ticket_types.get(ticket_type, ticket_types['outros'])
    
    # Criar canal do ticket
    category_id = config.get('ticket_category_id')
    category = interaction.guild.get_channel(category_id) if category_id else None
    
    ticket_name = f"{ticket_config['emoji']}-{ticket_type}-{interaction.user.name}"
    
    # Configurar permissões
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            attach_files=True,
            embed_links=True
        ),
        interaction.guild.me: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True
        )
    }
    
    # Adicionar permissão para staff (apenas ler até atender)
    staff_role_id = config.get('staff_role_id')
    if staff_role_id:
        staff_role = interaction.guild.get_role(staff_role_id)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
    
    # Criar canal
    ticket_channel = await interaction.guild.create_text_channel(
        name=ticket_name,
        category=category,
        overwrites=overwrites,
        topic=f"Ticket de {interaction.user} | Tipo: {ticket_config['name']}"
    )
    
    # Salvar dados do ticket
    tickets[str(ticket_channel.id)] = {
        'user_id': interaction.user.id,
        'guild_id': interaction.guild.id,
        'type': ticket_type,
        'created_at': datetime.now().isoformat(),
        'claimed_by': None,
        'claimed_at': None,
        'priority': 'normal',
        'warnings': 0
    }
    save_data('tickets.json', tickets)
    
    # Embed inicial do ticket
    embed = discord.Embed(
        title=f"{ticket_config['emoji']} Ticket - {ticket_config['name']}",
        description=f"""
Bem-vindo ao seu ticket, {interaction.user.mention}!

**📋 Tipo:** {ticket_config['name']}
**👤 Criado por:** {interaction.user.mention}
**📅 Data:** {datetime.now().strftime('%d/%m/%Y às %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📝 Instruções:**
• Descreva seu problema/solicitação detalhadamente
• Aguarde um staff atender seu ticket
• Não faça spam ou envie mensagens sem sentido
• O ticket pode ser fechado automaticamente por inatividade

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
        color=ticket_config['color'],
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Ticket ID: {ticket_channel.id}")
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    # View com controles
    view = TicketControlView(str(ticket_channel.id))
    
    await ticket_channel.send(
        content=f"{interaction.user.mention} | Staff: <@&{staff_role_id}>" if staff_role_id else interaction.user.mention,
        embed=embed,
        view=view
    )
    
    # Mensagem de confirmação
    await interaction.followup.send(
        f"✅ Ticket criado com sucesso: {ticket_channel.mention}",
        ephemeral=True
    )
    
    # Log
    log_channel_id = config.get('log_channel_id')
    if log_channel_id:
        log_channel = interaction.guild.get_channel(log_channel_id)
        if log_channel:
            log_embed = discord.Embed(
                title="🎫 Novo Ticket Criado",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="Usuário", value=interaction.user.mention, inline=True)
            log_embed.add_field(name="Tipo", value=ticket_config['name'], inline=True)
            log_embed.add_field(name="Canal", value=ticket_channel.mention, inline=True)
            await log_channel.send(embed=log_embed)

# ═══════════════════════════════════════════════════════════════
#                      COG PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class TicketsCog(commands.Cog, name="Tickets"):
    """Sistema completo de tickets"""
    
    def __init__(self, bot):
        self.bot = bot
        self.useless_message_count = {}  # Contador de mensagens inúteis por usuário
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Registrar views persistentes
        self.bot.add_view(TicketPanelView())
        
        # Registrar views de tickets existentes
        tickets = load_data('tickets.json')
        for ticket_id in tickets:
            self.bot.add_view(TicketControlView(ticket_id))
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """IA que analisa mensagens nos tickets"""
        if message.author.bot:
            return
        
        config = load_config()
        if not config.get('ai_enabled', True):
            return
        
        tickets = load_data('tickets.json')
        
        # Verificar se é um canal de ticket
        if str(message.channel.id) not in tickets:
            return
        
        ticket_data = tickets[str(message.channel.id)]
        
        # Se for staff que atendeu, não analisar
        if ticket_data.get('claimed_by') == message.author.id:
            return
        
        # Analisar mensagem
        analysis = TicketAI.analyze_message(message.content)
        
        # Se for mensagem inútil
        if analysis['is_useless']:
            # Incrementar contador
            user_id = str(message.author.id)
            if user_id not in self.useless_message_count:
                self.useless_message_count[user_id] = 0
            self.useless_message_count[user_id] += 1
            
            # Enviar aviso
            warning_msg = TicketAI.get_warning_message(analysis['reason'])
            warning_embed = discord.Embed(
                title="⚠️ Aviso Automático",
                description=warning_msg,
                color=discord.Color.yellow()
            )
            warning_embed.set_footer(text=f"Avisos: {self.useless_message_count[user_id]}/3")
            await message.channel.send(embed=warning_embed, delete_after=15)
            
            # Atualizar warnings no ticket
            ticket_data['warnings'] = self.useless_message_count.get(user_id, 0)
            tickets[str(message.channel.id)] = ticket_data
            save_data('tickets.json', tickets)
            
            # Fechar automaticamente se muitos avisos ou spam
            if analysis['should_close'] or self.useless_message_count[user_id] >= 3:
                embed = discord.Embed(
                    title="🚫 Ticket Fechado Automaticamente",
                    description="Este ticket foi fechado devido a múltiplas mensagens inúteis/spam.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                await asyncio.sleep(5)
                
                # Log
                log_channel_id = config.get('log_channel_id')
                if log_channel_id:
                    log_channel = message.guild.get_channel(log_channel_id)
                    if log_channel:
                        log_embed = discord.Embed(
                            title="🚫 Ticket Fechado (IA)",
                            description=f"Ticket fechado automaticamente por {analysis['reason']}",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        log_embed.add_field(name="Usuário", value=message.author.mention)
                        log_embed.add_field(name="Motivo", value=analysis['reason'])
                        await log_channel.send(embed=log_embed)
                
                # Remover dos dados
                del tickets[str(message.channel.id)]
                save_data('tickets.json', tickets)
                
                await message.channel.delete()
                return
        
        # Resposta automática se disponível
        if analysis['auto_response']:
            embed = discord.Embed(
                title="🤖 Resposta Automática",
                description=analysis['auto_response'],
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Esta é uma resposta automática. Um staff irá atendê-lo em breve.")
            await message.channel.send(embed=embed)
    
    @commands.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        """Configura o sistema de tickets"""
        
        embed = discord.Embed(
            title="🎫 Central de Atendimento",
            description="""
Bem-vindo à nossa central de tickets!

**📋 Como funciona:**
1. Selecione o tipo de ticket no menu abaixo
2. Um canal privado será criado para você
3. Descreva seu problema/solicitação
4. Aguarde um staff atendê-lo

**🎯 Tipos de Ticket:**
• 📢 **Denúncia** - Denunciar usuários
• ❓ **Dúvida** - Tirar dúvidas
• 🤝 **Parceria** - Propostas de parceria
• 💡 **Sugestão** - Sugerir melhorias
• 🐛 **Bug Report** - Reportar bugs
• 💼 **Candidatura Staff** - Aplicar para staff
• 🔧 **Suporte Técnico** - Problemas técnicos
• 📦 **Outros** - Outros assuntos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """,
            color=discord.Color.blurple()
        )
        embed.set_footer(text="DevBot • Sistema de Tickets")
        
        view = TicketPanelView()
        await ctx.send(embed=embed, view=view)
        
        # Tentar deletar comando
        try:
            await ctx.message.delete()
        except:
            pass
    
    @commands.command(name='fechar', aliases=['close'])
    async def close_ticket(self, ctx, *, motivo: str = "Não especificado"):
        """Fecha o ticket atual"""
        
        tickets = load_data('tickets.json')
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        config = load_config()
        
        # Verificar permissão
        is_owner = ticket_data['user_id'] == ctx.author.id
        is_staff = ticket_data.get('claimed_by') == ctx.author.id
        is_admin = ctx.author.guild_permissions.administrator
        
        if not (is_owner or is_staff or is_admin):
            await ctx.send("❌ Você não tem permissão para fechar este ticket!")
            return
        
        embed = discord.Embed(
            title="🔒 Fechando Ticket",
            description=f"**Motivo:** {motivo}\n\nEste ticket será fechado em 5 segundos...",
            color=discord.Color.red()
        )
        embed.add_field(name="Fechado por", value=ctx.author.mention)
        await ctx.send(embed=embed)
        
        await asyncio.sleep(5)
        
        # Log
        log_channel_id = config.get('log_channel_id')
        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)
            if log_channel:
                user = ctx.guild.get_member(ticket_data['user_id'])
                log_embed = discord.Embed(
                    title="🔒 Ticket Fechado",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="Usuário", value=user.mention if user else "Desconhecido")
                log_embed.add_field(name="Fechado por", value=ctx.author.mention)
                log_embed.add_field(name="Motivo", value=motivo, inline=False)
                await log_channel.send(embed=log_embed)
        
        # Remover dos dados
        del tickets[str(ctx.channel.id)]
        save_data('tickets.json', tickets)
        
        await ctx.channel.delete()
    
    @commands.command(name='claim', aliases=['atender'])
    async def claim_ticket(self, ctx):
        """Reivindica o ticket para atender"""
        
        tickets = load_data('tickets.json')
        config = load_config()
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        
        # Verificar cargo de staff
        staff_role_id = config.get('staff_role_id')
        if staff_role_id:
            staff_role = ctx.guild.get_role(staff_role_id)
            if staff_role not in ctx.author.roles and not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Você não tem permissão para atender tickets!")
                return
        
        if ticket_data.get('claimed_by'):
            await ctx.send(f"❌ Este ticket já está sendo atendido por <@{ticket_data['claimed_by']}>!")
            return
        
        # Atualizar dados
        ticket_data['claimed_by'] = ctx.author.id
        ticket_data['claimed_at'] = datetime.now().isoformat()
        tickets[str(ctx.channel.id)] = ticket_data
        save_data('tickets.json', tickets)
        
        # Atualizar permissões
        await ctx.channel.set_permissions(
            ctx.author,
            send_messages=True,
            read_messages=True,
            manage_channels=True,
            manage_messages=True
        )
        
        # Bloquear outros staffs
        if staff_role_id:
            staff_role = ctx.guild.get_role(staff_role_id)
            if staff_role:
                await ctx.channel.set_permissions(
                    staff_role,
                    send_messages=False,
                    read_messages=True
                )
        
        embed = discord.Embed(
            title="👤 Ticket Atendido",
            description=f"Este ticket agora está sendo atendido por {ctx.author.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unclaim', aliases=['desatender'])
    async def unclaim_ticket(self, ctx):
        """Libera o ticket para outro staff atender"""
        
        tickets = load_data('tickets.json')
        config = load_config()
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        
        if ticket_data.get('claimed_by') != ctx.author.id and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Você não está atendendo este ticket!")
            return
        
        # Atualizar dados
        ticket_data['claimed_by'] = None
        ticket_data['claimed_at'] = None
        tickets[str(ctx.channel.id)] = ticket_data
        save_data('tickets.json', tickets)
        
        # Restaurar permissões de staff
        staff_role_id = config.get('staff_role_id')
        if staff_role_id:
            staff_role = ctx.guild.get_role(staff_role_id)
            if staff_role:
                await ctx.channel.set_permissions(
                    staff_role,
                    send_messages=True,
                    read_messages=True
                )
        
        embed = discord.Embed(
            title="🔄 Ticket Liberado",
            description="Este ticket está disponível para outro staff atender.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='add')
    async def add_user(self, ctx, member: discord.Member):
        """Adiciona um usuário ao ticket"""
        
        tickets = load_data('tickets.json')
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        
        # Verificar permissão
        if ticket_data.get('claimed_by') != ctx.author.id and ticket_data['user_id'] != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Você não tem permissão!")
                return
        
        await ctx.channel.set_permissions(
            member,
            read_messages=True,
            send_messages=True
        )
        
        await ctx.send(f"✅ {member.mention} foi adicionado ao ticket!")
    
    @commands.command(name='remove')
    async def remove_user(self, ctx, member: discord.Member):
        """Remove um usuário do ticket"""
        
        tickets = load_data('tickets.json')
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        
        # Não pode remover o dono do ticket
        if member.id == ticket_data['user_id']:
            await ctx.send("❌ Não é possível remover o dono do ticket!")
            return
        
        # Verificar permissão
        if ticket_data.get('claimed_by') != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Você não tem permissão!")
                return
        
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"✅ {member.mention} foi removido do ticket!")
    
    @commands.command(name='rename')
    async def rename_ticket(self, ctx, *, novo_nome: str):
        """Renomeia o ticket"""
        
        tickets = load_data('tickets.json')
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        
        if ticket_data.get('claimed_by') != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ Você não tem permissão!")
                return
        
        await ctx.channel.edit(name=novo_nome)
        await ctx.send(f"✅ Ticket renomeado para: **{novo_nome}**")
    
    @commands.command(name='transcript')
    async def transcript(self, ctx):
        """Gera transcrição do ticket"""
        
        tickets = load_data('tickets.json')
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        await ctx.send("📝 Gerando transcrição...")
        
        messages = []
        async for message in ctx.channel.history(limit=500, oldest_first=True):
            timestamp = message.created_at.strftime("%d/%m/%Y %H:%M")
            content = message.content or "[Embed/Arquivo]"
            messages.append(f"[{timestamp}] {message.author}: {content}")
        
        transcript = "\n".join(messages)
        
        filename = f"transcript-{ctx.channel.name}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== TRANSCRIÇÃO DO TICKET ===\n")
            f.write(f"Canal: {ctx.channel.name}\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Total de mensagens: {len(messages)}\n")
            f.write(f"{'='*50}\n\n")
            f.write(transcript)
        
        await ctx.send("✅ Transcrição gerada!", file=discord.File(filename))
        
        import os
        os.remove(filename)
    
    @commands.command(name='prioridade')
    async def set_priority(self, ctx, nivel: str):
        """Define prioridade do ticket (alta/media/baixa)"""
        
        tickets = load_data('tickets.json')
        
        if str(ctx.channel.id) not in tickets:
            await ctx.send("❌ Este não é um canal de ticket!")
            return
        
        niveis = {
            'alta': {'emoji': '🔴', 'color': discord.Color.red()},
            'media': {'emoji': '🟡', 'color': discord.Color.yellow()},
            'baixa': {'emoji': '🟢', 'color': discord.Color.green()}
        }
        
        nivel_lower = nivel.lower()
        if nivel_lower not in niveis:
            await ctx.send("❌ Níveis disponíveis: `alta`, `media`, `baixa`")
            return
        
        ticket_data = tickets[str(ctx.channel.id)]
        ticket_data['priority'] = nivel_lower
        tickets[str(ctx.channel.id)] = ticket_data
        save_data('tickets.json', tickets)
        
        config = niveis[nivel_lower]
        embed = discord.Embed(
            title=f"{config['emoji']} Prioridade Definida",
            description=f"Prioridade do ticket: **{nivel.upper()}**",
            color=config['color']
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='setstaff')
    @commands.has_permissions(administrator=True)
    async def set_staff_role(self, ctx, role: discord.Role):
        """Define o cargo de staff para tickets"""
        
        config = load_config()
        config['staff_role_id'] = role.id
        save_config(config)
        
        await ctx.send(f"✅ Cargo de staff definido para: {role.mention}")
    
    @commands.command(name='setlog')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Define o canal de logs de tickets"""
        
        config = load_config()
        config['log_channel_id'] = channel.id
        save_config(config)
        
        await ctx.send(f"✅ Canal de logs definido para: {channel.mention}")
    
    @commands.command(name='setcategory')
    @commands.has_permissions(administrator=True)
    async def set_category(self, ctx, category: discord.CategoryChannel):
        """Define a categoria onde tickets serão criados"""
        
        config = load_config()
        config['ticket_category_id'] = category.id
        save_config(config)
        
        await ctx.send(f"✅ Categoria definida para: **{category.name}**")
    
    @commands.command(name='blacklist')
    @commands.has_permissions(administrator=True)
    async def blacklist_user(self, ctx, member: discord.Member):
        """Bloqueia um usuário de abrir tickets"""
        
        blacklist = load_data('blacklist.json')
        guild_id = str(ctx.guild.id)
        
        if guild_id not in blacklist:
            blacklist[guild_id] = []
        
        if str(member.id) in blacklist[guild_id]:
            await ctx.send(f"❌ {member.mention} já está na blacklist!")
            return
        
        blacklist[guild_id].append(str(member.id))
        save_data('blacklist.json', blacklist)
        
        await ctx.send(f"✅ {member.mention} foi adicionado à blacklist de tickets!")
    
    @commands.command(name='unblacklist')
    @commands.has_permissions(administrator=True)
    async def unblacklist_user(self, ctx, member: discord.Member):
        """Desbloqueia um usuário da blacklist de tickets"""
        
        blacklist = load_data('blacklist.json')
        guild_id = str(ctx.guild.id)
        
        if guild_id not in blacklist or str(member.id) not in blacklist[guild_id]:
            await ctx.send(f"❌ {member.mention} não está na blacklist!")
            return
        
        blacklist[guild_id].remove(str(member.id))
        save_data('blacklist.json', blacklist)
        
        await ctx.send(f"✅ {member.mention} foi removido da blacklist!")
    
    @commands.command(name='toggleai')
    @commands.has_permissions(administrator=True)
    async def toggle_ai(self, ctx):
        """Ativa/desativa a IA de tickets"""
        
        config = load_config()
        config['ai_enabled'] = not config.get('ai_enabled', True)
        save_config(config)
        
        status = "✅ ativada" if config['ai_enabled'] else "❌ desativada"
        await ctx.send(f"IA de tickets foi {status}!")

async def setup(bot):
    await bot.add_cog(TicketsCog(bot))