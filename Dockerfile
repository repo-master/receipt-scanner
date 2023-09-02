FROM python:3.11.4-slim-bookworm

WORKDIR /app

# ENV FLASK_APP=dash_app:create_app()

# Copy requirements file and install
COPY ./requirements.txt ./requirements.txt
RUN pip3 install -q -r requirements.txt

# Copy all app files to /app folder
COPY . /app

# TODO: Use gunicorn
CMD /app/entry.sh
