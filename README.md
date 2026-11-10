# Student Task Manager

A Flask app for tracking study and personal tasks. It supports categories, due dates, completion, and restoring deleted tasks.

## Run locally

1. Create a Python virtual environment and install dependencies with `pip install -r requirements.txt`.
2. Start the app with `python app.py`.
3. Open `http://127.0.0.1:5000`.

## Deploy on Render

This repository includes `render.yaml`. In Render, create a Blueprint from this repository and deploy the `student-task-manager` web service. Render generates the Flask `SECRET_KEY` automatically.

The app stores tasks in a local SQLite database (`tasks.db`). Render's free web service does not provide persistent local storage, so task data may be lost when the service restarts or redeploys. The local database is excluded from Git.

This app has no user login. Anyone who can open the public website can see and change its task list. Do not store sensitive information in it.
