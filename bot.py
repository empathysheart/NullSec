"""
NullSec — Discord Bot
A feature-rich Discord bot for a cybersecurity community.

Features:
- Welcome messages for new members
- Moderation commands (kick, ban, mute, clear)
- Cybersec utility commands (hash, encode, iplookup, whois, genpass, headers)
- Server info and user info
- Fun commands
"""

import discord
from discord import app_commands
from discord.ext import commands
import hashlib
import base64
import binascii
import string
import random
import aiohttp
import datetime
import os
import json
import asyncio
import time
import ssl
import socket
import codecs
import re
from urllib.parse import quote, unquote


# ─── Configuration ───────────────────────────────────────────────
TOKEN = "MTQ4MDA1NDQ4ODI0Mzg5NjU0MQ.Gv04qb.03y7jEQuZ9Beka6ArEt8OhBO-VgVVspyZ0xUDA"
GUILD_ID = 1480054184849182824
PREFIX = "!"
WELCOME_CHANNEL_NAME = "welcome"
LOG_CHANNEL_NAME = "mod-logs"

# Embed colors
COLOR_GREEN = 0x00ff88
COLOR_CYAN = 0x00d4ff
COLOR_RED = 0xff006e
COLOR_PURPLE = 0xa855f7
COLOR_YELLOW = 0xffbd2e


# ─── Bot Setup ───────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ─── Global State ───────────────────────────────────────────────
bot_start_time = time.time()
warnings_db: dict = {}  # {guild_id: {user_id: [reasons]}}

QUIZ_QUESTIONS = [
    {"q": "What does SQL injection exploit?", "options": ["A) XSS filters", "B) Unsanitized database queries", "C) Weak passwords", "D) Open ports"], "ans": "B"},
    {"q": "What port does HTTPS run on by default?", "options": ["A) 80", "B) 22", "C) 443", "D) 8080"], "ans": "C"},
    {"q": "What does ARP stand for?", "options": ["A) Address Resolution Protocol", "B) Application Routing Protocol", "C) Advanced Relay Process", "D) Automated Request Packet"], "ans": "A"},
    {"q": "Which hash algorithm is considered broken?", "options": ["A) SHA-256", "B) SHA-512", "C) MD5", "D) SHA-3"], "ans": "C"},
    {"q": "What is a zero-day vulnerability?", "options": ["A) A bug with no fix available", "B) A firewall rule", "C) An expired SSL cert", "D) A DDoS attack"], "ans": "A"},
    {"q": "What does OSINT stand for?", "options": ["A) Online Security Intelligence", "B) Open Source Intelligence", "C) Operational Software Integration", "D) Output Signal Interface Network"], "ans": "B"},
    {"q": "What type of attack floods a network with traffic?", "options": ["A) Phishing", "B) SQL Injection", "C) DDoS", "D) MITM"], "ans": "C"},
    {"q": "What does VPN stand for?", "options": ["A) Virtual Private Node", "B) Verified Proxy Network", "C) Virtual Private Network", "D) Visual Packet Notifier"], "ans": "C"},
    {"q": "What is a honeypot in cybersecurity?", "options": ["A) A type of malware", "B) A decoy system to lure attackers", "C) A password manager", "D) A firewall rule"], "ans": "B"},
    {"q": "What does CVSS measure?", "options": ["A) Network speed", "B) Firewall strength", "C) Vulnerability severity", "D) Encryption level"], "ans": "C"},
]

HACKER_QUOTES = [
    ("The quieter you become, the more you are able to hear.", "Kali Linux motto"),
    ("Security is always excessive until it's not enough.", "Robbie Sinclair"),
    ("If you think technology can solve your security problems, then you don't understand the problems and you don't understand the technology.", "Bruce Schneier"),
    ("Hackers are breaking the systems for profit. Before, it was about intellectual curiosity and pursuit of knowledge.", "Kevin Mitnick"),
    ("The only truly secure system is one that is powered off, cast in a block of concrete and sealed in a lead-lined room.", "Gene Spafford"),
    ("Privacy is not for the passive.", "Jeffrey Rosen"),
    ("Amateurs hack systems, professionals hack people.", "Bruce Schneier"),
    ("To hack is to be creative with technology.", "Anonymous"),
    ("Every system can be hacked — it's just a matter of time and motivation.", "Unknown"),
    ("The goal of security: reduce risk to acceptable levels.", "Unknown"),
]

DAILY_CHALLENGES = [
    "**Recon Challenge**: Find the technology stack of `nullsec.example.com` using only passive OSINT (Shodan, BuiltWith, etc). What web server, CMS, and CDN does it use?",
    "**Hash Cracking**: The hash `5f4dcc3b5aa765d61d8327deb882cf99` is MD5. What is the plaintext? (No tools, just knowledge!)",
    "**Port Knowledge**: Name 5 services that typically run on ports below 1024. Bonus: which ones are commonly left open by mistake?",
    "**SQL Injection**: Given the query `SELECT * FROM users WHERE name='$input'`, how would you escape it to always return true?",
    "**Network Challenge**: What is the difference between a hub, switch, and router? When would a pentester target each?",
    "**Crypto Challenge**: If I XOR the byte `0x41` with `0x20`, what ASCII character do I get?",
    "**OSINT Challenge**: Using only public information, find the email format used by a company of your choice (e.g. firstname.lastname@company.com).",
    "**Web Security**: What is the difference between stored XSS, reflected XSS, and DOM-based XSS? Give a one-line example of each.",
    "**Forensics**: A file has the magic bytes `FF D8 FF`. What file format is it and how would you verify this?",
    "**Social Engineering**: List 3 red flags that an email might be a phishing attempt.",
]


# ─── Events ─────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"+======================================+")
    print(f"|  NullSec Bot -- Online!               |")
    print(f"|  Logged in as: {bot.user}")
    print(f"|  Servers: {len(bot.guilds)}")
    print(f"+======================================+")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="the network 🔒"
        )
    )

    # Sync slash commands instantly to the specific guild
    guild_obj = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild_obj)
    try:
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"[OK] Synced {len(synced)} slash commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"[X] Failed to sync commands: {e}")


@bot.event
async def on_member_join(member: discord.Member):
    """Send welcome message when a new member joins."""

    # ── Welcome message ───────────────────────────────────────
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    if not channel:
        return

    embed = discord.Embed(
        title="🔐 New Agent Connected!",
        description=(
            f"Welcome to **NullSec**, {member.mention}!\n\n"
            f"🛡️ Check out our channels and introduce yourself.\n"
            f"📚 Read the rules in #rules.\n"
            f"💬 Start chatting in #general-chat.\n\n"
            f"You are member **#{member.guild.member_count}**!"
        ),
        color=COLOR_GREEN,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="NullSec • Stay secure, stay curious")

    await channel.send(embed=embed)


