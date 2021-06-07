# Set base image (host OS)
FROM python:3.8-alpine
RUN apk add build-base
RUN apk add gcc musl-dev python3-dev libffi-dev openssl-dev cargo
# By default, listen on port 5000
EXPOSE 8000/tcp

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY app.py .
ADD conf conf/
COPY run-server.sh .
COPY wsgi.py .
ADD pickle pickle/

# Specify the command to run on container start
CMD [ "sh", "run-server.sh" ]
