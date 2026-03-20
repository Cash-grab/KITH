# 1. Use a lightweight Python image
FROM python:3.11-slim

# 2. Set build arguments & working directory inside container
WORKDIR /app

# 3. Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the app source
COPY . .

# 5. Expose flask port (default)
EXPOSE 5000

# 6. Use environment variables for config and ensure best practice
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 7. Run the app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "3", "--threads", "2"]
