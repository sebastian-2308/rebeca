from .config import Config
from .llm import LLMClient
from .prompts import TOOL_DESCRIPTION_PROMPT
from .tools import parse_tool_call, execute_tool


def run_agent_simple(config: Config) -> None:
    llm = LLMClient(config)
    messages = [
        {"role": "system", "content": config.system_prompt + "\n\n" + TOOL_DESCRIPTION_PROMPT},
    ]

    while True:
        try:
            user_input = input(" You: ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input.strip():
            continue
        if user_input.strip().lower() == "exit":
            break
        if user_input.strip().lower() == "reset":
            messages = [
                {"role": "system", "content": config.system_prompt + "\n\n" + TOOL_DESCRIPTION_PROMPT},
            ]
            continue

        messages.append({"role": "user", "content": user_input})

        for turn in range(config.max_turns):
            response_text = llm.send_message(messages)
            messages.append({"role": "assistant", "content": response_text})

            tool_call = parse_tool_call(response_text)

            if tool_call is None:
                reminder = "[SYSTEM: You MUST use a tool. Say nothing else. Just output the tool call JSON.]"
                print(f" [system: missing tool call, reminding...]")
                messages.append({"role": "user", "content": reminder})
                continue

            tool_name, params = tool_call

            if tool_name == "say":
                print(f" Rebeca: {params.get('text', '')}")
                break

            result_text = execute_tool(tool_name, params)
            print(f"  \u2699 {tool_name}(...)")
            short = result_text[:200].replace("\n", " ")
            if len(result_text) > 200:
                short += "..."
            print(f"  \u21b3 {short}")
            messages.append({"role": "user", "content": f"Tool result for {tool_name}:\n{result_text}"})
        else:
            print(" Rebeca: (max turns reached)")
