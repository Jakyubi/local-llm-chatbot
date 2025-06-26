import subprocess
import sys
import os
import shutil
import textwrap
import threading
import time

if sys.platform == "win32":
    os.system("")


class Colors:
    USER = '\033[92m'       #green
    ASSISTANT = '\033[94m'  #blue
    ERROR = '\033[91m'      #red
    SYSTEM = '\033[90m'     #gray
    RESET = '\033[0m'       #reset

#formats and prints history
def print_history(history: str):
    border = "=" * 40
    print(f"\n{Colors.SYSTEM}{border}")
    print(" CURRENT CHAT HISTORY")
    print(border + Colors.RESET)

    margin = ' ' * 4  # lewy margines

    lines = history.strip().split("\n")
    for line in lines:
        if line.startswith("User:"):
            content = line[len("User:"):].strip()
            print(f"{Colors.SYSTEM}{margin}User:{Colors.RESET}")
            print_with_margins(content, left_margin=8, color=Colors.SYSTEM)
            print()
        elif line.startswith("Assistant:"):
            content = line[len("Assistant:"):].strip()
            print(f"{Colors.SYSTEM}{margin}Assistant:{Colors.RESET}")
            print_with_margins(content, left_margin=8, color=Colors.SYSTEM)
            print()
        else:
            # system prompt lub inne linie
            print(f"{Colors.SYSTEM}{margin}{line}{Colors.RESET}")

    print(f"{Colors.SYSTEM}{border}\n{Colors.RESET}")

#estimated token count
def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)

#trim history to context limit of model, leaving first line - system promt untouched
def trim_history_to_limit(history: str, max_context: int) -> str:
    lines = history.strip().split("\n")
    system_prompt = lines[0]
    other_lines = lines[1:]

    while count_tokens(system_prompt + "\n" + "\n".join(other_lines)) > max_context and len(other_lines) > 0:
        other_lines.pop(0)
    return system_prompt + "\n" + "\n".join(other_lines) + "\n"

#format text with margins and wrapping
def print_with_margins(text, left_margin=4, right_margin=4, color=Colors.RESET):
    columns = shutil.get_terminal_size().columns
    usable_width = max(20, columns-left_margin - right_margin)
    margin = ' ' * left_margin

    lines = text.split('\n')
    for line in lines:
        wrapped = textwrap.wrap(line, width=usable_width)
        if not wrapped:
            print()
        else:
            for wline in wrapped:
                print(f"{color}{margin}{wline}{Colors.RESET}")
        sys.stdout.flush()

#cleans response of ai-generated user: lines (only for history)
def clean_response(response: str) -> str:
    parts = response.split("\nUser:",1)
    response = parts[0].strip()
    return response

#unused run function, generates whole ai answer at once
'''
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
'''


#runs 'ollama run <model> <prompt>, streaming one chunk of text at time, doesn't wait for whole answer to generate
#without threads process may get stuck while printing ai answer
def run_ollama_streaming(model_name: str, prompt: str) -> str:
    try:
        process = subprocess.Popen(
            ["ollama", "run", model_name, prompt],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True,
            encoding = "utf-8",
            bufsize = 1
        )

        output_lines = []
        buffer = ""

        def read_stdout():
            nonlocal buffer
            started_printing = False
            while True:
                chunk = process.stdout.readline()
                if chunk == '':
                    break
                buffer += chunk
                if '\n' in buffer:
                    parts = buffer.split('\n')
                    for line in parts[:-1]:
                        if not started_printing and line.strip() == "":
                            continue
                        #stops when ai tries to generate user: prompt
                        if line.strip().startswith("User:"): 
                            return
                        started_printing = True
                        print_with_margins(line)
                        output_lines.append(line.strip())
                    buffer = parts[-1]
            if buffer.strip():
                print_with_margins(buffer)
                output_lines.append(buffer.strip())
        def read_stderr():
            for _ in iter(process.stderr.readline, ''):
                pass
        
        t_out = threading.Thread(target=read_stdout)
        t_err = threading.Thread(target=read_stderr)

        t_out.start()
        t_err.start()

        process.wait()
        t_out.join()
        t_err.join()

        while output_lines and output_lines[0] == "":
            output_lines.pop(0)
        while output_lines and output_lines[-1] == "":
            output_lines.pop()

        return "\n".join(output_lines).strip()
    
    except Exception as e:
        return f"Error: {e}"
        

        

    
def main():
    model = "openhermes25"  #select llm model to run
    max_context = 8000      #max context of your model
    print(f"{Colors.SYSTEM}Welcome! Type 'exit' to quit, commands: /reset, /history, /style [name] - change style (normal,)\n{Colors.RESET}")

    #starting style
    current_style = "normal"

    #here you can add or modify styles
    style_prompts = {
        "normal" : "You are a helpful AI assistant. Provide clear, polite, and formal answers. Do not invent User inputs. Only respond as Assistant."
    }

    history = style_prompts[current_style] + "\n" #start of history, can act as system prompt

    #main loop
    while True:
        user_input = input(f"{Colors.USER}User: {Colors.RESET}").strip()
        if user_input.lower() in ("exit"): #close with 'exit'
            print(f"{Colors.SYSTEM}Exiting...{Colors.RESET}")
            break

        if user_input == "/history":
            print_history(history)
            continue

        if user_input.startswith("/style"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1] in style_prompts:
                current_style = parts[1]
                history = style_prompts[current_style] + "\n"
                print(f"{Colors.SYSTEM}Style changed to '{current_style}'. History reset.{Colors.RESET}\n")
            else:
                print(f"{Colors.ERROR}Unknown style. Available: {', '.join(style_prompts.keys())}{Colors.RESET}\n")
            continue

        if user_input == "/reset":
            history = style_prompts[current_style] + "\n"
            print(f"{Colors.SYSTEM}History reset.{Colors.RESET}\n")
            continue
        
        
        history += f"User: {user_input}\nAssistant: " #add user input to history
        
        print(f"{Colors.SYSTEM}Processing...{Colors.RESET}")
        print(f"{Colors.ASSISTANT}Assistant:{Colors.RESET}\n")  #print model's response
        
        start_time = time.perf_counter()
        raw_response = run_ollama_streaming(model, history) #run model with history as prompt
        end_time = time.perf_counter()
        response = clean_response(raw_response)
        
        #calculate estimated tokens per second
        token_count = count_tokens(response)
        elapsed = end_time - start_time
        tps = token_count / elapsed if elapsed > 0 else float('inf')
        print(f"{Colors.SYSTEM}Performance: {token_count} tokens generated in {elapsed:.2f} s -> {tps:.2f} tokens/s{Colors.RESET}\n")

        history += response + "\n" #add response to history
        history = trim_history_to_limit(history, max_context)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
        sys.exit(0)
        