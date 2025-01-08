import os
from openai import OpenAI
from openai import AssistantEventHandler
from typing_extensions import override


# Define the relative path to the key.txt file
key_file_path = os.path.join(os.path.dirname(__file__), "../config/key.txt")
with open(key_file_path, "r") as file:
    line = file.readline().strip()

key = line.split("=")[1]
client = OpenAI(
        api_key = key
    )

viper = client.beta.assistants.create(
    name="Viper",
    instructions="",
    model="gpt-4o-mini"
)

thread = client.beta.threads.create()

class EventHandler(AssistantEventHandler):
    
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
        
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
            for output in delta.code_interpreter.outputs:
                if output.type == "logs":
                    print(f"\n{output.logs}", flush=True)


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


while True:
    print()
    message = input("you > ")
    if message == "exit":
        break
    send_message(message)