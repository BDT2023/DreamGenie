from flask import Flask, abort, request
from tempfile import NamedTemporaryFile

from faster_whisper import WhisperModel
import torch
#import whisper

# Check if NVIDIA GPU is available
torch.cuda.is_available()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model_size = "medium"
# Load the Whisper model:
# model = whisper.load_model(model_size, device=DEVICE)
model = WhisperModel(model_size, device="cuda", compute_type="int8")

app = Flask(__name__)


@app.route("/")
def hello():
    return "Whisper Hello World!"


@app.route("/whisper", methods=["POST"])
def handler():
    if not request.files:
        # If the user didn't submit any files, return a 400 (Bad Request) error.
        abort(400)

    # For each file, let's store the results in a list of dictionaries.
    results = []

    # Loop over every file that the user submitted.
    for filename, handle in request.files.items():
        # Create a temporary file.
        # The location of the temporary file is available in `temp.name`.
        temp = NamedTemporaryFile(delete=False)
        # Write the user's uploaded file to the temporary file.
        # The file will get deleted when it drops out of scope.
        handle.save(temp)
        temp.close()
        # Let's get the transcript of the temporary file.
        # This returns segments, so we need to modify them:
        segments, info = model.transcribe(temp.name, language='en')
        result = {}
        result["text"] = " ".join([seg.text for seg in segments])
        # Now we can store the result object for this file.
        results.append(
            {
                "filename": filename,
                "transcript": result["text"],
            }
        )

    # This will be automatically converted to JSON.
    return {"results": results}