@bot.event
async def on_member_remove(member: discord.Member):
    """Log when a member leaves."""
    channel = discord.utils.get(member.guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel:
        embed = discord.Embed(
            title="👋 Agent Disconnected",
            description=f"**{member.display_name}** has left the server.",
            color=COLOR_RED,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await channel.send(embed=embed)


# ─── Help Command (Paginated) ────────────────────────────────────

HELP_PAGES = [
    {
        "title": "📖 NullSec Bot — Page 1/5",
        "description": "**Core Cybersec Tools**",
        "fields": [
            {
                "name": "🔧 Original Tools",
                "value": (
                    "`/hash` — Hash text (MD5, SHA1, SHA256, SHA512)\n"
                    "`/encode` — Encode/decode Base64, hex, URL, binary\n"
                    "`/iplookup` — Lookup IP geolocation & ISP info\n"
                    "`/whois` — WHOIS domain registration lookup\n"
                    "`/genpass` — Generate a secure random password\n"
                    "`/headers` — Analyze HTTP security headers of a URL"
                ),
                "inline": True
            },
            {
                "name": "🔬 Extended Tools",
                "value": (
                    "`/cve` — Look up a CVE vulnerability by ID\n"
                    "`/subnet` — Calculate subnet info from CIDR\n"
                    "`/port` — Look up what a port number is used for\n"
                    "`/dns` — DNS lookup (A, MX, TXT, NS, CNAME)\n"
                    "`/reverseip` — Reverse IP / PTR DNS lookup\n"
                    "`/convert` — Convert between decimal/hex/binary/octal"
                ),
                "inline": True
            }
        ]
    },
    {
        "title": "📖 NullSec Bot — Page 2/5",
        "description": "**Advanced Cybersec Tools**",
        "fields": [
            {
                "name": "🌐 Network & Recon",
                "value": (
                    "`/ssl` — Check SSL cert info & expiry for a domain\n"
                    "`/robots` — Fetch a site's robots.txt file\n"
                    "`/mac` — Lookup MAC address vendor/manufacturer\n"
                    "`/asn` — Lookup IP or ASN number info\n"
                ),
                "inline": True
            },
            {
                "name": "🔐 Crypto & Code",
                "value": (
                    "`/cipher` — Caesar, ROT13, Atbash, Vigenere cipher\n"
                    "`/regex` — Test a regex pattern against a string\n"
                ),
                "inline": True
            }
        ]
    },
    {
        "title": "📖 NullSec Bot — Page 3/5",
        "description": "**Community & Fun**",
        "fields": [
            {
                "name": "🎮 Fun Commands",
                "value": (
                    "`/quiz` — Random cybersec trivia with A/B/C/D buttons\n"
                    "`/quote` — Get a random hacker/security quote\n"
                    "`/challenge` — Daily rotating cybersec challenge\n"
                    "`/ctftime` — Show upcoming CTF competitions\n"
                ),
                "inline": True
            },
            {
                "name": "📋 Server Management",
                "value": (
                    "`/setup` — Auto-create all channels, roles & categories\n"
                    "`/postrules` — Post server rules in #rules\n"
                    "`/announce` — Post a formatted announcement\n"
                ),
                "inline": True
            }
        ]
    },
    {
        "title": "📖 NullSec Bot — Page 4/5",
        "description": "**Moderation Tools**",
        "fields": [
            {
                "name": "🛡️ Member Actions",
                "value": (
                    "`/kick` — Kick a member from the server\n"
                    "`/ban` — Ban a member from the server\n"
                    "`/unban` — Unban a user by ID\n"
                    "`/mute` — Timeout a member for X minutes\n"
                    "`/clear` — Bulk delete messages (1–100)\n"
                    "`/warn` — Warn a member and log it\n"
                    "`/warnings` — View a member's warning history"
                ),
                "inline": True
            },
            {
                "name": "� Channel Control",
                "value": (
                    "`/slowmode` — Set channel slowmode delay\n"
                    "`/lock` — Lock a channel (members can't send)\n"
                    "`/unlock` — Unlock a previously locked channel\n"
                ),
                "inline": True
            }
        ]
    },
    {
        "title": "📖 NullSec Bot — Page 5/5",
        "description": "**Utility & Info Commands**",
        "fields": [
            {
                "name": "📊 Info Commands",
                "value": (
                    "`/serverinfo` — Show server stats & info\n"
                    "`/userinfo` — Show a user's account info\n"
                    "`/avatar` — Display a user's avatar\n"
                    "`/ping` — Check bot latency & status\n"
                    "`/uptime` — Show how long the bot has been running"
                ),
                "inline": True
            },
            {
                "name": "⏰ Tools",
                "value": (
                    "`/remind` — Set a DM reminder after X minutes\n"
                    "`/poll` — Create a poll with up to 4 options\n"
                ),
                "inline": True
            }
        ]
    }
]


class HelpView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.page = 0
        self.user_id = user_id
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page == len(HELP_PAGES) - 1
        self.page_label.label = f"{self.page + 1} / {len(HELP_PAGES)}"

    def build_embed(self) -> discord.Embed:
        page = HELP_PAGES[self.page]
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=COLOR_CYAN
        )
        for field in page["fields"]:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        embed.set_footer(text="NullSec Bot • Use the buttons to navigate pages")
        return embed

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="help_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This menu isn't for you!", ephemeral=True)
            return
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="1 / 3", style=discord.ButtonStyle.primary, custom_id="help_page", disabled=True)
    async def page_label(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="help_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This menu isn't for you!", ephemeral=True)
            return
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    view = HelpView(user_id=interaction.user.id)
    await interaction.response.send_message(embed=view.build_embed(), view=view)



# ─── Cybersec Utility Commands ──────────────────────────────────

@bot.tree.command(name="hash", description="Generate hashes of a text string")
@app_commands.describe(text="The text to hash", algorithm="Hash algorithm to use")
@app_commands.choices(algorithm=[
    app_commands.Choice(name="All", value="all"),
    app_commands.Choice(name="MD5", value="md5"),
    app_commands.Choice(name="SHA1", value="sha1"),
    app_commands.Choice(name="SHA256", value="sha256"),
    app_commands.Choice(name="SHA512", value="sha512"),
])
async def hash_command(interaction: discord.Interaction, text: str, algorithm: str = "all"):
    hashes = {
        "MD5": hashlib.md5(text.encode()).hexdigest(),
        "SHA1": hashlib.sha1(text.encode()).hexdigest(),
        "SHA256": hashlib.sha256(text.encode()).hexdigest(),
        "SHA512": hashlib.sha512(text.encode()).hexdigest(),
    }

    embed = discord.Embed(
        title="🔑 Hash Generator",
        description=f"Input: `{text[:100]}{'...' if len(text) > 100 else ''}`",
        color=COLOR_GREEN
    )

    if algorithm == "all":
        for name, value in hashes.items():
            embed.add_field(name=name, value=f"```{value}```", inline=False)
    else:
        name = algorithm.upper()
        embed.add_field(name=name, value=f"```{hashes[name]}```", inline=False)

    embed.set_footer(text="NullSec Bot")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="encode", description="Encode or decode text")
@app_commands.describe(
    text="The text to encode/decode",
    method="Encoding method",
    mode="Encode or decode"
)
@app_commands.choices(
    method=[
        app_commands.Choice(name="Base64", value="base64"),
        app_commands.Choice(name="Hex", value="hex"),
        app_commands.Choice(name="URL Encode", value="url"),
        app_commands.Choice(name="Binary", value="binary"),
        app_commands.Choice(name="ROT13", value="rot13"),
    ],
    mode=[
        app_commands.Choice(name="Encode", value="encode"),
        app_commands.Choice(name="Decode", value="decode"),
    ]
)
async def encode_command(interaction: discord.Interaction, text: str, method: str, mode: str = "encode"):
    result = ""
    try:
        if method == "base64":
            if mode == "encode":
                result = base64.b64encode(text.encode()).decode()
            else:
                result = base64.b64decode(text.encode()).decode()

        elif method == "hex":
            if mode == "encode":
                result = binascii.hexlify(text.encode()).decode()
            else:
                result = binascii.unhexlify(text).decode()

        elif method == "url":
            if mode == "encode":
                result = quote(text)
            else:
                result = unquote(text)

        elif method == "binary":
            if mode == "encode":
                result = ' '.join(format(ord(c), '08b') for c in text)
            else:
                chars = text.split()
                result = ''.join(chr(int(b, 2)) for b in chars)

        elif method == "rot13":
            import codecs
            result = codecs.encode(text, 'rot_13')

    except Exception as e:
        result = f"Error: {str(e)}"

    embed = discord.Embed(
        title=f"🔄 {method.upper()} — {mode.capitalize()}",
        color=COLOR_CYAN
    )
    embed.add_field(name="Input", value=f"```{text[:500]}```", inline=False)
    embed.add_field(name="Output", value=f"```{result[:1000]}```", inline=False)
    embed.set_footer(text="NullSec Bot • Encoding Tool")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="iplookup", description="Lookup information about an IP address")
@app_commands.describe(ip="The IP address to lookup")
async def iplookup_command(interaction: discord.Interaction, ip: str):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query") as resp:
                data = await resp.json()

            if data.get("status") == "fail":
                embed = discord.Embed(
                    title="❌ IP Lookup Failed",
                    description=f"Could not find information for `{ip}`.\n{data.get('message', '')}",
                    color=COLOR_RED
                )
            else:
                embed = discord.Embed(
                    title=f"🌐 IP Lookup — {data['query']}",
                    color=COLOR_GREEN
                )
                embed.add_field(name="🏙️ Location", value=f"{data.get('city', 'N/A')}, {data.get('regionName', 'N/A')}, {data.get('country', 'N/A')}", inline=False)
                embed.add_field(name="📮 ZIP", value=data.get('zip', 'N/A'), inline=True)
                embed.add_field(name="🕐 Timezone", value=data.get('timezone', 'N/A'), inline=True)
                embed.add_field(name="📡 ISP", value=data.get('isp', 'N/A'), inline=False)
                embed.add_field(name="🏢 Organization", value=data.get('org', 'N/A'), inline=False)
                embed.add_field(name="🔗 AS", value=data.get('as', 'N/A'), inline=False)
                embed.add_field(name="📍 Coordinates", value=f"`{data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}`", inline=False)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to lookup IP: {str(e)}",
                color=COLOR_RED
            )

    embed.set_footer(text="NullSec Bot • IP Lookup Tool")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="whois", description="Perform a WHOIS lookup on a domain")
