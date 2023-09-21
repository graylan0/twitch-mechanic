import openai
import json
import sqlite3
from asgiref.sync import sync_to_async
from .models import StoryEntry
from .trideque import TriDeque

class StoryGenerator:
    MAX_PAST_ENTRIES = 100  # maximum number of past entries to store in memory

    def __init__(self, character_memory):
        self.character_memory = character_memory
        self.past_story_entries = TriDeque(self.MAX_PAST_ENTRIES)
        self.job_config = self.load_job_config()
        initial_prompt = self.construct_initial_prompt()
        self.past_story_entries.push(
            StoryEntry(
                story_action='',
                narration_result=initial_prompt
            )
        )

    def load_job_config(self):
        with open('JobConfig.json', 'r') as f:
            return json.load(f)

    def construct_initial_prompt(self, config_name='config1'):
        rules = self.job_config['configurations'][config_name]['initial_prompt_rules']
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=self.construct_prompt_messages(rules, config_name),
        )
        initial_prompt = response['choices'][0]['message']['content']
        return initial_prompt

    def construct_prompt_messages(self, story_action: str, config_name='config1'):
        system_message_content = self.job_config['configurations'][config_name]['system_message_content']
        messages = [
            {
                'role': 'system',
                'content': system_message_content,
            },
        ]
        
        for story_entry in self.past_story_entries:
                if story_entry.story_action:
                    messages += [{'role': 'user',
                                  'content': story_entry.story_action}]
                if story_entry.narration_result:
                    messages += [
                        {
                            'role': 'assistant',
                            'content': story_entry.narration_result,
                        }
                    ]
        # Add character's past actions to the messages
        for action in self.character_memory.past_actions:
            messages.append({'role': 'user', 'content': action.content})
        messages.append({'role': 'user', 'content': story_action})
        return messages

    @sync_to_async
    def generate_next_story_narration(self, story_action: str):
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-16k',
                messages=self.construct_prompt_messages(story_action),
            )
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return None

        next_narration = response['choices'][0]['message']['content']
        self.past_story_entries.push(
            StoryEntry(
                story_action=story_action,
                narration_result=next_narration
            )
        )

 
        return next_narration

    def reset(self):
        self.past_story_entries = TriDeque(self.MAX_PAST_ENTRIES)
        initial_prompt = self.construct_initial_prompt()
        self.past_story_entries.push(
            StoryEntry(
                story_action='',
                narration_result=initial_prompt
            )
        )
