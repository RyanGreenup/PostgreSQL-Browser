import os
import yaml
import requests
from warning_types import issue_warning, OpenAIWarning
from collections import namedtuple

Message = namedtuple("Message", ["system", "prompt"])


def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        issue_warning(
            "OpenAI API key not found. Set the OPENAI_API_KEY environment variable.",
            OpenAIWarning,
        )
    return api_key


def make_request(api_url, headers, payload):
    response = requests.post(api_url, headers=headers, json=payload)
    # Handle different HTTP responses
    if response.status_code == 200:
        return response.json()  # Return JSON data
    else:
        # Raise an exception for non-200 responses
        raise Exception(
            f"Request failed with status {response.status_code}: {response.text}"
        )


def get_openai_completion(model, prompt, max_tokens=100, url="http://localhost:11434"):
    api_key = get_openai_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens}
    api_url = url + "/v1/completions"
    return make_request(api_url, headers, payload)


def get_openai_chat_response(
    model, prompt, system_message, max_tokens=100, url="http://localhost:11434"
):
    api_key = get_openai_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    api_url = url + "/v1/chat/completions"
    return make_request(api_url, headers, payload)


def warning_empty_response():
    issue_warning("No choices found in response", OpenAIWarning)


def completion_response_to_string(response) -> str:
    response = dict(response)

    if choice := response.get("choices"):
        if first_choice := choice[0]:
            if text := first_choice.get("text"):
                return text
            else:
                warning_empty_response()
        else:
            warning_empty_response()
    else:
        warning_empty_response()
    return str(response)


def chat_response_to_string(response) -> str | None:
    response = dict(response)

    out = None

    if d := response.get("choices"):
        if d := d[0]:
            if d := d.get("message"):
                if d := d.get("content"):
                    out = d

    if not out:
        warning_empty_response()
        return out
    else:
        return strip_code_fence(out)


def strip_code_fence(text: str) -> str:
    code_fence = "```"
    lines = text.split("\n")
    lines_without_code_fence = [li for li in lines if code_fence not in li.strip()]
    return "\n".join(lines_without_code_fence)


def build_prompt_from_schema(schema: str, message: str) -> Message:
    system = """
    You create SQL queries for Postgresql. Answer only with the SQL query.

    Don't forget that uppercase letters need to be quoted in postgresql.

    For example, note the careful attention to quoting capital letters in the following query:

    ```sql
    SELECT t.id, t.name, COUNT(_ltt."B") AS tag_count
    FROM "Tag" t
    LEFT JOIN "_LinkToTag" _ltt ON t.id = _ltt."B"
    GROUP BY t.id, t.name;
    ```
    """
    prompt = f"""
    Complete the following task:

    {message}
    """
    return Message(system, prompt)


if __name__ == "__main__":
    # Simple
    # response = get_openai_completion("phi3", "Once upon a time, there was")
    # response = completion_response_to_string(response)
    # print(response)

    # With Schema
    iris_3nf = """
    Table: IrisPlant
      Column: id, Type: integer
      Column: sepal_length, Type: real
      Column: sepal_width, Type: real
      Column: petal_length, Type: real
      Column: petal_width, Type: real
      Column: species_id, Type: integer

    Table: Species
      Column: species_id, Type: integer
      Column: species_name, Type: text
    """
    task = "List the species names and the average petal length for each species."
    prompt = build_prompt_from_schema(schema=iris_3nf, message=task)
    response = get_openai_chat_response(
        "phi3", system_message=prompt.system, prompt=prompt.prompt
    )
    response = chat_response_to_string(response)
    print(response)
