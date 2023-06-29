import json
import logging

import backoff
import openai
import regex
import tiktoken

from SocAI.models.chatgpt.instruction import instruction


class ChatGPTResponseParsingError(Exception):
    pass


class ChatGPT:
    def __init__(self, api_key):
        openai.api_key = api_key

    @backoff.on_exception(backoff.expo,
                          ChatGPTResponseParsingError,
                          max_time=3)
    def ask(self, question):

        model = 'gpt-3.5-turbo-16k'

        maxtokens = 16384
        tokens_by_reponse = 500


        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": ''},
        ]

        messages_tokens = num_tokens_from_messages(messages)

        question_length = maxtokens - tokens_by_reponse - messages_tokens

        messages[1]["content"] = truncated_string(question.replace('\\', ''), question_length, model)

        try:
            response = openai.ChatCompletion.create(
                model=model,
                n=1,
                max_tokens=tokens_by_reponse,
                messages=messages)

            message = response.choices[0]['message']['content']
            return parse_chatgpt_response(message)

        except openai.error.AuthenticationError as e:
            raise openai.error.AuthenticationError("Error during OpenAI authentication: Failed to authenticate the "
                                                   "API credentials.") from e
        except ChatGPTResponseParsingError:
            raise

        except Exception as e:
            # handle exception
            raise Exception("Error asking chatgpt", e)


def parse_chatgpt_response(chatgpt_string_response):
    try:
        pattern = regex.compile(r'{(?:[^{}]|(?R))*}')

        if matches := pattern.findall(chatgpt_string_response):
            extracted_dict = matches[0]
        else:
            raise Exception(f"No dictionary found in the ChatGPT response: {chatgpt_string_response}")

        chatgpt_dict_response = json.loads(extracted_dict)

        required_keys = ["classification", "reasoning", "next_steps"]
        if not all(key in chatgpt_dict_response for key in required_keys):
            raise Exception("Response does not have all the required keys.")

        return chatgpt_dict_response

    except json.JSONDecodeError:
        error_message = "Failed parsing ChatGPT response: Invalid JSON format."
        logging.error(error_message)
        raise ChatGPTResponseParsingError(error_message)

    except Exception as e:
        error_message = f"Failed parsing ChatGPT response: {e}"
        logging.error(error_message)
        raise ChatGPTResponseParsingError(error_message)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-16k"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-16k")
    elif model == "gpt-4":
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-16k":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def truncated_string(
        string: str,
        max_tokens: int,
        model: str = 'gpt-3.5-turbo',
        print_warning: bool = True,
) -> str:
    """Truncate a string to a maximum number of tokens."""
    encoding = tiktoken.encoding_for_model(model)
    encoded_string = encoding.encode(string)
    return encoding.decode(encoded_string[:max_tokens])
