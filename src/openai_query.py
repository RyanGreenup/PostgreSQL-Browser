import os
import requests
from collections import namedtuple
from warning_types import issue_warning, OpenAIWarning

Message = namedtuple("Message", ["system", "prompt"])


class OpenAIQueryManager:
    def __init__(self, url="http://localhost:11434"):
        self.url = url
        self.api_key = self.get_openai_api_key()

    @staticmethod
    def get_openai_api_key():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            issue_warning(
                "OpenAI API key not found. Set the OPENAI_API_KEY environment variable.",
                OpenAIWarning,
            )
        return api_key

    def make_request(self, api_url, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    def _get_openai_completion(self, model, prompt, max_tokens=100):
        payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens}
        api_url = f"{self.url}/v1/completions"
        return self.make_request(api_url, payload)

    def _get_openai_chat_response(
        self, model: str, prompt: str, system_message: str, max_tokens=100
    ):
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
        api_url = f"{self.url}/v1/chat/completions"
        return self.make_request(api_url, payload)

    def get_openai_completion_string(self, model, prompt, max_tokens=100) -> str:
        response = self._get_openai_completion(model, prompt, max_tokens)
        return self.completion_response_to_string(response)

    @staticmethod
    def warning_empty_response():
        issue_warning("No choices found in response", OpenAIWarning)

    @classmethod
    def completion_response_to_string(cls, response) -> str:
        response = dict(response)
        if choice := response.get("choices"):
            if first_choice := choice[0]:
                if text := first_choice.get("text"):
                    return text
                else:
                    cls.warning_empty_response()
            else:
                cls.warning_empty_response()
        else:
            cls.warning_empty_response()
        return str(response)

    @classmethod
    def chat_response_to_string(cls, response) -> str | None:
        response = dict(response)
        out = None
        if d := response.get("choices"):
            if d := d[0]:
                if d := d.get("message"):
                    if d := d.get("content"):
                        out = d
        if not out:
            cls.warning_empty_response()
            return out
        else:
            return cls.strip_code_fence(out)

    def get_chat_completion_string(
        self, model: str, prompt: str, system_message: str, max_tokens=100
    ) -> str | None:
        response = self._get_openai_chat_response(
            model, prompt, system_message, max_tokens
        )
        out_string = self.chat_response_to_string(response)
        return out_string

    @staticmethod
    def strip_code_fence(text: str) -> str:
        code_fence = "```"
        lines = text.split("\n")
        lines_without_code_fence = [li for li in lines if code_fence not in li.strip()]
        return "\n".join(lines_without_code_fence)

    def get_ollama_models(self) -> list[str]:
        api_url = f"{self.url}/api/tags"
        response = requests.get(api_url)
        if response.status_code == 200:
            try:
                model_and_size = [
                    (m["name"], m["size"]) for m in response.json()["models"]
                ]
                # sort by size
                model_and_size.sort(key=lambda x: x[1])
                # Return only the model names
                return [m[0] for m in model_and_size]
            except Exception as e:
                issue_warning(
                    f"Failed to retrieve available Ollama models: {str(e)}",
                    OpenAIWarning,
                )
                return []
        else:
            issue_warning(
                f"{response.status_code} Error Failed to retrieve available Ollama models",
                OpenAIWarning,
            )
            return []

    def get_available_models(self) -> list[str]:
        models = self.get_ollama_models()
        api_url = f"{self.url}/v1/models"
        try:
            response = self.make_request(api_url, payload={})
            models = [model["id"] for model in response.get("data", [])]
            models += self.get_ollama_models()
            return sorted(models)
        except Exception as e:
            # TODO this is erroneous
            # Consider an ollama flag to enable/disable
            issue_warning(
                f"Failed to retrieve available models: {str(e)}", OpenAIWarning
            )
            return models

    @staticmethod
    def build_prompt_from_schema(schema: str, message: str) -> Message:
        system = """
        You create SQL queries for Postgresql. Answer only with the SQL query.

        You will be given a context and an instruction.
        The context contains a sql schema that you must use to write a sql query to complete the task.
        Return only the sql query.

        Quote all table and column names that contain uppercase letters as
        this is required in Postgresql.

        For example the following query is valid as it contains uppercase letters which are quoted:


        ```sql
        SELECT t."Id" FROM "Field" FROM "Table" t;
        ```

        """
        prompt = f"""
        ## Context
        ### Schema
        Here is the schema you must work with:

        {schema}

        ### SQL Structure
        Quote all table and column names that contain uppercase letters as
        this is required in Postgresql.

        For example the following query is valid as it contains uppercase letters which are quoted:


        ```sql
        SELECT t."Id" FROM "Field" FROM "Table" t;
        ```
        ## Instruction
        Complete the following task:

        Write a SQL query to: {message}.

        Return only the SQL query. Quote all table and column names.
        """
        return Message(system, prompt)

    def completion_from_schema(
        self, schema: str, model: str, message: str, max_tokens=300
    ) -> str | None:
        prompt = self.build_prompt_from_schema(schema, message)
        if output_sql := self.get_openai_completion_string(
            model, prompt, max_tokens=max_tokens
        ):
            return output_sql
            # if output_sql := self._quote_table_names(model, output_sql):
            #     return output_sql
        issue_warning("No response from completion", OpenAIWarning)
        return None

    def chat_completion_from_schema(
        self, schema: str, model: str, message: str, max_tokens=300
    ) -> str | None:
        prompt = self.build_prompt_from_schema(schema, message)
        response = self._get_openai_chat_response(
            model, prompt.prompt, prompt.system, max_tokens=max_tokens
        )
        output_query = self.chat_response_to_string(response)
        if not output_query:
            issue_warning("No response from chat completion", OpenAIWarning)
        # pyperclip.copy(prompt)
        print("## System")
        print(prompt.system)
        print("## user")
        print(prompt.prompt)
        return output_query

    def _update_ai_response(
        self,
        model: str,
        ai_output: str,
        before_prompt: str,
        after_prompt: str,
        system_message: str,
        max_tokens: int = 100,
    ) -> str | None:
        prompt = f"""
        Given the following SQL query, {before_prompt}:
            {ai_output}
        {after_prompt}
        """
        if output := self.get_chat_completion_string(
            model, prompt, system_message, max_tokens=max_tokens
        ):
            return output
        issue_warning("No response from chat completion", OpenAIWarning)
        return None

    def _quote_table_names(
        self, model: str, prompt: str, max_tokens: int = 100
    ) -> str | None:
        # prompt = f"""
        # Given the following SQL query, quote all table and column names:
        #     {prompt}
        # Respond only with the SQL query.
        # """
        system_message = """
        You are expert SQL query writer. Answer only with the SQL query.
        """

        if output := self._update_ai_response(
            model,
            prompt,
            (
                r'quote all table and field names names using `"`, the output should look something like this:\n'
                "```sql\n"
                'SELECT "Id" FROM "Field"\n'
                "```"
            ),
            "Respond only with the SQL query.",
            system_message,
            max_tokens,
        ):
            return output
        issue_warning("No response from chat completion", OpenAIWarning)
        return None

    def _query_improve(
        self, model: str, prompt: str, max_tokens: int = 100
    ) -> str | None:
        system_message = """
        You are expert SQL query writer. Answer only with the SQL query.
        """

        if output := self._update_ai_response(
            model,
            prompt,
            r"Rewrite it to follow all best practices of SQL",
            "Respond only with the SQL query.",
            system_message,
            max_tokens,
        ):
            return output
            if output := self._quote_column_names(model, output):
                return output
        issue_warning("No response from chat completion", OpenAIWarning)
        return None


if __name__ == "__main__":
    # Example usage
    query_manager = OpenAIQueryManager()

    # Simple completion example
    response = query_manager._get_openai_completion(
        "phi3", "Once upon a time, there was"
    )
    response = query_manager.completion_response_to_string(response)
    print(response)

    # With Schema example
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
    prompt = query_manager.build_prompt_from_schema(schema=iris_3nf, message=task)
    response = query_manager._get_openai_chat_response(
        "phi3", system_message=prompt.system, prompt=prompt.prompt
    )
    response = query_manager.chat_response_to_string(response)
    print(response)

    # Get available models
    available_models = query_manager.get_available_models()
    print("Available models:")
    for model in available_models:
        print(f"- {model}")
