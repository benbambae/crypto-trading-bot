# Full
FROM python:3.12-slim

# Set working dir
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of your code
COPY . .

# Set entry command to run your bot
CMD ["python", "src/bot.py"]
