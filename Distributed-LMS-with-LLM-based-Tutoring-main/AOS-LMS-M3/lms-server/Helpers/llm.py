from Importers.common_imports import *
from Importers.common_methods import *
from Database.methods import *

MODEL_PATH = "./Model/Phi-3-Context-Obedient-RAG-Q4_K_M.gguf"


# Helper functions for formatting messages
def format_chat_template(messages):
    """Format the chat history into the model's input template."""
    formatted_input = ""
    for message in messages:
        if message['role'] == 'user':
            formatted_input += "<|user|>\n" + message['content'] + "\n<|end|>\n<|assistant|>\n"
        elif message['role'] == 'assistant':
            formatted_input += message['content'] + "\n<|end|>\n"
    return formatted_input


def construct_message(role, content):
    """Create a message dictionary."""
    return {"role": role, "content": content}


class ModelPipeline:
    def __init__(self, model, context_limit=1):


        self.system = [
            construct_message("user",
                              "You are a virtual assistant capable of only answering questions related to Science and Technology. If the question is unrelated, reply in denial."),
            construct_message("user", "What is an Operating System?"),
            construct_message("assistant",
                              "An operating system is software that enables applications to interact with a computer's hardware.")
        ]
        self.context = []
        self.model = model
        self.context_limit = context_limit

    def add_message(self, message):
        user_message = construct_message("user", message)

        current_context = self.system + self.context[
                                        -(self.context_limit * 2):]
        current_context.append(user_message)

        model_input = format_chat_template(current_context)
        output = self.model(model_input, max_tokens=80, top_p=0.5, temperature=0.6)
        output_text = output['choices'][0].get("text", "").strip()
        lines = output_text.split("\n")
        output_text = "".join(lines)
        assistant_message = construct_message("assistant", output_text)
        self.context.append(user_message)
        self.context.append(assistant_message)

        return output_text


model = Llama(model_path=MODEL_PATH, verbose=False, use_mlock=True,device="cuda")


# Create a chat interface
def Chat():
    pipeline = ModelPipeline(model)

    return pipeline
