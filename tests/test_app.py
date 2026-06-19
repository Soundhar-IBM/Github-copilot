import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    original_participants = {
        "Chess Club": ["michael@mergington.edu", "daniel@mergington.edu"],
        "Programming Class": ["emma@mergington.edu", "sophia@mergington.edu"],
        "Gym Class": ["john@mergington.edu", "olivia@mergington.edu"],
        "Basketball Team": ["sarah@mergington.edu", "alex@mergington.edu"],
        "Soccer Club": ["liam@mergington.edu", "maya@mergington.edu"],
        "Art Club": ["ava@mergington.edu", "noah@mergington.edu"],
        "Drama Club": ["mia@mergington.edu", "ethan@mergington.edu"],
    }
    
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants.copy()
    
    yield
    
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants.copy()

class TestGetActivities:
    def test_get_activities_returns_all(self, client):
        """Test that GET /activities returns all activities"""
        # Arrange
        expected_count = 7
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_count
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity in data.items():
            for field in required_fields:
                assert field in activity, f"Missing field '{field}' in {activity_name}"

class TestSignup:
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert new_email in activities[activity_name]["participants"]
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"

    def test_signup_duplicate_email(self, client):
        """Test that duplicate signup is rejected"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_invalid_activity(self, client):
        """Test signup for non-existent activity"""
        # Arrange
        invalid_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that same student can signup for different activities"""
        # Arrange
        email = "student@school.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]

class TestDeleteParticipant:
    def test_delete_participant_success(self, client):
        """Test successful deletion of a participant"""
        # Arrange
        activity_name = "Chess Club"
        email_to_delete = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email_to_delete}"
        )
        final_count = len(activities[activity_name]["participants"])
        
        # Assert
        assert response.status_code == 200
        assert email_to_delete not in activities[activity_name]["participants"]
        assert final_count == initial_count - 1

    def test_delete_nonexistent_participant(self, client):
        """Test deleting a participant that doesn't exist"""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "notaparticipant@school.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_delete_from_invalid_activity(self, client):
        """Test deleting from a non-existent activity"""
        # Arrange
        invalid_activity = "Nonexistent Club"
        email = "student@school.edu"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

class TestIntegration:
    def test_signup_then_delete(self, client):
        """Test signing up and then deleting a participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "integration@test.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        signup_successful = email in activities[activity_name]["participants"]
        
        # Act - Delete
        delete_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        delete_successful = email not in activities[activity_name]["participants"]
        
        # Assert
        assert signup_response.status_code == 200
        assert signup_successful
        assert delete_response.status_code == 200
        assert delete_successful

    def test_availability_updates_after_signup(self, client):
        """Test that availability count updates after signup"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newperson@test.edu"
        
        response1 = client.get("/activities")
        initial_participants = len(response1.json()[activity_name]["participants"])
        initial_available = response1.json()[activity_name]["max_participants"] - initial_participants
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        response2 = client.get("/activities")
        final_participants = len(response2.json()[activity_name]["participants"])
        final_available = response2.json()[activity_name]["max_participants"] - final_participants
        
        # Assert
        assert final_participants == initial_participants + 1
        assert final_available == initial_available - 1
