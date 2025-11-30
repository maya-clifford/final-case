from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from src.database import get_db
from bson import ObjectId
import os

app = Flask(__name__)
CORS(app)
db = get_db()
workouts_collection = db['workouts']

def serialize_workout(workout):
    workout['_id'] = str(workout['_id'])
    return workout

@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "workout-tracker"}), 200

@app.route('/workouts', methods=['POST'])
def create_workout():
    """Create a new workout entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['exercise', 'sets', 'reps', 'weight']
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Create workout document
        workout = {
            'exercise': data['exercise'],
            'sets': int(data['sets']),
            'reps': int(data['reps']),
            'weight': float(data['weight']),
            'date': data.get('date', datetime.now().isoformat()),
            'notes': data.get('notes', ''),
            'created_at': datetime.now().isoformat()
        }
        
        result = workouts_collection.insert_one(workout)
        workout['_id'] = str(result.inserted_id)
        
        return jsonify(workout), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/workouts', methods=['GET'])
def get_workouts():
    """Get all workouts, optionally filter by exercise"""
    try:
        exercise = request.args.get('exercise')
        
        # Build query
        query = {}
        if exercise:
            query['exercise'] = {'$regex': exercise, '$options': 'i'}
        
        workouts = list(workouts_collection.find(query).sort('date', -1))
        workouts = [serialize_workout(w) for w in workouts]
        
        return jsonify(workouts), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/workouts/<workout_id>', methods=['GET'])
def get_workout(workout_id):
    """Get a specific workout by ID"""
    try:
        workout = workouts_collection.find_one({'_id': ObjectId(workout_id)})
        
        if not workout:
            return jsonify({"error": "Workout not found"}), 404
        
        return jsonify(serialize_workout(workout)), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/workouts/<workout_id>', methods=['DELETE'])
def delete_workout(workout_id):
    """Delete a workout by ID"""
    try:
        result = workouts_collection.delete_one({'_id': ObjectId(workout_id)})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Workout not found"}), 404
        
        return jsonify({"message": "Workout deleted successfully"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/pr', methods=['GET'])
def get_personal_records():
    """Get personal records (max weight) for each exercise"""
    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$exercise',
                    'max_weight': {'$max': '$weight'},
                    'total_sets': {'$sum': '$sets'},
                    'workout_count': {'$sum': 1}
                }
            },
            {
                '$project': {
                    'exercise': '$_id',
                    'max_weight': 1,
                    'total_sets': 1,
                    'workout_count': 1,
                    '_id': 0
                }
            },
            {'$sort': {'max_weight': -1}}
        ]
        
        prs = list(workouts_collection.aggregate(pipeline))
        return jsonify(prs), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/volume', methods=['GET'])
def get_volume():
    """Calculate total training volume (sets × reps × weight)"""
    try:
        exercise = request.args.get('exercise')
        query = {}
        if exercise:
            query['exercise'] = {'$regex': exercise, '$options': 'i'}
        
        workouts = list(workouts_collection.find(query))
        
        total_volume = sum(
            w['sets'] * w['reps'] * w['weight'] 
            for w in workouts
        )
        
        return jsonify({
            "exercise": exercise or "all",
            "total_volume": total_volume,
            "workout_count": len(workouts)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8080))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=True)
