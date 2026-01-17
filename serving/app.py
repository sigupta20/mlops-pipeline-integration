from flask import Flask, request, jsonify
from google.cloud import aiplatform
from config import PROJECT_ID, REGION, ENDPOINT_ID

app = Flask(__name__)

# Initialize Vertex AI once
aiplatform.init(project=PROJECT_ID, location=REGION)

endpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}"
)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    if not data or "instances" not in data:
        return jsonify({"error": "Missing 'instances' field"}), 400

    try:
        response = endpoint.predict(
            instances=data["instances"]
        )

        return jsonify({
            "predictions": response.predictions
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