@app_commands.describe(domain="The domain to lookup (e.g. example.com)")
async def whois_command(interaction: discord.Interaction, domain: str):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        try:
            # Using a free WHOIS API
            async with session.get(f"https://api.api-ninjas.com/v1/whois?domain={domain}",
                                   headers={"X-Api-Key": "FREE_API_KEY"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(
                        title=f"🔍 WHOIS — {domain}",
                        color=COLOR_CYAN
                    )

                    if data.get("domain_name"):
                        embed.add_field(name="Domain", value=f"`{data.get('domain_name', 'N/A')}`", inline=True)
                    if data.get("registrar"):
                        embed.add_field(name="Registrar", value=data.get('registrar', 'N/A'), inline=True)
                    if data.get("creation_date"):
                        embed.add_field(name="Created", value=data.get('creation_date', 'N/A'), inline=True)
                    if data.get("expiration_date"):
                        embed.add_field(name="Expires", value=data.get('expiration_date', 'N/A'), inline=True)
                    if data.get("name_servers"):
                        ns = data.get('name_servers', [])
                        if isinstance(ns, list):
                            ns = '\n'.join(ns[:5])
                        embed.add_field(name="Name Servers", value=f"```{ns}```", inline=False)
                else:
                    embed = discord.Embed(
                        title="❌ WHOIS Lookup Failed",
                        description=f"Could not find WHOIS data for `{domain}`.\nTip: You can get a free API key from api-ninjas.com and set it in the bot config.",
                        color=COLOR_RED
                    )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"WHOIS lookup failed: {str(e)}",
                color=COLOR_RED
            )

    embed.set_footer(text="NullSec Bot • WHOIS Tool")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="genpass", description="Generate a secure random password")
@app_commands.describe(
    length="Password length (8-128)",
    uppercase="Include uppercase letters",
    numbers="Include numbers",
    symbols="Include special symbols"
)
async def genpass_command(
    interaction: discord.Interaction,
    length: int = 16,
    uppercase: bool = True,
    numbers: bool = True,
    symbols: bool = True
):
    if length < 8 or length > 128:
        await interaction.response.send_message("❌ Password length must be between 8 and 128.", ephemeral=True)
        return

    charset = string.ascii_lowercase
    if uppercase:
        charset += string.ascii_uppercase
    if numbers:
        charset += string.digits
    if symbols:
        charset += string.punctuation

    password = ''.join(random.SystemRandom().choice(charset) for _ in range(length))

    # Calculate entropy
    import math
    entropy = math.log2(len(charset)) * length

    # Strength rating
    if entropy < 40:
        strength = "🔴 Weak"
    elif entropy < 60:
        strength = "🟡 Moderate"
    elif entropy < 80:
        strength = "🟢 Strong"
    else:
        strength = "💎 Very Strong"

    embed = discord.Embed(
        title="🔐 Password Generator",
        color=COLOR_GREEN
    )
    embed.add_field(name="Password", value=f"||`{password}`||", inline=False)
    embed.add_field(name="Length", value=str(length), inline=True)
    embed.add_field(name="Entropy", value=f"{entropy:.1f} bits", inline=True)
    embed.add_field(name="Strength", value=strength, inline=True)
    embed.add_field(
        name="Character Set",
        value=f"{'✅' if True else '❌'} Lowercase  {'✅' if uppercase else '❌'} Uppercase  {'✅' if numbers else '❌'} Numbers  {'✅' if symbols else '❌'} Symbols",
        inline=False
    )
    embed.set_footer(text="NullSec Bot • Password is hidden in a spoiler tag")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="headers", description="Fetch and analyze HTTP headers of a URL")
@app_commands.describe(url="The URL to fetch headers from")
async def headers_command(interaction: discord.Interaction, url: str):
    await interaction.response.defer()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
                embed = discord.Embed(
                    title=f"📡 HTTP Headers — {url[:50]}",
                    description=f"Status: **{resp.status} {resp.reason}**",
                    color=COLOR_GREEN if resp.status == 200 else COLOR_YELLOW
                )

                # Security headers to check
                security_headers = {
                    "Strict-Transport-Security": "HSTS",
                    "Content-Security-Policy": "CSP",
                    "X-Frame-Options": "X-Frame",
                    "X-Content-Type-Options": "X-Content-Type",
                    "X-XSS-Protection": "XSS Protection",
                    "Referrer-Policy": "Referrer Policy",
                    "Permissions-Policy": "Permissions Policy"
                }

                # Show key headers
                header_text = ""
                for key, value in list(resp.headers.items())[:15]:
                    header_text += f"`{key}`: {value[:80]}\n"

                if header_text:
                    embed.add_field(name="Response Headers", value=header_text[:1024], inline=False)

                # Security header check
                security_text = ""
                for header, label in security_headers.items():
                    if header in resp.headers:
                        security_text += f"✅ {label}\n"
                    else:
                        security_text += f"❌ {label} (missing)\n"

                embed.add_field(name="🔒 Security Headers", value=security_text, inline=False)

        except aiohttp.ClientError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to fetch headers: {str(e)}",
                color=COLOR_RED
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Unexpected error: {str(e)}",
                color=COLOR_RED
            )

    embed.set_footer(text="NullSec Bot • Header Analysis Tool")
    await interaction.followup.send(embed=embed)



# ─── Extended Cybersec Tools ────────────────────────────────────

@bot.tree.command(name="cve", description="Look up a CVE vulnerability by ID")
@app_commands.describe(cve_id="The CVE ID to look up (e.g. CVE-2021-44228)")
async def cve_command(interaction: discord.Interaction, cve_id: str):
    await interaction.response.defer()

    cve_id = cve_id.upper().strip()
    if not cve_id.startswith("CVE-"):
        cve_id = "CVE-" + cve_id

    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://cveawg.mitre.org/api/cve/{cve_id}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    meta = data.get("cveMetadata", {})
                    containers = data.get("containers", {}).get("cna", {})
                    desc = containers.get("descriptions", [{}])[0].get("value", "No description available.")
                    title = containers.get("title", cve_id)
                    severity = "Unknown"
                    score = "N/A"
                    metrics = containers.get("metrics", [])
                    for m in metrics:
                        for key in ["cvssV3_1", "cvssV3_0", "cvssV2_0"]:
                            if key in m:
                                score = m[key].get("baseScore", "N/A")
                                severity = m[key].get("baseSeverity", "Unknown")
                                break

                    if severity == "CRITICAL":
                        color = COLOR_RED
                    elif severity in ("HIGH",):
                        color = COLOR_YELLOW
                    else:
                        color = COLOR_CYAN

                    embed = discord.Embed(
                        title=f"🔍 {cve_id}",
                        description=f"**{title}**\n\n{desc[:800]}{'...' if len(desc) > 800 else ''}",
                        color=color
                    )
                    embed.add_field(name="Severity", value=severity, inline=True)
                    embed.add_field(name="CVSS Score", value=str(score), inline=True)
                    embed.add_field(name="State", value=meta.get("state", "N/A"), inline=True)
                    embed.add_field(name="Published", value=meta.get("datePublished", "N/A")[:10], inline=True)
                    embed.add_field(name="NVD Link", value=f"[View on NVD](https://nvd.nist.gov/vuln/detail/{cve_id})", inline=False)
                else:
                    embed = discord.Embed(
                        title="❌ CVE Not Found",
                        description=f"Could not find data for `{cve_id}`. Make sure the ID is correct.",
                        color=COLOR_RED
                    )
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)

    embed.set_footer(text="NullSec Bot • CVE Lookup")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="subnet", description="Calculate subnet information from a CIDR address")
