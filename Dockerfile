# Use official Python image
FROM python:3.11

# Set up a new user named "user" with user ID 1000 (Required by Hugging Face)
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Install dependencies
RUN pip install --no-cache-dir -e .

# Command to run the application (Hugging Face expects port 7860)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
