import unittest
import json
from src.app import app

class WorkoutAPITestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_create_workout(self):
        workout = {
            'exercise': 'Bench Press',
            'sets': 3,
            'reps': 10,
            'weight': 135
        }
        response = self.app.post('/workouts',
                                data=json.dumps(workout),
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)
    
    def test_get_workouts(self):
        response = self.app.get('/workouts')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