@app_commands.describe(cidr="CIDR notation (e.g. 192.168.1.0/24)")
async def subnet_command(interaction: discord.Interaction, cidr: str):
    import ipaddress
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        embed = discord.Embed(
            title=f"🌐 Subnet Calculator — {cidr}",
            color=COLOR_CYAN
        )
        embed.add_field(name="Network Address", value=f"`{net.network_address}`", inline=True)
        embed.add_field(name="Broadcast Address", value=f"`{net.broadcast_address}`", inline=True)
        embed.add_field(name="Subnet Mask", value=f"`{net.netmask}`", inline=True)
        embed.add_field(name="Wildcard Mask", value=f"`{net.hostmask}`", inline=True)
        embed.add_field(name="Total Hosts", value=f"`{net.num_addresses:,}`", inline=True)
        embed.add_field(name="Usable Hosts", value=f"`{max(0, net.num_addresses - 2):,}`", inline=True)
        embed.add_field(name="IP Version", value=f"IPv{net.version}", inline=True)
        embed.add_field(name="Prefix Length", value=f"`/{net.prefixlen}`", inline=True)
        first = list(net.hosts())[0] if net.num_addresses > 2 else net.network_address
        last = list(net.hosts())[-1] if net.num_addresses > 2 else net.broadcast_address
        embed.add_field(name="Usable Range", value=f"`{first}` → `{last}`", inline=False)
        embed.set_footer(text="NullSec Bot • Subnet Calculator")
        await interaction.response.send_message(embed=embed)
    except ValueError as e:
        await interaction.response.send_message(f"❌ Invalid CIDR notation: `{cidr}`\nExample: `192.168.1.0/24`", ephemeral=True)


# Common ports reference
COMMON_PORTS = {
    20: ("FTP Data", "File Transfer Protocol data transfer"),
    21: ("FTP Control", "File Transfer Protocol command control"),
    22: ("SSH", "Secure Shell — encrypted remote access"),
    23: ("Telnet", "Unencrypted remote access (legacy/insecure)"),
    25: ("SMTP", "Simple Mail Transfer Protocol — sending email"),
    53: ("DNS", "Domain Name System — resolves hostnames to IPs"),
    67: ("DHCP Server", "Dynamic Host Configuration Protocol server"),
    68: ("DHCP Client", "Dynamic Host Configuration Protocol client"),
    80: ("HTTP", "Hypertext Transfer Protocol — unencrypted web traffic"),
    110: ("POP3", "Post Office Protocol — email retrieval"),
    119: ("NNTP", "Network News Transfer Protocol"),
    123: ("NTP", "Network Time Protocol — clock synchronization"),
    143: ("IMAP", "Internet Message Access Protocol — email"),
    161: ("SNMP", "Simple Network Management Protocol"),
    194: ("IRC", "Internet Relay Chat"),
    389: ("LDAP", "Lightweight Directory Access Protocol"),
    443: ("HTTPS", "HTTP Secure — encrypted web traffic"),
    445: ("SMB", "Server Message Block — Windows file sharing"),
    465: ("SMTPS", "SMTP over SSL — secure email sending"),
    514: ("Syslog", "System logging protocol"),
    587: ("SMTP Submission", "Email submission with authentication"),
    636: ("LDAPS", "LDAP over SSL"),
    993: ("IMAPS", "IMAP over SSL — secure email"),
    995: ("POP3S", "POP3 over SSL — secure email retrieval"),
    1080: ("SOCKS Proxy", "SOCKS proxy server"),
    1433: ("MSSQL", "Microsoft SQL Server"),
    1521: ("Oracle DB", "Oracle Database"),
    3306: ("MySQL", "MySQL database server"),
    3389: ("RDP", "Remote Desktop Protocol — Windows remote access"),
    5432: ("PostgreSQL", "PostgreSQL database server"),
    5900: ("VNC", "Virtual Network Computing — remote desktop"),
    6379: ("Redis", "Redis in-memory data structure store"),
    8080: ("HTTP Alt", "Alternative HTTP port / web proxies"),
    8443: ("HTTPS Alt", "Alternative HTTPS port"),
    27017: ("MongoDB", "MongoDB NoSQL database"),
}

@bot.tree.command(name="port", description="Look up what a port number is commonly used for")
@app_commands.describe(number="The port number to look up (0-65535)")
async def port_command(interaction: discord.Interaction, number: int):
    if number < 0 or number > 65535:
        await interaction.response.send_message("❌ Port must be between 0 and 65535.", ephemeral=True)
        return

    if number in COMMON_PORTS:
        name, desc = COMMON_PORTS[number]
        if number in (23, 21, 110):
            security = "🔴 Insecure — avoid exposing this port"
            color = COLOR_RED
        elif number in (22, 443, 465, 993, 995, 636):
            security = "🟢 Encrypted / Secure protocol"
            color = COLOR_GREEN
        else:
            color = COLOR_CYAN
            security = "🟡 Use with caution — depends on configuration"

        embed = discord.Embed(
            title=f"🔌 Port {number} — {name}",
            description=desc,
            color=color
        )
        embed.add_field(name="Security Note", value=security, inline=False)
    else:
        embed = discord.Embed(
            title=f"🔌 Port {number}",
            description="This is not a well-known reserved port. It may be used by custom applications or services.",
            color=COLOR_YELLOW
        )
        if number < 1024:
            embed.add_field(name="Range", value="Well-known ports (0–1023) — requires root/admin to bind", inline=False)
        elif number < 49152:
            embed.add_field(name="Range", value="Registered ports (1024–49151) — used by applications", inline=False)
        else:
            embed.add_field(name="Range", value="Dynamic/private ports (49152–65535) — ephemeral connections", inline=False)

    embed.set_footer(text="NullSec Bot • Port Reference")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="dns", description="Perform a DNS lookup on a domain")
@app_commands.describe(domain="The domain to look up (e.g. example.com)")
@app_commands.choices(record_type=[
    app_commands.Choice(name="A (IPv4)", value="A"),
    app_commands.Choice(name="AAAA (IPv6)", value="AAAA"),
    app_commands.Choice(name="MX (Mail)", value="MX"),
    app_commands.Choice(name="TXT", value="TXT"),
    app_commands.Choice(name="NS (Nameservers)", value="NS"),
    app_commands.Choice(name="CNAME", value="CNAME"),
])
async def dns_command(interaction: discord.Interaction, domain: str, record_type: str = "A"):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://dns.google/resolve?name={domain}&type={record_type}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()

            status = data.get("Status", -1)
            answers = data.get("Answer", [])

            status_map = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 5: "REFUSED"}
            status_str = status_map.get(status, f"Code {status}")

            embed = discord.Embed(
                title=f"🌐 DNS Lookup — {domain} ({record_type})",
                color=COLOR_GREEN if answers else COLOR_RED
            )
            embed.add_field(name="Status", value=status_str, inline=True)
            embed.add_field(name="Records Found", value=str(len(answers)), inline=True)

            if answers:
                records = []
                for a in answers[:10]:
                    ttl = a.get("TTL", "?")
                    val = a.get("data", "?")
                    records.append(f"`{val}` (TTL: {ttl}s)")
                embed.add_field(name=f"{record_type} Records", value="\n".join(records), inline=False)
            else:
                embed.add_field(name="Result", value="No records found for this domain/type.", inline=False)

        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)

    embed.set_footer(text="NullSec Bot • DNS Lookup via Google DNS")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="reverseip", description="Find domains hosted on the same IP")
@app_commands.describe(ip="IP address or domain to reverse lookup")
async def reverseip_command(interaction: discord.Interaction, ip: str):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        try:
            # First resolve domain to IP if needed
            async with session.get(
                f"https://dns.google/resolve?name={ip}&type=A",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
                answers = data.get("Answer", [])
                resolved_ip = answers[0].get("data", ip) if answers else ip

            # Reverse DNS via Google
            parts = resolved_ip.split(".")
            reversed_parts = ".".join(reversed(parts))
            async with session.get(
                f"https://dns.google/resolve?name={reversed_parts}.in-addr.arpa&type=PTR",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
                ptr_answers = data.get("Answer", [])

            embed = discord.Embed(
                title=f"🔄 Reverse IP — {ip}",
                color=COLOR_PURPLE
            )
            embed.add_field(name="Resolved IP", value=f"`{resolved_ip}`", inline=True)

            if ptr_answers:
                hostnames = [a.get("data", "?").rstrip(".") for a in ptr_answers]
                embed.add_field(name="Reverse DNS (PTR)", value="\n".join(f"`{h}`" for h in hostnames), inline=False)
            else:
                embed.add_field(name="Reverse DNS (PTR)", value="No PTR record found.", inline=False)

            embed.add_field(
                name="Tip",
                value=f"For full domain enumeration, try [ViewDNS.info](https://viewdns.info/reverseip/?host={resolved_ip}&t=1)",
                inline=False
            )

        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)

    embed.set_footer(text="NullSec Bot • Reverse IP Tool")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="convert", description="Convert a number between different bases")
