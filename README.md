# Medi Chat - Health Chatbot

## Overview
Medi Chat is an AI-powered chatbot designed to assist users with health concerns by providing information based on a comprehensive medical knowledge base.

## Running the Application

To run the application in a production environment, use a WSGI server like Gunicorn or Waitress. Here are example commands to run the application:

### Using Gunicorn (Unix-based systems)
```bash
gunicorn -w 4 app:app
```

### Using Waitress (Windows)
1. Install Waitress:
   ```bash
   pip install waitress
   ```
2. Verify the installation:
   ```bash
   pip show waitress
   ```
3. Run the application:
   ```bash
   waitress-serve --port=5000 app:app
   ```

If you encounter an error stating that `waitress-serve` is not recognized, ensure that your Python Scripts directory is included in your system's PATH environment variable. This directory is typically located at:
```
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python<version>\Scripts
```
Replace `<YourUsername>` and `<version>` with your actual username and Python version.

### Checking Python Version
To check the version of Python installed on your system, run the following command in your command prompt or terminal:
```bash
python --version
```
or
```bash
python -V
```
If you have multiple versions of Python installed, you might need to specify `python3`:
```bash
python3 --version
```

Adjust the number of workers based on your server's capabilities.

## Deployment Instructions

This project can be deployed on cloud platforms that support Python backend applications such as Render, Heroku, or Railway.

### Prerequisites
- Ensure you have a Git repository initialized and your code committed.
- Ensure `requirements.txt` and `Procfile` are present in the project root.
- Have an account on your chosen platform (Render, Heroku, Railway).

### Deploying on Render
1. Go to [Render](https://render.com) and create a new Web Service.
2. Connect your GitHub/GitLab repository containing this project.
3. Set the build command to:
   ```
   pip install -r requirements.txt
   ```
4. Set the start command to:
   ```
   gunicorn -w 4 app:app
   ```
5. Set environment variables if needed (e.g., `SESSION_SECRET`).
6. Deploy the service and wait for it to build and start.

### Deploying on Heroku
1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
2. Log in to Heroku:
   ```
   heroku login
   ```
3. Create a new Heroku app:
   ```
   heroku create your-app-name
   ```
4. Push your code to Heroku:
   ```
   git push heroku main
   ```
5. Set environment variables if needed:
   ```
   heroku config:set SESSION_SECRET=your_secret_key
   ```
6. Scale the web dyno:
   ```
   heroku ps:scale web=1
   ```
7. Open your app:
   ```
   heroku open
   ```

### Notes
- Replace `your-app-name` with your desired app name.
- Adjust the number of Gunicorn workers based on your server capacity.
- Monitor logs for errors:
  ```
  heroku logs --tail
  ```

Feel free to reach out if you need help with deployment or further automation.
  heroku logs --tail
