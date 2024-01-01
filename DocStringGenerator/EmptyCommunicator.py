from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator

class EmptyCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()

    def ask(self, prompt, replacements) -> APIResponse:
        return APIResponse('Ok', True)