@app_commands.describe(value="The number to convert", from_base="The base to convert from")
@app_commands.choices(from_base=[
    app_commands.Choice(name="Decimal (base 10)", value="dec"),
    app_commands.Choice(name="Hexadecimal (base 16)", value="hex"),
    app_commands.Choice(name="Binary (base 2)", value="bin"),
    app_commands.Choice(name="Octal (base 8)", value="oct"),
])
async def convert_command(interaction: discord.Interaction, value: str, from_base: str = "dec"):
    try:
        value = value.strip().lower().replace("0x", "").replace("0b", "").replace("0o", "")
        base_map = {"dec": 10, "hex": 16, "bin": 2, "oct": 8}
        n = int(value, base_map[from_base])

        embed = discord.Embed(
            title="🔢 Base Converter",
            color=COLOR_CYAN
        )
        embed.add_field(name="Decimal (base 10)", value=f"`{n}`", inline=True)
        embed.add_field(name="Hexadecimal (base 16)", value=f"`{hex(n)}`", inline=True)
        embed.add_field(name="Binary (base 2)", value=f"`{bin(n)}`", inline=True)
        embed.add_field(name="Octal (base 8)", value=f"`{oct(n)}`", inline=True)
        embed.add_field(name="ASCII", value=f"`{chr(n)}`" if 32 <= n <= 126 else "N/A (out of printable range)", inline=True)
        embed.set_footer(text="NullSec Bot • Base Converter")
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message(
            f"❌ `{value}` is not a valid {from_base} number.", ephemeral=True
        )


# ─── More Cybersec Tools ──────────────────────────────────────────

@bot.tree.command(name="ssl", description="Check SSL certificate info for a domain")
@app_commands.describe(domain="The domain to check (e.g. google.com)")
async def ssl_command(interaction: discord.Interaction, domain: str):
    await interaction.response.defer()
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
    try:
        ctx = ssl.create_default_context()
        loop = asyncio.get_event_loop()
        def get_cert():
            with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                s.settimeout(10)
                s.connect((domain, 443))
                return s.getpeercert()
        cert = await loop.run_in_executor(None, get_cert)
        subject = dict(x[0] for x in cert.get("subject", []))
        issuer = dict(x[0] for x in cert.get("issuer", []))
        not_after = cert.get("notAfter", "?")
        not_before = cert.get("notBefore", "?")
        san = cert.get("subjectAltName", [])
        san_str = ", ".join(v for _, v in san[:5]) + (" ..." if len(san) > 5 else "")
        import datetime as dt
        expiry = dt.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        days_left = (expiry - dt.datetime.utcnow()).days
        color = COLOR_GREEN if days_left > 30 else (COLOR_YELLOW if days_left > 7 else COLOR_RED)
        embed = discord.Embed(title=f"🔒 SSL Certificate — {domain}", color=color)
        embed.add_field(name="Common Name", value=subject.get("commonName", "N/A"), inline=True)
        embed.add_field(name="Issuer", value=issuer.get("organizationName", "N/A"), inline=True)
        embed.add_field(name="Valid From", value=not_before[:12], inline=True)
        embed.add_field(name="Expires", value=not_after[:12], inline=True)
        embed.add_field(name="Days Remaining", value=f"`{days_left}` days", inline=True)
        embed.add_field(name="Alt Names", value=san_str or "N/A", inline=False)
    except Exception as e:
        embed = discord.Embed(title="❌ SSL Check Failed", description=str(e), color=COLOR_RED)
    embed.set_footer(text="NullSec Bot • SSL Checker")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="robots", description="Fetch a site's robots.txt file")
@app_commands.describe(url="The site to check (e.g. example.com)")
async def robots_command(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    base = url.rstrip("/")
    robots_url = f"{base}/robots.txt"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    content = content[:1500] + ("\n... (truncated)" if len(content) > 1500 else "")
                    embed = discord.Embed(
                        title=f"🤖 robots.txt — {base}",
                        description=f"```{content}```",
                        color=COLOR_CYAN
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Not Found",
                        description=f"No robots.txt found at `{robots_url}` (HTTP {resp.status})",
                        color=COLOR_RED
                    )
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)
    embed.set_footer(text="NullSec Bot • robots.txt Viewer")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="mac", description="Lookup the vendor/manufacturer of a MAC address")
@app_commands.describe(mac="The MAC address (e.g. 00:1A:2B:3C:4D:5E)")
async def mac_command(interaction: discord.Interaction, mac: str):
    await interaction.response.defer()
    mac_clean = mac.replace(":", "").replace("-", "").replace(".", "")[:6]
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://api.macvendors.com/{mac_clean}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    vendor = await resp.text()
                    embed = discord.Embed(title=f"🌐 MAC Vendor Lookup", color=COLOR_GREEN)
                    embed.add_field(name="MAC Address", value=f"`{mac}`", inline=True)
                    embed.add_field(name="OUI (first 6 hex)", value=f"`{mac_clean.upper()}`", inline=True)
                    embed.add_field(name="Manufacturer", value=vendor, inline=False)
                else:
                    embed = discord.Embed(title="❌ Not Found", description=f"No vendor found for `{mac}`. Make sure it's a valid MAC address.", color=COLOR_RED)
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)
    embed.set_footer(text="NullSec Bot • MAC Vendor Lookup")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="asn", description="Lookup an IP or ASN number")
@app_commands.describe(query="IP address or ASN (e.g. 8.8.8.8 or AS15169)")
async def asn_command(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://ipinfo.io/{query}/json", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
            embed = discord.Embed(title=f"📶 ASN Lookup — {query}", color=COLOR_PURPLE)
            for key in ["ip", "hostname", "city", "region", "country", "org", "timezone"]:
                if key in data:
                    embed.add_field(name=key.capitalize(), value=f"`{data[key]}`", inline=True)
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)
    embed.set_footer(text="NullSec Bot • ASN Lookup via ipinfo.io")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="cipher", description="Encrypt or decrypt text using classic ciphers")
@app_commands.describe(text="Text to encrypt/decode", cipher_type="Cipher to use", key="Key (for Caesar: shift number, for Vigenere: keyword)")
@app_commands.choices(cipher_type=[
    app_commands.Choice(name="Caesar", value="caesar"),
    app_commands.Choice(name="ROT13", value="rot13"),
    app_commands.Choice(name="Atbash", value="atbash"),
    app_commands.Choice(name="Vigenere", value="vigenere"),
])
async def cipher_command(interaction: discord.Interaction, text: str, cipher_type: str, key: str = "3"):
    result = ""
    try:
        if cipher_type == "rot13":
            result = codecs.encode(text, "rot_13")
        elif cipher_type == "caesar":
            shift = int(key) % 26
            result = "".join(
                chr((ord(c) - (65 if c.isupper() else 97) + shift) % 26 + (65 if c.isupper() else 97))
                if c.isalpha() else c for c in text
            )
        elif cipher_type == "atbash":
            result = "".join(
                chr(90 - (ord(c) - 65)) if c.isupper() else
                chr(122 - (ord(c) - 97)) if c.islower() else c
                for c in text
            )
        elif cipher_type == "vigenere":
            key_clean = key.lower()
            key_idx = 0
            for c in text:
                if c.isalpha():
                    shift = ord(key_clean[key_idx % len(key_clean)]) - 97
                    base = 65 if c.isupper() else 97
                    result += chr((ord(c) - base + shift) % 26 + base)
                    key_idx += 1
                else:
                    result += c
    except Exception as e:
        result = f"Error: {e}"

    embed = discord.Embed(title=f"🔐 {cipher_type.capitalize()} Cipher", color=COLOR_PURPLE)
    embed.add_field(name="Input", value=f"```{text[:500]}```", inline=False)
    embed.add_field(name="Output", value=f"```{result[:500]}```", inline=False)
    if cipher_type in ("caesar", "vigenere"):
        embed.add_field(name="Key", value=f"`{key}`", inline=True)
    embed.set_footer(text="NullSec Bot • Classic Cipher Tool")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="regex", description="Test a regex pattern against a string")
