import requests
import json
import pandas as pd
import io

def fetch_json_from_url(url):
    """
    Fetches a JSON file from the given URL and returns its content as a Python object.

    Args:
        url (str): The URL of the JSON file.

    Returns:
        dict or list: A Python object representing the JSON content if successful,
                      otherwise None.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # E.g. 404, 500
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}") # E.g. DNS failure, refused connection
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred: {req_err}")
    except json.JSONDecodeError as json_err:
        print(f"Error decoding JSON from response: {json_err}")
    return None


def load_json_file(file_path):
    """
    Loads the content of a JSON file and returns it as a Python object.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict or list: A Python object representing the JSON content.
                      Returns None if the file cannot be read or is invalid JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_object = json.load(f)
        return json_object
    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file at '{file_path}' contains invalid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# Example usage (you can uncomment and modify this to test):
# # Fetch JSON from URL
# json_data = fetch_json_from_url('https://api.github.com/users/octocat')
# if json_data:
#     print("JSON fetched successfully:")
#     print(json_data)
#     print(f"Type of loaded object: {type(json_data)}")

# # Load JSON from file
# my_json_data = load_json_file('example.json')
# if my_json_data:
#     print("JSON loaded successfully:")
#     print(my_json_data)
#     print(f"Type of loaded object: {type(my_json_data)}")



def download_and_parse_file(url):
    """Downloads a file from a URL and attempts to parse it as a CSV using pandas."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        # Assuming it's a CSV file, use pandas to read it
        df = pd.read_csv(io.StringIO(response.text))
        return df.to_dict(orient='records')
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6+
    except Exception as err:
        print(f"An error occurred: {err}")
    return None