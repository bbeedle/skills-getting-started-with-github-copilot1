"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    global activities
    # Store original activities
    original_activities = copy.deepcopy(activities)
    
    # Reset to original state before each test
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    
    yield
    
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)


class TestActivitiesEndpoint:
    """Test cases for GET /activities endpoint"""
    
    def test_get_activities_success(self):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify structure of activity data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        # Verify specific data
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
    
    def test_get_activities_returns_json(self):
        """Test that activities endpoint returns JSON format"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"


class TestSignupEndpoint:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up newstudent@mergington.edu for Chess Club"
        
        # Verify student was added to the activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Non-existent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_student_already_registered(self):
        """Test signup when student is already registered"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_multiple_different_activities(self):
        """Test student can signup for multiple different activities"""
        email = "multistudent@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]
    
    def test_signup_url_encoding(self):
        """Test signup with URL-encoded activity names"""
        # Test with spaces in activity name
        response = client.post(
            "/activities/Programming%20Class/signup?email=encoded@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up encoded@mergington.edu for Programming Class"


class TestUnregisterEndpoint:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # michael@mergington.edu is already in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unregistered michael@mergington.edu from Chess Club"
        
        # Verify student was removed from the activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
        # daniel should still be there
        assert "daniel@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_unregister_activity_not_found(self):
        """Test unregistration from non-existent activity"""
        response = client.delete(
            "/activities/Non-existent Club/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_student_not_registered(self):
        """Test unregistration when student is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Student not registered for this activity"
    
    def test_unregister_url_encoding(self):
        """Test unregistration with URL-encoded activity names and emails"""
        # First signup the student
        client.post("/activities/Programming%20Class/signup?email=test%2Buser@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=test%2Buser@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "test+user@mergington.edu" in data["message"]


class TestRootEndpoint:
    """Test cases for root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    def test_complete_signup_and_unregister_flow(self):
        """Test complete flow: signup -> verify -> unregister -> verify"""
        email = "integration@mergington.edu"
        activity = "Chess Club"
        
        # Initial state - student not registered
        activities_response = client.get("/activities")
        initial_data = activities_response.json()
        assert email not in initial_data[activity]["participants"]
        initial_count = len(initial_data[activity]["participants"])
        
        # Step 1: Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        after_signup_data = activities_response.json()
        assert email in after_signup_data[activity]["participants"]
        assert len(after_signup_data[activity]["participants"]) == initial_count + 1
        
        # Step 2: Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = client.get("/activities")
        after_unregister_data = activities_response.json()
        assert email not in after_unregister_data[activity]["participants"]
        assert len(after_unregister_data[activity]["participants"]) == initial_count
    
    def test_prevent_double_signup_after_unregister(self):
        """Test that a student can't signup twice, even after unregistering and re-registering"""
        email = "double@mergington.edu"
        activity = "Programming Class"
        
        # Signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Try to signup again (should fail)
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        
        # Unregister
        response3 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response3.status_code == 200
        
        # Signup again (should work)
        response4 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response4.status_code == 200