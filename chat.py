import subprocess
import sys

#runs 'ollama run <model> <prompt>
def run_ollama(model_name: str, prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model_name, prompt], #command tu run
            capture_output=True, #capture stdout and stderr
            text=True, #input as string
            encoding="utf-8", 
            timeout=120, #timeout exception after x seconds. Can be set to higher values on low-end pc
            check=True #exception on non-zero exit code
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Timeout expired"
    except Exception as e:
        return f"Error: {e}"
    
def main():
    model = "" #select llm model to run
    history = "\n" #start of history, can act as system prompt
    print("Welcome! Type 'exit' to quit\n")

    while True:
        user_input = input("User: ").strip() #user input
        if user_input.lower() in ("exit"): #close with 'exit'
            print("Exiting...")
            break

        history += f"User: {user_input}\nAssistant: " #add user input to history
        print("Processing...")
        response = run_ollama(model, history) #run model with history as prompt
        print(f"Assistant:\n{response}\n")  #print model's response

    history += response + "\n" #add response to history

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
        sys.exit(0)