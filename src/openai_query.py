import os
import requests
from warning_types import issue_warning, OpenAIWarning


def get_openai_response(model, prompt, max_tokens=100, url="http://localhost:11434"):
    # Check if the OpenAI API key is set
    if not (api_key := os.getenv("OPENAI_API_KEY")):
        issue_warning(
            "OpenAI API key not found. Set the OPENAI_API_KEY environment variable.",
            OpenAIWarning,
        )

    # Set the appropriate headers
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Define the payload for the API request
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens}

    # The endpoint for the OpenAI completions API
    api_url = url + "/v1/completions"

    # Make the request to the OpenAI API
    response = requests.post(api_url, headers=headers, json=payload)

    # Handle different HTTP responses
    if response.status_code == 200:
        return response.json()  # Return JSON data
    else:
        # Raise an exception for non-200 responses
        raise Exception(
            f"Request failed with status {response.status_code}: {response.text}"
        )


def response_to_string(response) -> str:
    response = dict(response)

    if choice := response.get("choices"):
        if first_choice := choice[0]:
            if text := first_choice.get("text"):
                return text
            else:
                issue_warning("No text found in response", OpenAIWarning)
        else:
            issue_warning("No choices found in response", OpenAIWarning)
    else:
        issue_warning("No choices found in response", OpenAIWarning)
    return str(response)


if __name__ == "__main__":
    response = get_openai_response("phi3", "Once upon a time, there was")
    response = response_to_string(response)
    print(response)
