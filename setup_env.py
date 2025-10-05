import os
from dotenv import load_dotenv  # Optional: for loading later in your code

def prepare_env_file():
    env_path = '.env'
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write('# Environment variables for API keys and credentials\n')
            f.write('OPENAI_API_KEY=your_openai_key_here  # For later LLM, but needed for embeddings in scoring\n')
            f.write('LINKEDIN_EMAIL=your_linkedin_email\n')
            f.write('LINKEDIN_PASSWORD=your_linkedin_password  # For login; use app password if 2FA\n')
        print(f".env file created in {os.getcwd()}")
        return True
    else:
        print(".env file already exists.")
        return False

# Run the function
prepare_env_file()

# To load the vars in your code later:
# load_dotenv()  # This makes os.getenv('OPENAI_API_KEY') work
