import discord
from discord.ext import commands
from datetime import datetime
import json
import base64
import hashlib
import re
import aiohttp

# ═══════════════════════════════════════════════════════════════
#                💻 COMANDOS PARA DESENVOLVEDORES
# ═══════════════════════════════════════════════════════════════

class DeveloperCog(commands.Cog, name="Desenvolvedor"):
    """Comandos úteis para desenvolvedores"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='code')
    async def code_block(self, ctx, linguagem: str, *, codigo: str):
        """Formata código com syntax highlighting"""
        
        embed = discord.Embed(
            title=f"💻 Código ({linguagem.upper()})",
            description=f"```{linguagem}\n{codigo}\n```",
            color=discord.Color.dark_gray()
        )
        embed.set_footer(text=f"Enviado por {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name='docs')
    async def docs(self, ctx, linguagem: str = None):
        """Links para documentações populares"""
        
        docs = {
            'python': 'https://docs.python.org/3/',
            'javascript': 'https://developer.mozilla.org/pt-BR/docs/Web/JavaScript',
            'java': 'https://docs.oracle.com/en/java/',
            'csharp': 'https://docs.microsoft.com/pt-br/dotnet/csharp/',
            'rust': 'https://doc.rust-lang.org/book/',
            'go': 'https://golang.org/doc/',
            'typescript': 'https://www.typescriptlang.org/docs/',
            'php': 'https://www.php.net/docs.php',
            'ruby': 'https://ruby-doc.org/',
            'cpp': 'https://en.cppreference.com/w/',
            'discordpy': 'https://discordpy.readthedocs.io/en/stable/',
            'discordjs': 'https://discord.js.org/#/docs/',
            'react': 'https://reactjs.org/docs/',
            'vue': 'https://vuejs.org/v2/guide/',
            'nodejs': 'https://nodejs.org/docs/',
            'docker': 'https://docs.docker.com/',
            'git': 'https://git-scm.com/doc',
            'mongodb': 'https://docs.mongodb.com/',
            'postgresql': 'https://www.postgresql.org/docs/',
        }
        
        if not linguagem:
            embed = discord.Embed(
                title="📚 Documentações Disponíveis",
                description="\n".join([f"• `{lang}`" for lang in sorted(docs.keys())]),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        linguagem_lower = linguagem.lower()
        if linguagem_lower in docs:
            embed = discord.Embed(
                title=f"📚 Documentação - {linguagem.upper()}",
                description=f"[Clique aqui para acessar]({docs[linguagem_lower]})",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Documentação para `{linguagem}` não encontrada!")
    
    @commands.command(name='github', aliases=['gh'])
    async def github(self, ctx, repo: str):
        """Mostra informações de um repositório GitHub"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.github.com/repos/{repo}") as response:
                    if response.status != 200:
                        await ctx.send("❌ Repositório não encontrado!")
                        return
                    
                    data = await response.json()
            
            embed = discord.Embed(
                title=f"📦 {data['full_name']}",
                description=data.get('description', 'Sem descrição'),
                url=data['html_url'],
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="⭐ Stars", value=data['stargazers_count'], inline=True)
            embed.add_field(name="🍴 Forks", value=data['forks_count'], inline=True)
            embed.add_field(name="👁️ Watchers", value=data['watchers_count'], inline=True)
            embed.add_field(name="💻 Linguagem", value=data.get('language', 'N/A'), inline=True)
            embed.add_field(name="📄 Licença", value=data.get('license', {}).get('name', 'N/A'), inline=True)
            embed.add_field(name="🐛 Issues", value=data['open_issues_count'], inline=True)
            
            if data.get('owner', {}).get('avatar_url'):
                embed.set_thumbnail(url=data['owner']['avatar_url'])
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar repositório: {e}")
    
    @commands.command(name='regex')
    async def regex_test(self, ctx, padrao: str, *, texto: str):
        """Testa uma expressão regular"""
        
        try:
            pattern = re.compile(padrao)
            matches = pattern.findall(texto)
            
            embed = discord.Embed(
                title="🔍 Resultado do Regex",
                color=discord.Color.green() if matches else discord.Color.red()
            )
            embed.add_field(name="Padrão", value=f"`{padrao}`", inline=False)
            embed.add_field(name="Texto", value=f"```{texto}```", inline=False)
            
            if matches:
                embed.add_field(
                    name=f"✅ Matches ({len(matches)})",
                    value=f"```{matches}```",
                    inline=False
                )
            else:
                embed.add_field(name="❌ Resultado", value="Nenhum match encontrado", inline=False)
            
            await ctx.send(embed=embed)
        except re.error as e:
            await ctx.send(f"❌ Regex inválido: {e}")
    
    @commands.command(name='json')
    async def json_format(self, ctx, *, json_string: str):
        """Formata e valida JSON"""
        
        # Remover code blocks se houver
        json_string = json_string.strip('`').strip()
        if json_string.startswith('json'):
            json_string = json_string[4:].strip()
        
        try:
            parsed = json.loads(json_string)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ JSON Válido",
                description=f"```json\n{formatted[:1900]}\n```",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except json.JSONDecodeError as e:
            embed = discord.Embed(
                title="❌ JSON Inválido",
                description=f"Erro: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='base64')
    async def base64_convert(self, ctx, modo: str, *, texto: str):
        """Codifica/decodifica Base64"""
        
        modo = modo.lower()
        
        if modo == 'encode':
            result = base64.b64encode(texto.encode()).decode()
            title = "🔒 Base64 Encoded"
        elif modo == 'decode':
            try:
                result = base64.b64decode(texto.encode()).decode()
                title = "🔓 Base64 Decoded"
            except:
                await ctx.send("❌ String Base64 inválida!")
                return
        else:
            await ctx.send("❌ Use: `encode` ou `decode`")
            return
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Input", value=f"```{texto[:500]}```", inline=False)
        embed.add_field(name="Output", value=f"```{result[:500]}```", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='hash')
    async def hash_text(self, ctx, algoritmo: str, *, texto: str):
        """Gera hash de um texto"""
        
        algoritmo = algoritmo.lower()
        
        hashes = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512,
        }
        
        if algoritmo not in hashes:
            await ctx.send(f"❌ Algoritmos disponíveis: {', '.join(hashes.keys())}")
            return
        
        result = hashes[algoritmo](texto.encode()).hexdigest()
        
        embed = discord.Embed(
            title=f"🔐 Hash {algoritmo.upper()}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Input", value=f"```{texto[:200]}```", inline=False)
        embed.add_field(name="Hash", value=f"```{result}```", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='color', aliases=['cor'])
    async def color_preview(self, ctx, hex_color: str):
        """Mostra preview de uma cor"""
        
        # Remover # se houver
        hex_color = hex_color.strip('#')
        
        try:
            color_int = int(hex_color, 16)
            
            # Calcular RGB
            r = (color_int >> 16) & 255
            g = (color_int >> 8) & 255
            b = color_int & 255
            
            embed = discord.Embed(
                title="🎨 Preview de Cor",
                description=f"Cor: **#{hex_color.upper()}**",
                color=discord.Color(color_int)
            )
            embed.add_field(name="HEX", value=f"`#{hex_color.upper()}`", inline=True)
            embed.add_field(name="RGB", value=f"`rgb({r}, {g}, {b})`", inline=True)
            embed.add_field(name="Decimal", value=f"`{color_int}`", inline=True)
            
            # Imagem colorida via API
            embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_color}/100x100")
            
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("❌ Cor hexadecimal inválida!")
    
    @commands.command(name='ascii')
    async def ascii_art(self, ctx, *, texto: str):
        """Converte texto para ASCII art"""
        
        if len(texto) > 10:
            await ctx.send("❌ Máximo 10 caracteres!")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://artii.herokuapp.com/make?text={texto}") as response:
                    if response.status == 200:
                        art = await response.text()
                        await ctx.send(f"```\n{art}\n```")
                    else:
                        await ctx.send("❌ Erro ao gerar ASCII art!")
        except:
            # Fallback simples
            await ctx.send(f"```\n{texto.upper()}\n```")
    
    @commands.command(name='timestamp')
    async def timestamp(self, ctx, timestamp: int = None):
        """Converte timestamp Unix para data legível"""
        
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            embed = discord.Embed(
                title="⏰ Timestamp",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Unix", value=f"`{timestamp}`", inline=True)
            embed.add_field(name="Data", value=dt.strftime('%d/%m/%Y %H:%M:%S'), inline=True)
            embed.add_field(name="Discord", value=f"<t:{timestamp}:F>", inline=False)
        else:
            now = int(datetime.now().timestamp())
            embed = discord.Embed(
                title="⏰ Timestamp Atual",
                description=f"```{now}```",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Discord", value=f"<t:{now}:F>", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='calc')
    async def calculator(self, ctx, *, expressao: str):
        """Calculadora simples"""
        
        # Apenas permitir caracteres matemáticos seguros
        allowed = set('0123456789+-*/.() ')
        if not all(c in allowed for c in expressao):
            await ctx.send("❌ Expressão inválida!")
            return
        
        try:
            result = eval(expressao)
            embed = discord.Embed(
                title="🔢 Calculadora",
                color=discord.Color.green()
            )
            embed.add_field(name="Expressão", value=f"`{expressao}`", inline=False)
            embed.add_field(name="Resultado", value=f"```{result}```", inline=False)
            await ctx.send(embed=embed)
        except:
            await ctx.send("❌ Erro ao calcular!")
    
    @commands.command(name='lorem')
    async def lorem_ipsum(self, ctx, paragrafos: int = 1):
        """Gera texto Lorem Ipsum"""
        
        if paragrafos > 5:
            paragrafos = 5
        
        lorem = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."""
        
        text = "\n\n".join([lorem for _ in range(paragrafos)])
        
        embed = discord.Embed(
            title="📝 Lorem Ipsum",
            description=text[:2000],
            color=discord.Color.light_gray()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DeveloperCog(bot))