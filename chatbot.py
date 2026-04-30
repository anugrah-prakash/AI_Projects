import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent

load_dotenv()


@tool
def calculator(a: float, b: float) -> str:
    """Useful for performing basic calculation with numbers."""
    return f"The difference of {a} and {b} is {a - b}"


@tool
def greet(name: str) -> str:
    """Useful for greeting a user by name."""
    return f"Hello {name}, I am your AI"


class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI Chatbot")
        self.root.geometry("500x400")

        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.agent = create_agent(model=self.model, tools=[calculator, greet])

        self.chat_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Arial", 11), state="disabled"
        )
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.user_input = tk.Entry(self.input_frame, font=("Arial", 12))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(
            self.input_frame, text="Send", command=self.send_message, width=10
        )
        self.send_button.pack(side=tk.RIGHT)

        self.add_message("Assistant", "Welcome, I am your AI assistant.")

    def add_message(self, sender, message):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def send_message(self, event=None):
        user_text = self.user_input.get().strip()

        if not user_text:
            return

        if user_text.lower() == "quit":
            self.root.destroy()
            return

        self.user_input.delete(0, tk.END)
        self.add_message("You", user_text)

        self.send_button.config(state="disabled")
        threading.Thread(
            target=self.get_bot_response, args=(user_text,), daemon=True
        ).start()

    def get_bot_response(self, user_text):
        try:
            final_state = None

            for state in self.agent.stream(
                {"messages": [HumanMessage(content=user_text)]},
                stream_mode="values",
            ):
                final_state = state

            response = final_state["messages"][-1].content

        except Exception as e:
            response = f"Error: {str(e)}"

        self.root.after(0, lambda: self.display_bot_response(response))

    def display_bot_response(self, response):
        self.add_message("Assistant", response)
        self.send_button.config(state="normal")


def main():
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
