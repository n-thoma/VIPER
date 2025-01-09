import os
from openai import OpenAI
from openai import AssistantEventHandler
from typing_extensions import override

# Module imports
from modules.m_time import *


# ---------------------------------------------------------------------------------------------------------------------
#   Initializing the OpenAI client and creating the Viper assistant
# ---------------------------------------------------------------------------------------------------------------------

# Extract API Key from file
key_file_path = os.path.join(os.path.dirname(__file__), "../config/key.txt")
with open(key_file_path, "r") as file:
    line = file.readline().strip()

key = line.split("=")[1]

# Initialize the OpenAI client with key
client = OpenAI(
        api_key = key
    )

# Create the Viper assistant
viper = client.beta.assistants.create(
    name="Viper",
    instructions="Your name is Viper, an acroynm for Virtual Intelligent Processing and Enhanced Reponse. You are a home assistant designed to help with a variety of tasks. You are designed to be a helpful and friendly assistant, always ready to assist with whatever you can.",
    model="gpt-4o-mini",
    tools=[
        {
            "type": "function",
            "function": {
            "name": "get_current_time",
            "description": "Get the current time of the current location."
            }
        },
        {
            "type": "function",
            "function": {
            "name": "get_current_date",
            "description": "Get the current date of the current location."
            }
        },
    ]
)

# Create a thread for the assistant
thread = client.beta.threads.create()


# ---------------------------------------------------------------------------------------------------------------------
#   Define the event handler class for Viper
# ---------------------------------------------------------------------------------------------------------------------

class EventHandler(AssistantEventHandler):
    
    @override
    def on_event(self, event):
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.handle_requires_action(event.data, run_id)

    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
        
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        # For all tools that require action
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            output_str = ""

            # Extract function and call it with proper arg
            if tool.function.name == "get_current_time":
                output_str = f"The current time is {get_current_time()}. Make sure you tell the user what the time is in a more human-friendly way. Don't include the seconds unless told to do so by the user."
            elif tool.function.name == "get_current_date":
                output_str = f"The current date is {get_current_date()}. Make sure you tell the user what the date is in a more human-friendly way."

            # Append output to tool_outputs arr
            tool_outputs.append({"tool_call_id": tool.id, "output": str(output_str)})

        self.submit_tool_outputs(tool_outputs, run_id)

    # Submits output from function calls to the assistant
    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=thread.id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler()
        ) as stream:
            stream.until_done()


# ---------------------------------------------------------------------------------------------------------------------
#   Viper Functions
# ---------------------------------------------------------------------------------------------------------------------

def send_message(message):

    # Send the message to the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    # Stream the messages from the thread and waits for stream to be done
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=viper.id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()


# ---------------------------------------------------------------------------------------------------------------------
#   Update Loop
# ---------------------------------------------------------------------------------------------------------------------

while True:
    print()
    message = input("you > ")
    if message == "exit":
        break
    send_message(message)
