from flask import Flask, request, jsonify, abort
import os
import json
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

class Log:
    @staticmethod
    def time_str():
        current = datetime.now(timezone(timedelta(hours=8)))
        return current.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def log(file_name, log_type, content):
        content = "[%s] %s | %s"%(log_type, Log.time_str(), str(content).replace("\n", "\n    "))
        with open(file_name, "a") as f:
            f.write("%s\n"%content)
    
    @staticmethod
    def message(file_name, content):
        return Log.log( file_name, "MSG",content)
    
    @staticmethod
    def error(file_name, content):
        return Log.log(file_name,"ERR",  content)
    
    @staticmethod
    def warning(file_name, content):
        return Log.log(file_name, "WRN", content)


app = Flask(__name__)
os.environ['TOGETHER_API_KEY'] = os.getenv('TOGETHER_API_KEY')

client = OpenAI(
    api_key=os.getenv('TOGETHER_API_KEY'),
    base_url="https://api.together.xyz/v1"
)

@app.route('/api/together/completion', methods=["POST"])
def together_completion():
    # Set up logging directories
    tt = datetime.now(timezone(timedelta(hours=8)))
    day = tt.strftime("%Y-%m-%d")
    hour = tt.strftime("%H")
    log_dir = f"log/{day}/{hour}"
    log_msg_path = os.path.join(log_dir, "completion.log")
    log_data_path = os.path.join(log_dir, "completion.jsonl")
    os.makedirs(log_dir, exist_ok=True)

    try:
        # Send request to Together API
        response = client.chat.completions.create(**request.json)
    except Exception as e:

        error_message = str(e)
        Log.error(log_msg_path, error_message)
        print(f"[Error] {error_message}")
        
        # Handle specific API error cases
        if "exceeded your current quota" in error_message or "deactivate" in error_message:
            Log.error("log/exceed.log", error_message)  # Log quota errors
            
        return abort(500, error_message)

    # Log successful response
    Log.message(log_msg_path, "Successful")
    with open(log_data_path, "a+") as f:
        f.write(json.dumps({
            "request": request.json,
            "response": response.choices[0].message.content
        }) + "\n")

    response_dict = response.to_dict()
    return jsonify(response_dict)

if __name__ == '__main__':
    app.run("0.0.0.0", port=10001)