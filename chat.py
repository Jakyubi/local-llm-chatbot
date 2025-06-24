import subprocess
import sys
import os

if sys.platform == "win32":
    os.system("")


class Colors:
    USER = '\033[92m'       #green
    ASSISTANT = '\033[94m'  #blue
    ERROR = '\033[91m'      #red
    SYSTEM = '\033[90m'     #gray
    RESET = '\033[0m'       #reset

def print_history(history: str):
    border = "=" * 40
    print(f"\n{Colors.SYSTEM}{border}")
    print(" CURRENT CHAT HISTORY")
    print(border)
    print(history)
    print(border + "\n" + Colors.RESET)

#runs 'ollama run <model> <prompt>
def run_ollama(model_name: str, prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model_name, prompt], #command tu run
            capture_output=True,            #capture stdout and stderr
            text=True,                      #input as string
            encoding="utf-8", 
            timeout=120,                    #timeout exception after x seconds. Can be set to higher values on low-end pc
            check=True                      #exception on non-zero exit code
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Timeout expired"
    except Exception as e:
        return f"Error: {e}"
    
def main():
    model = "openhermes25" #select llm model to run
    history = "You are a helpful AI assistant. Provide clear, polite, and formal answers. Do not invent User inputs. Only respond as Assistant.\n" #start of history, can act as system prompt
    print(f"{Colors.SYSTEM}Welcome! Type 'exit' to quit, commands: /history.\n{Colors.RESET}")

    while True:
        user_input = input(f"{Colors.USER}User: {Colors.RESET}").strip() #user input
        if user_input.lower() in ("exit"): #close with 'exit'
            print(f"{Colors.SYSTEM}Exiting...{Colors.RESET}")
            break
        if user_input == "/history":
            print_history(history)
            continue

        history += f"User: {user_input}\nAssistant: " #add user input to history
        print(f"{Colors.SYSTEM}Processing...{Colors.RESET}")
        response = run_ollama(model, history) #run model with history as prompt
        print(f"{Colors.ASSISTANT}Assistant:{Colors.RESET}\n{response}\n")  #print model's response

        history += response + "\n" #add response to history

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
        sys.exit(0)