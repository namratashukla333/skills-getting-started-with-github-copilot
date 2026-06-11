import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        # No setup needed; activities are pre-loaded in app

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities

    def test_get_activities_includes_all_required_fields(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert all(field in activity_data for field in expected_fields), \
                f"Activity '{activity_name}' missing required fields"

    def test_get_activities_participants_list_is_populated(self, client):
        # Arrange
        # Activities have pre-populated participants

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        chess_club = activities["Chess Club"]
        assert isinstance(chess_club["participants"], list)
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        new_email = "newstudent@mergington.edu"
        activity_name = "Programming Class"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert new_email in app_module.activities[activity_name]["participants"]

    def test_signup_student_twice_returns_error(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_updates_participant_count(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        activity_name = "Gym Class"
        initial_count = len(app_module.activities[activity_name]["participants"])
        new_email = "newgymstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        updated_count = len(app_module.activities[activity_name]["participants"])
        assert updated_count == initial_count + 1

    @pytest.mark.parametrize("email", [
        "student1@mergington.edu",
        "student.two@mergington.edu",
        "student_3@mergington.edu",
    ])
    def test_signup_with_various_email_formats(self, client, activities, email):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        activity_name = "Programming Class"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert email in app_module.activities[activity_name]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_existing_participant_success(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        assert email in app_module.activities[activity_name]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in app_module.activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_returns_404(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_participant_updates_count(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(app_module.activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 200
        updated_count = len(app_module.activities[activity_name]["participants"])
        assert updated_count == initial_count - 1

    def test_remove_all_participants(self, client, activities):
        # Arrange
        from src import app as app_module
        app_module.activities = activities
        activity_name = "Chess Club"
        participants = list(app_module.activities[activity_name]["participants"])

        # Act
        for email in participants:
            response = client.delete(
                f"/activities/{activity_name}/participants/{email}"
            )
            assert response.status_code == 200

        # Assert
        assert len(app_module.activities[activity_name]["participants"]) == 0
