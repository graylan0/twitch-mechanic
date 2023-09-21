import asyncio
import openai
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import sqlite3
from .llm_game import LlmGame
from .llm_game import CharacterMemory
from .llm_twitch_bot import LlmTwitchBot
from .models import Proposal, StoryEntry
from .story_generator import StoryGenerator
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI()

# We need to maintain a reference to running coroutines to prevent GC
background_task = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.on_event('startup')
async def on_startup():
    global background_task
    app.state.game = game = LlmGame()
    app.state.bot = bot = LlmTwitchBot(game)
    game.hooks = bot
    background_task = asyncio.create_task(bot.start())

@app.get('/proposals')
def get_proposals() -> List[Proposal]:
    game: LlmGame = app.state.game
    return game.proposals

@app.get('/story-history')
def get_story_history() -> List[StoryEntry]:
    game: LlmGame = app.state.game
    return game.generator.past_story_entries

@app.get('/vote-time-remaining')
def get_vote_time_remaining():
    game: LlmGame = app.state.game
    remaining_time = game.calculate_remaining_time()
    return {"remaining_time": remaining_time}

@app.post("/generate-image")
async def generate_image():
    character_memory = CharacterMemory()
    generator = StoryGenerator(character_memory)
    scene_description = await generator.generate_image_prompt()
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: openai.Image.create(
        prompt=scene_description,
        n=1,
        size="512x512"
    ))
    return {"image": response['data'][0]['url']}

@app.get("/get_mechanic_reply/")
async def get_mechanic_reply():
    conn = sqlite3.connect('extra_replies.db')
    c = conn.cursor()
    c.execute("SELECT extra_content FROM extra_replies ORDER BY id DESC LIMIT 5")
    extra_replies = [row[0] for row in c.fetchall()]
    conn.close()
    return {"extra_replies": extra_replies}