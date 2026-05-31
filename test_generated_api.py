def test_get_project_tasks_completed(api_request_context):
    project_id = "123e4567-e89b-12d3-a456-426614174000"  # Example project_id
    url = f"/api/v1/projects/{project_id}/tasks"
    headers = {
        "Authorization": "Bearer mock_token_123",
        "X-Client-ID": "Automation_Suite"
    }
    params = {
        "status": "completed"
    }

    response = api_request_context.get(url, headers=headers, params=params)

    assert response.status == 200

    response_body = response.json()
    assert isinstance(response_body, list)

    for task in response_body:
        assert "task_id" in task
        assert "title" in task
        assert isinstance(task["task_id"], str)  # Assuming task_id is a string
        assert isinstance(task["title"], str)   # Assuming title is a string