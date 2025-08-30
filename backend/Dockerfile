# Use the official Python image as a parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer cache.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code (main.py) and your data file (openapi.json)
# into the container's /app directory.
COPY main.py .
COPY openapi.json .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# This is the command that will run when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]