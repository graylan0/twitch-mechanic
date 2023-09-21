import asyncio
import sys
import logging
from typing import Optional
import sqlite3
import openai
from twitchio.ext import commands
from twitchio.channel import Channel
from .config import config
from .models import Proposal
from .story_generator import StoryGenerator

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class LlmGameHooks:
    def on_get_narration_result(self, narration_result: str, proposal: Proposal, proposal_id: int):
        pass


class LlmGame:
    def __init__(self):
        pass

    def add_proposal(self, story_action: str, author: str):
        pass

    def vote(self, proposal_id: int):
        pass

    def end_vote(self):
        pass

    def restart(self):
        pass

class LlmTwitchBot(commands.Bot, LlmGameHooks):
    max_message_len = 500  # Twitch has a 500 character limit

    def __init__(self, llm_game: LlmGame):
        # Initialise our Bot with our access token, prefix, and a list of channels to join on boot...
        super().__init__(
            token=config.twitch_bot_client_id,
            prefix='!',
            initial_channels=[config.twitch_channel_name],
        )
        self.game = llm_game
        self.channel: Optional[Channel] = None

    async def _extract_message_text(self, ctx: commands.Context) -> str:
        """
        Extract the text part of a user message after the command
        (i.e., "bar baz" from the message "!foo bar baz")
        Perform content moderation and skip unwanted messages.
        """
        message_text = ctx.message.content.split(' ', 1)[1]

        return message_text
   
    async def event_ready(self):
        """Function that runs when the bot connects to the server"""
        asyncio.get_running_loop().set_debug(True)
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        self.channel = self.get_channel(config.twitch_channel_name)
    
        initial_story_message = f'Starting Twitch Mechanic: {self.game.initial_story_message}'
        for i in range(0, len(initial_story_message), self.max_message_len):
            chunk = initial_story_message[i:i+self.max_message_len]
            await self.channel.send(chunk)

    @commands.command()
    async def action(self, ctx: commands.Context):
        """Trigger for the user to perform an action within the game"""
        story_action = await self._extract_message_text(ctx)
        user = ctx.author.name
        await self._propose_story_action(story_action, user)

    @commands.command()
    async def mechanic(self, ctx: commands.Context):
        """Trigger for the user to say something within the game"""
        story_action = 'Generating 🤖 for "' + await self._extract_message_text(ctx) + '"'
    
        await self._propose_story_action(story_action, ctx.author.name)

    @commands.command()
    async def vote(self, ctx):
        await self._vote(ctx)

    @commands.command()
    async def help(self, ctx: commands.Context):
        """Help command"""
        await self._send(
            'Welcome to the Mechanic AI 🤖 Using OpenAI. use !mechanic then your question to use the mechanic bot. Info: github.com/graylan0 built for twitch.tv/retrononymous_".'
        )

    # --- MOD COMMANDS ---

    @commands.command()
    async def reset(self, ctx: commands.Context):
        """Resets the game if the user is a mod"""
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return

        self.game.restart()
        await self._send(f'Game has been reset | {self.game.initial_story_message}')

    @commands.command()
    async def modvote(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return
        await self._vote(ctx, weight=99)

    @commands.command()
    async def endvote(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await self._send(ctx.author.name + ', You are not a mod')
            return
        self.game.end_vote()

    # --- Other Methods ---

    async def _vote(self, ctx: commands.Context, weight: int = 1):
        """Trigger for the user to vote on the next action"""
        vote_option_str = await self._extract_message_text(ctx)

        try:
            proposal = self.game.vote(int(vote_option_str))
            new_count = proposal.vote
        except ValueError:
            await self._send(f'Invalid vote option: {vote_option_str}')
        else:
            await self._send(
                f' {vote_option_str}. : {new_count}'
            )

    async def on_get_narration_result(
        self, narration_result: str, proposal: Proposal, proposal_id: int
    ):
        # Store the narration result in the SQLite database
        await self.save_to_database(narration_result)

    async def _propose_story_action(self, story_action: str, author: str):
        """Continues the story by performing an action, communicating the result to the channel"""
        proposal_id = self.game.add_proposal(story_action, author)
        await self._send(f' {proposal_id} : {story_action}')

    async def _send(self, message: str):
        # Sending messages to Twitch (You can customize this)
        await self.channel.send(message)

    async def openai_check_content(self, content: str) -> bool:
        try:
            prompt = (
                "You are the AI moderator for the Mechanic JobHat community. Your role is to ensure that messages "
                "follow a specific tone related to mechanics. You should check if the following message aligns with "
                "the mechanic jobhat's tone. If the message from the user does not request information or engagement "
                "related to mechanics, you should reply with a single word: 'unwanted'."
                f"\n\nMessage to evaluate: '{content}'"
            )

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are the AI moderator for the Mechanic JobHat community."},
                    {"role": "user", "content": f"{prompt}"}
                ]
            )

            moderation_result = response['choices'][0]['message']['content'].strip()
            return moderation_result != "unwanted"
        except Exception as e:
            print(f"OpenAI Check Error: {e}")
            return False

    async def save_to_database(self, data_to_save):
        # First, check the content using OpenAI
        is_content_allowed = await self.openai_check_content(data_to_save)
        if not is_content_allowed:
            print("Content not allowed by OpenAI moderation.")
            return

        # Connect to the SQLite database and store data
        conn = sqlite3.connect('extra_replies.db')
        cursor = conn.cursor()

        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extra_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extra_content TEXT
                )
            ''')

            cursor.execute('INSERT INTO extra_replies (extra_content) VALUES (?)', (data_to_save,))
            conn.commit()

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            conn.close()

    async def _send_chunked(self, text: str):
        while text:
            suffix = '...' if len(text) >= self.max_message_len else ''
            await self._send(text[: self.max_message_len - 3] + suffix)
            print(text[: self.max_message_len - 3] + suffix)
            await asyncio.sleep(2.0)
            text = text[self.max_message_len - 3 :]
