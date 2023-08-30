# Run the Abot backend server in production-ready mode (gunicorn)

FROM python:3.11.5-bullseye

# Copy requirements file and install
COPY ./requirements.txt ./requirements.txt
RUN pip install -q -r requirements.txt

# Copy all app files to /app folder
COPY . /app

CMD ["python" "dash_app.py"]
