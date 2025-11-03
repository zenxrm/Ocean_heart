from flask import Flask, render_template, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

try:
    logger.info("Attempting to load model...")
    model = load_model('FishSpeciesClassifier.h5')
    logger.info("Model loaded successfully")
    
    input_shape = model.input_shape
    output_shape = model.output_shape
    logger.info(f"Model input shape: {input_shape}")
    logger.info(f"Model output shape: {output_shape}")
    
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    model = None

fish_species = {
    0: "Bangus",
    1: "Big Head Carp",
    2: "Black Spotted Barb",
    3: "Catfish", 
    4: "Climbing Perch",
    5: "Fourfinger Threadfin",
    6: "Freshwater Eel",
    7: "Glass Perchlet",
    8: "Goby",
    9: "Gold Fish",
    10: "Gourami",
    11: "Grass Carp",
    12: "Green Spotted Puffer",
    13: "Indian Carp",
    14: "Indo-Pacific Tarpon",
    15: "Jaguar Gapote",
    16: "Janitor Fish",
    17: "Knifefish",
    18: "Long-Snouted Pipefish",
    19: "Mosquito Fish",
    20: "Mudfish",
    21: "Mullet",
    22: "Pangasius",
    23: "Perch",
    24: "Scat Fish",
    25: "Silver Barb",
    26: "Silver Carp",
    27: "Silver Perch",
    28: "Snakehead",
    29: "Tenpounder",
    30: "Tilapia"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'success': False, 'error': 'Model not loaded. Check server logs.'}), 500

    if 'file' not in request.files:
        logger.warning("No file part in request")
        return jsonify({'success': False, 'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("No selected file")
        return jsonify({'success': False, 'error': 'No selected file'}), 400

    if file:
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        
        try:
            if not os.path.exists(upload_dir):
                logger.info(f"Creating uploads directory at {upload_dir}")
                os.makedirs(upload_dir)
                
            img_path = os.path.join(upload_dir, file.filename)
            logger.info(f"Saving uploaded file to {img_path}")
            file.save(img_path)
            
            if not os.path.exists(img_path):
                logger.error(f"File not saved at {img_path}")
                return jsonify({'success': False, 'error': 'Failed to save uploaded file'}), 500
                
            target_size = (128, 128)
            logger.info(f"Using target size: {target_size}")

            logger.info(f"Loading image with target size {target_size}")
            img = image.load_img(img_path, target_size=target_size)
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize

            logger.info("Making prediction")
            prediction = model.predict(img_array)
            logger.info(f"Raw prediction shape: {prediction.shape}")
            logger.info(f"Raw prediction values: {prediction}")
            
            predicted_class = int(np.argmax(prediction, axis=1)[0])
            confidence = float(np.max(prediction) * 100)  # Convert to percentage
            
            logger.info(f"Predicted class index: {predicted_class}")
            logger.info(f"Confidence: {confidence}%")
            
            species_name = fish_species.get(predicted_class, f"Unknown Species (Class {predicted_class})")
            
            return jsonify({
                'success': True,
                'class': predicted_class,
                'species': species_name,
                'confidence': round(confidence, 2)
            })
            
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error processing image: {error_message}")
            logger.error(f"Stack trace: {stack_trace}")
            return jsonify({
                'success': False,
                'error': f"Error processing image: {error_message}"
            }), 500

if __name__ == '__main__':
    app.run(debug=True)