@app_commands.describe(pattern="The regex pattern", text="The string to test against")
async def regex_command(interaction: discord.Interaction, pattern: str, text: str):
    try:
        compiled = re.compile(pattern)
        matches = compiled.findall(text)
        full_match = compiled.search(text)
        embed = discord.Embed(
            title="🔍 Regex Tester",
            color=COLOR_GREEN if matches else COLOR_RED
        )
        embed.add_field(name="Pattern", value=f"```{pattern}```", inline=False)
        embed.add_field(name="Input", value=f"```{text[:300]}```", inline=False)
        embed.add_field(name="Match Found", value="Yes" if full_match else "No", inline=True)
        embed.add_field(name="Total Matches", value=str(len(matches)), inline=True)
        if matches:
            embed.add_field(name="Matches", value="\n".join(f"`{m}`" for m in matches[:10]), inline=False)
    except re.error as e:
        embed = discord.Embed(title="❌ Invalid Regex", description=f"Error: `{e}`", color=COLOR_RED)
    embed.set_footer(text="NullSec Bot • Regex Tester")
    await interaction.response.send_message(embed=embed)


# ─── Quiz View ────────────────────────────────────────────────

class QuizView(discord.ui.View):
    def __init__(self, question: dict, user_id: int):
        super().__init__(timeout=30)
        self.question = question
        self.user_id = user_id
        self.answered = False

    async def handle_answer(self, interaction: discord.Interaction, chosen: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This quiz isn't for you!", ephemeral=True)
            return
        if self.answered:
            await interaction.response.send_message("Already answered!", ephemeral=True)
            return
        self.answered = True
        for item in self.children:
            item.disabled = True
        correct = chosen == self.question["ans"]
        result = "🎉 Correct!" if correct else f"❌ Wrong! The answer was **{self.question['ans']}**"
        await interaction.response.edit_message(
            content=f"{result}",
            view=self
        )

    @discord.ui.button(label="A", style=discord.ButtonStyle.secondary)
    async def btn_a(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_answer(i, "A")
    @discord.ui.button(label="B", style=discord.ButtonStyle.secondary)
    async def btn_b(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_answer(i, "B")
    @discord.ui.button(label="C", style=discord.ButtonStyle.secondary)
    async def btn_c(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_answer(i, "C")
    @discord.ui.button(label="D", style=discord.ButtonStyle.secondary)
    async def btn_d(self, i: discord.Interaction, b: discord.ui.Button): await self.handle_answer(i, "D")


@bot.tree.command(name="quiz", description="Get a random cybersec trivia question")
async def quiz_command(interaction: discord.Interaction):
    q = random.choice(QUIZ_QUESTIONS)
    embed = discord.Embed(
        title="🧠 Cybersec Quiz",
        description=f"**{q['q']}**\n\n" + "\n".join(q["options"]),
        color=COLOR_CYAN
    )
    embed.set_footer(text="You have 30 seconds to answer!")
    view = QuizView(q, interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="quote", description="Get a random hacker/security quote")
async def quote_command(interaction: discord.Interaction):
    q, author = random.choice(HACKER_QUOTES)
    embed = discord.Embed(
        title="💬 Hacker Quote",
        description=f"*“{q}”*\n\n— **{author}**",
        color=COLOR_PURPLE
    )
    embed.set_footer(text="NullSec Bot • /quote")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="challenge", description="Get a daily cybersec challenge")
async def challenge_command(interaction: discord.Interaction):
    # Pick challenge based on current day so it rotates daily
    day_index = datetime.datetime.utcnow().timetuple().tm_yday % len(DAILY_CHALLENGES)
    challenge = DAILY_CHALLENGES[day_index]
    embed = discord.Embed(
        title=f"🎯 Daily Challenge — Day {day_index + 1}",
        description=challenge,
        color=COLOR_GREEN
    )
    embed.set_footer(text="NullSec Bot • Share your answer in the server!")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ctftime", description="Show upcoming CTF competitions from CTFtime")
async def ctftime_command(interaction: discord.Interaction):
    await interaction.response.defer()
    async with aiohttp.ClientSession() as session:
        try:
            now = int(time.time())
            url = f"https://ctftime.org/api/v1/events/?limit=5&start={now}"
            headers = {"User-Agent": "NullSecBot/1.0"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                events = await resp.json()
            embed = discord.Embed(
                title="🏆 Upcoming CTF Competitions",
                description="Next 5 events from [CTFtime.org](https://ctftime.org)",
                color=COLOR_YELLOW
            )
            for ev in events[:5]:
                start = ev.get("start", "?")[:10]
                end = ev.get("finish", "?")[:10]
                url_ev = ev.get("url", "#")
                embed.add_field(
                    name=ev.get("title", "Unknown"),
                    value=f"📅 {start} → {end}\n🔗 [Event Page]({url_ev})",
                    inline=True
                )
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=str(e), color=COLOR_RED)
    embed.set_footer(text="NullSec Bot • CTFtime.org")
    await interaction.followup.send(embed=embed)


# ─── Moderation Commands ────────────────────────────────────────────

@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="The member to kick", reason="Reason for kicking")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_command(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You cannot kick someone with an equal or higher role.", ephemeral=True)
        return

    await member.kick(reason=reason)
    embed = discord.Embed(
        title="👢 Member Kicked",
        description=f"**{member.display_name}** has been kicked.\n**Reason:** {reason}",
        color=COLOR_RED,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text=f"Kicked by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="The member to ban", reason="Reason for banning")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_command(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ You cannot ban someone with an equal or higher role.", ephemeral=True)
        return

    await member.ban(reason=reason)
    embed = discord.Embed(
        title="🔨 Member Banned",
        description=f"**{member.display_name}** has been banned.\n**Reason:** {reason}",
        color=COLOR_RED,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text=f"Banned by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.describe(user_id="The user ID to unban")
@app_commands.checks.has_permissions(ban_members=True)
async def unban_command(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        embed = discord.Embed(
            title="✅ User Unbanned",
            description=f"**{user.display_name}** has been unbanned.",
            color=COLOR_GREEN
        )
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)


@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.describe(
    member="The member to mute",
    duration="Duration in minutes",
    reason="Reason for muting"
)
@app_commands.checks.has_permissions(moderate_members=True)
async def mute_command(interaction: discord.Interaction, member: discord.Member, duration: int = 10, reason: str = "No reason provided"):
    if duration < 1 or duration > 40320:  # Max 28 days
        await interaction.response.send_message("❌ Duration must be between 1 and 40320 minutes (28 days).", ephemeral=True)
        return

    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=duration)
    await member.timeout(until, reason=reason)

    embed = discord.Embed(
        title="🔇 Member Muted",
        description=f"**{member.display_name}** has been muted for **{duration} minutes**.\n**Reason:** {reason}",
        color=COLOR_YELLOW,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text=f"Muted by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Clear messages from the channel")
@app_commands.describe(amount="Number of messages to clear (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_command(interaction: discord.Interaction, amount: int = 10):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Cleared **{len(deleted)}** messages.", ephemeral=True)


# ─── Server Setup Command ───────────────────────────────────────

@bot.tree.command(name="setup", description="Automatically set up the NullSec server (channels, roles, categories)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    log = []

    # ── Roles ──────────────────────────────────────────────────
    role_configs = [
        {"name": "Admin",     "color": discord.Color.red(),                 "hoist": True,  "permissions": discord.Permissions.all()},
        {"name": "Moderator", "color": discord.Color.orange(),              "hoist": True,  "permissions": discord.Permissions(kick_members=True, ban_members=True, manage_messages=True, moderate_members=True)},
        {"name": "Member",    "color": discord.Color.from_rgb(0, 212, 255), "hoist": False, "permissions": discord.Permissions(send_messages=True, read_messages=True, read_message_history=True)},
        {"name": "Bot",       "color": discord.Color.greyple(),             "hoist": False, "permissions": discord.Permissions(send_messages=True, read_messages=True)},
    ]

    created_roles = {}
    existing_role_names = {r.name for r in guild.roles}
    for rc in role_configs:
        if rc["name"] not in existing_role_names:
            role = await guild.create_role(
                name=rc["name"],
                color=rc["color"],
                hoist=rc["hoist"],
                permissions=rc["permissions"],
                reason="NullSec /setup"
            )
            log.append(f"Role created: @{rc['name']}")
        else:
            role = discord.utils.get(guild.roles, name=rc["name"])
            log.append(f"Role already exists: @{rc['name']}")
        created_roles[rc["name"]] = role

    # ── Categories & Channels ───────────────────────────────────
    everyone = guild.default_role
    moderator_role = created_roles.get("Moderator")
    admin_role = created_roles.get("Admin")

    # Helper: get or create a category
    async def get_or_create_category(name, overwrites=None):
        cat = discord.utils.get(guild.categories, name=name)
        if not cat:
            kwargs = {"reason": "NullSec /setup"}
            if overwrites:
                kwargs["overwrites"] = overwrites
            cat = await guild.create_category(name, **kwargs)
            log.append(f"Category created: {name}")
        else:
            log.append(f"Category already exists: {name}")
        return cat

    # Helper: get or create a text channel
    async def get_or_create_channel(name, category, topic="", overwrites=None):
        ch = discord.utils.get(guild.text_channels, name=name)
        if not ch:
            kwargs = {"category": category, "topic": topic, "reason": "NullSec /setup"}
            if overwrites:
                kwargs["overwrites"] = overwrites
            ch = await guild.create_text_channel(name, **kwargs)
            log.append(f"Channel created: #{name}")
        else:
            log.append(f"Channel already exists: #{name}")
        return ch

    # Build overwrites safely (only include roles that actually exist)
    staff_overwrites = {everyone: discord.PermissionOverwrite(read_messages=False)}
    if moderator_role:
        staff_overwrites[moderator_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    if admin_role:
        staff_overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    # Read-only (announcements, rules)
    readonly_overwrites = {
        everyone: discord.PermissionOverwrite(read_messages=True, send_messages=False),
    }

    # 📋 INFO
    cat_info = await get_or_create_category("📋 INFO")
    await get_or_create_channel("rules",         cat_info, "Server rules — read before chatting.", readonly_overwrites)
    await get_or_create_channel("announcements", cat_info, "Official NullSec announcements.",       readonly_overwrites)
    await get_or_create_channel("welcome",       cat_info, "Welcome new members!")

    # 💬 GENERAL
    cat_general = await get_or_create_category("💬 GENERAL")
    await get_or_create_channel("general-chat",    cat_general, "General conversation.")
    await get_or_create_channel("introductions",   cat_general, "Introduce yourself to the community.")
    await get_or_create_channel("off-topic",       cat_general, "Anything goes (keep it clean).")

    # 🔐 CYBERSEC
    cat_cyber = await get_or_create_category("🔐 CYBERSEC")
    await get_or_create_channel("ctf-challenges",  cat_cyber, "CTF challenge discussion and hints.")
    await get_or_create_channel("tools-resources", cat_cyber, "Useful cybersec tools and resources.")
    await get_or_create_channel("writeups",        cat_cyber, "Post your CTF writeups here.")
    await get_or_create_channel("news",            cat_cyber, "Cybersecurity news and updates.")

    # 🤖 BOT
    cat_bot = await get_or_create_category("🤖 BOT")
    await get_or_create_channel("bot-commands",    cat_bot, "Use bot commands here.")

    # 🛡️ STAFF (private)
    cat_staff = await get_or_create_category("🛡️ STAFF", overwrites=staff_overwrites)
    await get_or_create_channel("mod-logs",   cat_staff, "Automated moderation logs.", staff_overwrites)
    await get_or_create_channel("staff-chat", cat_staff, "Staff discussion.",          staff_overwrites)

    # ── Summary embed ───────────────────────────────────────────
    embed = discord.Embed(
        title="✅ NullSec Server Setup Complete!",
        description=f"Created/verified **{len(log)}** items.",
        color=COLOR_GREEN,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(
        name="What was set up",
        value=(
            "**Roles:** Admin, Moderator, Member, Bot\n"
            "**Categories:** INFO, GENERAL, CYBERSEC, BOT, STAFF\n"
            "**Channels:** rules, announcements, welcome, general-chat, introductions, "
            "off-topic, ctf-challenges, tools-resources, writeups, news, bot-commands, mod-logs, staff-chat"
        ),
        inline=False
    )
    embed.add_field(
        name="Next Steps",
        value=(
            "1. Assign yourself the **Admin** role\n"
            "2. Assign the bot the **Bot** role\n"
            "3. Post your rules in #rules\n"
            "4. Create a Discord invite and share it!"
        ),
        inline=False
    )
    embed.set_footer(text="NullSec Bot • /setup")
    await interaction.followup.send(embed=embed, ephemeral=True)



# ─── Rules Command ──────────────────────────────────────────────

@bot.tree.command(name="postrules", description="Post the server rules in #rules (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def postrules_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # Use #rules if it exists, otherwise post in the current channel
    channel = discord.utils.get(interaction.guild.text_channels, name="rules") or interaction.channel

    # ── Header embed ────────────────────────────────────────────
    header = discord.Embed(
        title="📜 NullSec — Server Rules",
        description=(
            "Welcome to **NullSec**, a community for cybersecurity enthusiasts, learners, and professionals.\n\n"
            "To keep this a safe and productive space, all members must follow the rules below.\n"
            "Failure to comply may result in a mute, kick, or ban at moderator discretion."
        ),
        color=COLOR_CYAN
    )
    header.set_footer(text="Last updated by NullSec Staff • NullSec")

    # ── Rules embed ─────────────────────────────────────────────
    rules = discord.Embed(color=COLOR_PURPLE)

    rules.add_field(
        name="1️⃣  Be Respectful",
        value="Treat all members with respect. No harassment, hate speech, discrimination, or personal attacks of any kind.",
        inline=False
    )
    rules.add_field(
        name="2️⃣  No Illegal Activity",
        value="Do **not** share, request, or discuss tools, exploits, or techniques intended for illegal use. "
              "Educational discussion is welcome — actively helping someone attack systems is not.",
        inline=False
    )
    rules.add_field(
        name="3️⃣  No Spam or Self-Promotion",
        value="No spam, flooding, or unsolicited advertising. Do not DM members to promote services without permission.",
        inline=False
    )
    rules.add_field(
        name="4️⃣  Keep Topics On-Point",
        value="Use the correct channels for your messages. Cybersec topics go in #cybersec channels, general chat in #general-chat, etc.",
        inline=False
    )
    rules.add_field(
        name="5️⃣  No NSFW Content",
        value="This is a professional community. NSFW, explicit, or offensive content is strictly forbidden.",
        inline=False
    )
    rules.add_field(
        name="6️⃣  No Doxxing",
        value="Never share anyone's personal information (real name, address, phone number, etc.) without their explicit consent.",
        inline=False
    )
    rules.add_field(
        name="7️⃣  English Only in Main Channels",
        value="Please keep conversations in English in the main channels so everyone can participate.",
        inline=False
    )
    rules.add_field(
        name="8️⃣  Listen to Staff",
        value="Moderators and Admins have the final say. If you disagree with a decision, bring it up respectfully in a DM — do not argue in public channels.",
        inline=False
    )
    rules.add_field(
        name="9️⃣  No Account Sharing",
        value="One person per account. Sharing accounts or using alt accounts to evade bans is not allowed.",
        inline=False
    )
    rules.add_field(
        name="🔟  Have Fun & Learn",
        value="This community exists to learn and grow together. Share knowledge, help each other, and enjoy the journey. Stay curious. Stay secure. 🔒",
        inline=False
    )

    # ── Footer embed ────────────────────────────────────────────
    footer = discord.Embed(
        description=(
            "By participating in **NullSec** you agree to these rules.\n"
            "For questions or to report an issue, DM a staff member or use the mod channels."
        ),
        color=COLOR_GREEN
    )

    await channel.send(embed=header)
    await channel.send(embed=rules)
    await channel.send(embed=footer)

    await interaction.followup.send("Rules posted in #rules!", ephemeral=True)


# ─── Utility Commands ───────────────────────────────────────────

@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping_command(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    if latency < 100:
        status = "🟢 Excellent"
    elif latency < 200:
        status = "🟡 Good"
    else:
        status = "🔴 High"

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** {latency}ms\n**Status:** {status}",
        color=COLOR_GREEN
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Show server information")
async def serverinfo_command(interaction: discord.Interaction):
    guild = interaction.guild

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=COLOR_CYAN,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
    embed.add_field(name="🔒 Verification", value=str(guild.verification_level).capitalize(), inline=True)
    embed.add_field(name="📅 Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)

    embed.set_footer(text="NullSec Bot")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Show information about a user")
@app_commands.describe(member="The user to look up")
async def userinfo_command(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    embed = discord.Embed(
        title=f"👤 {member.display_name}",
        color=member.color if member.color != discord.Color.default() else COLOR_CYAN,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=str(member), inline=True)
    embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
    embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="📥 Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
    embed.add_field(name="🎭 Top Role", value=member.top_role.mention, inline=True)

    roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
    if roles:
        embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles[:10]), inline=False)

    embed.set_footer(text="NullSec Bot")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Show a user's avatar")
@app_commands.describe(member="The user whose avatar to show")
async def avatar_command(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    embed = discord.Embed(
        title=f"🖼️ {member.display_name}'s Avatar",
        color=COLOR_CYAN
    )
    embed.set_image(url=member.display_avatar.with_size(1024).url)
    embed.set_footer(text="NullSec Bot")
    await interaction.response.send_message(embed=embed)


# ─── Error Handling ─────────────────────────────────────────────

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    msg = ""
    if isinstance(error, app_commands.MissingPermissions):
        msg = "You don't have permission to use this command."
    elif isinstance(error, app_commands.CommandOnCooldown):
        msg = f"Slow down! Try again in {error.retry_after:.1f} seconds."
    else:
        msg = f"An error occurred: {str(error)}"
        print(f"[ERROR] {error}")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"Error: {msg}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {msg}", ephemeral=True)
    except Exception:
        pass



# ─── Warn System ────────────────────────────────────────────────

@bot.tree.command(name="warn", description="Warn a member and log it")
@app_commands.describe(member="Member to warn", reason="Reason for the warning")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn_command(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    gid = str(interaction.guild.id)
    uid = str(member.id)
    if gid not in warnings_db:
        warnings_db[gid] = {}
    if uid not in warnings_db[gid]:
        warnings_db[gid][uid] = []
    warnings_db[gid][uid].append(reason)
    count = len(warnings_db[gid][uid])
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has been warned.",
        color=COLOR_YELLOW,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Warnings", value=str(count), inline=True)
    embed.set_footer(text=f"Warned by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
    try:
        await member.send(f"⚠️ You have been warned in **{interaction.guild.name}**\nReason: {reason}\nTotal warnings: {count}")
    except Exception:
        pass


@bot.tree.command(name="warnings", description="View a member's warning history")
@app_commands.describe(member="Member to check")
@app_commands.checks.has_permissions(manage_messages=True)
async def warnings_command(interaction: discord.Interaction, member: discord.Member):
    gid = str(interaction.guild.id)
    uid = str(member.id)
    warns = warnings_db.get(gid, {}).get(uid, [])
    embed = discord.Embed(
        title=f"📋 Warnings — {member.display_name}",
        color=COLOR_YELLOW if warns else COLOR_GREEN
    )
    if warns:
        for i, w in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i}", value=w, inline=False)
    else:
        embed.description = "✅ This member has no warnings."
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="slowmode", description="Set the slowmode delay for the current channel")
@app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode_command(interaction: discord.Interaction, seconds: int):
    if seconds < 0 or seconds > 21600:
        await interaction.response.send_message("❌ Slowmode must be between 0 and 21600 seconds.", ephemeral=True)
        return
    await interaction.channel.edit(slowmode_delay=seconds)
    if seconds == 0:
        msg = f"⏰ Slowmode **disabled** in {interaction.channel.mention}."
    else:
        msg = f"⏰ Slowmode set to **{seconds}s** in {interaction.channel.mention}."
    await interaction.response.send_message(msg)


@bot.tree.command(name="lock", description="Lock the current channel so members can't send messages")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock_command(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    embed = discord.Embed(
        title="🔒 Channel Locked",
        description=f"{interaction.channel.mention} has been locked. Members can no longer send messages.",
        color=COLOR_RED
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unlock", description="Unlock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock_command(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = None
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    embed = discord.Embed(
        title="🔓 Channel Unlocked",
        description=f"{interaction.channel.mention} has been unlocked. Members can send messages again.",
        color=COLOR_GREEN
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="announce", description="Post a formatted announcement to #announcements")
@app_commands.describe(title="Announcement title", message="Announcement body", ping="Ping @everyone?")
@app_commands.checks.has_permissions(administrator=True)
async def announce_command(interaction: discord.Interaction, title: str, message: str, ping: bool = False):
    await interaction.response.defer(ephemeral=True)
    channel = discord.utils.get(interaction.guild.text_channels, name="announcements")
    if not channel:
        await interaction.followup.send("❌ Could not find #announcements channel.", ephemeral=True)
        return
    embed = discord.Embed(
        title=f"📢 {title}",
        description=message,
        color=COLOR_CYAN,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text=f"Announced by {interaction.user.display_name}")
    content = "@everyone" if ping else None
    await channel.send(content=content, embed=embed)
    await interaction.followup.send(f"✅ Announcement posted in {channel.mention}!", ephemeral=True)


@bot.tree.command(name="uptime", description="Show how long the bot has been running")
async def uptime_command(interaction: discord.Interaction):
    elapsed = int(time.time() - bot_start_time)
    days = elapsed // 86400
    hours = (elapsed % 86400) // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    embed = discord.Embed(
        title="⏱️ Bot Uptime",
        description=f"`{days}d {hours}h {minutes}m {seconds}s`",
        color=COLOR_GREEN
    )
    embed.set_footer(text="NullSec Bot • Running since last restart")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="remind", description="Set a reminder that DMs you after X minutes")
@app_commands.describe(minutes="Minutes until reminder", reminder="What to remind you about")
async def remind_command(interaction: discord.Interaction, minutes: int, reminder: str):
    if minutes < 1 or minutes > 1440:
        await interaction.response.send_message("❌ Minutes must be between 1 and 1440 (24 hours).", ephemeral=True)
        return
    await interaction.response.send_message(f"⏰ Got it! I'll DM you in **{minutes} minute(s)** about: {reminder}", ephemeral=True)
    await asyncio.sleep(minutes * 60)
    try:
        await interaction.user.send(f"⏰ **Reminder!**\n{reminder}\n\n*(Set {minutes} minute(s) ago in {interaction.guild.name})*")
    except Exception:
        pass


class PollView(discord.ui.View):
    def __init__(self, options: list, author_id: int):
        super().__init__(timeout=None)
        self.votes: dict = {label: 0 for label in options}
        self.voted: set = set()
        self.author_id = author_id
        for label in options:
            self.add_item(PollButton(label))


class PollButton(discord.ui.Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        if interaction.user.id in view.voted:
            await interaction.response.send_message("❌ You already voted!", ephemeral=True)
            return
        view.voted.add(interaction.user.id)
        view.votes[self.label] += 1
        total = sum(view.votes.values())
        results = "\n".join(
            f"{opt}: **{cnt}** vote(s) ({int(cnt/total*100) if total else 0}%)"
            for opt, cnt in view.votes.items()
        )
        await interaction.response.send_message(f"✅ Vote recorded!\n\n**Current results:**\n{results}", ephemeral=True)


@bot.tree.command(name="poll", description="Create a poll with up to 4 options")
@app_commands.describe(question="The poll question", option1="Option 1", option2="Option 2", option3="Option 3 (optional)", option4="Option 4 (optional)")
async def poll_command(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = "", option4: str = ""):
    options = [o for o in [option1, option2, option3, option4] if o.strip()]
    embed = discord.Embed(
        title=f"📊 {question}",
        description="Vote using the buttons below!",
        color=COLOR_PURPLE,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    for i, opt in enumerate(options, 1):
        embed.add_field(name=f"Option {i}", value=opt, inline=True)
    embed.set_footer(text=f"Poll by {interaction.user.display_name}")
    view = PollView(options, interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


# ─── Run the Bot ────────────────────────────────────────────────
if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("=" * 50)
        print("⚠️  Please set your bot token!")
        print("   Option 1: Set DISCORD_BOT_TOKEN environment variable")
        print('   Option 2: Replace YOUR_BOT_TOKEN_HERE in this file')
        print("=" * 50)
        print()
        print("📝 How to get a bot token:")
        print("   1. Go to https://discord.com/developers/applications")
        print("   2. Click 'New Application' and give it a name")
        print("   3. Go to 'Bot' tab → click 'Reset Token' → copy the token")
        print("   4. Enable 'Message Content Intent' and 'Server Members Intent'")
        print("   5. Go to 'OAuth2' → 'URL Generator'")
        print("      - Scopes: 'bot', 'applications.commands'")
        print("      - Permissions: Administrator (or specific perms)")
        print("   6. Copy the generated URL and open it in your browser to invite the bot")
        print()
    else:
        bot.run(TOKEN)
