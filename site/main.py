
import sys
import os
from typing import Any
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()
from DocStringGenerator.GlobalConfig import GlobalConfig
global_config = dependencies.resolve(GlobalConfig)
global_config.mode = "web"
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.CodeProcessor import CodeProcessor, ChunkData
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.Utility import APIResponse
from DocStringGenerator.Logger import Logger
from flask import Flask, Response, request, jsonify, stream_with_context, render_template, session
import queue


code_processor = CodeProcessor()


app = Flask(__name__)
data_queue: queue.Queue[str] = queue.Queue()

available_bots = [
    {"bot": "google", "model":"bard"},
    {"bot": "openai", "model":"gpt-4-1106-preview"},
    {"bot": "anthropic", "model":"claude-2.1"},
    {"bot": "file", "model":"classTest"}
]

available_bot_names = ["google","openai","anthropic","file"]

config = {     
    "wipe_docstrings": True,
    "verbose": True,
    "include_subfolders": False,    
    "keep_responses": False,
    "class_docstrings_verbosity_level": 5,
    "function_docstrings_verbosity_level": 2,
    "example_verbosity_level":3,
    "max_line_length": 79,    
    "dry_run": True    
}

@app.route('/')
def home(): 
    dependencies.resolve(Logger, on_chunk_received)
    return render_template('index.html', available_bot_names=available_bot_names)


@app.route('/process_code', methods=['POST'])
def process_code():
    source_code = ''
    selected_chatbots: list[Any] = []
    if request.json:
        source_code = request.json.get('code')
        selected_chatbots = request.json.get('chatbots')

    if not source_code:
        return jsonify(APIResponse('', False, 'No code provided')), 400
    
    if not selected_chatbots:
        return jsonify(APIResponse('', False, 'No chatbots selected')), 400

    try:
        final_response = start_bots(source_code, selected_chatbots)
        return jsonify(final_response)

    except Exception as e:
        return jsonify(APIResponse('', False, f'An error occurred: {str(e)}')), 500
 
         
data_queues: dict[str, queue.Queue[Any]] = {
    "google": queue.Queue(),
    "openai": queue.Queue(),
    "anthropic": queue.Queue()
}


def on_chunk_received(data: ChunkData) -> None:
    bot_name = data.bot_name
    chunk = data.chunk
    if data.bot_name in data_queues:
        data_br = chunk.replace('\n', '<br>')
        data_queues[bot_name].put(data_br)


@app.route('/stream/<bot_name>')
def stream(bot_name: str):
    def generate(bot_name: str):
        while True:
            chunk = data_queues[bot_name].get()  # Get chunk from the specific bot's queue
            yield f"data: {chunk}\n\n"

    if bot_name in data_queues:
        return Response(stream_with_context(generate(bot_name)), mimetype='text/event-stream')
    else:
        return jsonify(APIResponse('',False, "Invalid bot name")), 400          

def start_bots(source_code: str, selected_chatbots: list[str]):
    config_manager = ConfigManager()
    config_manager.update_config(config)

    enabled_bots: list[dict[str, str]] = [bot for bot in available_bots if bot["bot"] in selected_chatbots]
    all_responses: list[Any] = []  # To store responses from each bot

    for bot_info in enabled_bots:
        model = bot_info.get('model')
        switch_bot(bot_info['bot'], model if model else '')
        response = code_processor.process_code(source_code)
        
        if response.is_valid:
            all_responses.append(response.content)
        else:
            # Handle invalid response case
            all_responses.append(f"Error processing with {bot_info['bot']}: {response.content}")

    # Consolidate responses and return an APIResponse
    final_content = '\n'.join(all_responses)  # You can format this as per your requirement
    return APIResponse(final_content, True, "Processing completed") if all_responses else APIResponse('', False, "No responses")          
    
def switch_bot(bot: str, model: str):
    # Set bot and model configuration
    ConfigManager().set_config("bot", bot)
    ConfigManager().set_config("model", model)
    communicator_manager = dependencies.resolve(CommunicatorManager)
    communicator_manager.initialize_bot_communicator()    

def start_bot(bot_info: dict[str, Any], source_code: str):
    bot = bot_info['bot']
    model = bot_info.get('model')
    switch_bot(bot, model if model else '')
    final_response = code_processor.process_code(source_code)
    if not final_response.is_valid:
        failed_files = final_response.content
        for file in failed_files:
            data_queues[bot].put(f"Failed to process {file.file_name}: {file.response}")
    return final_response


if __name__ == '__main__':
    app.run(debug=True)