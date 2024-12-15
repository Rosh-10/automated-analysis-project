# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "httpx",
#   "chardet",
#   "python-dotenv",
#   "tenacity",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import httpx
import chardet
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

# Force non-interactive matplotlib backend
matplotlib.use('Agg')

# Load environment variables
load_dotenv()

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

if not AIPROXY_TOKEN:
    raise ValueError("API token not set. Please set AIPROXY_TOKEN in the environment.")

def load_data(file_path):
    """Load CSV data with encoding detection."""
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        encoding = result['encoding']
        return pd.read_csv(file_path, encoding=encoding)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)

def analyze_data(df):
    """Perform basic data analysis."""
    numeric_df = df.select_dtypes(include=['number'])  # Select only numeric columns
    analysis = {
        'summary': df.describe(include='all').to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict()  # Compute correlation only on numeric columns
    }
    return analysis

from PIL import Image

def visualize_data(df, output_dir):
    """Generate and save low-quality visualizations."""
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns
    for column in numeric_columns:
        plt.figure()
        sns.histplot(df[column].dropna(), kde=True)
        plt.title(f'Distribution of {column}')
        
        # Save the plot as PNG temporarily
        temp_file_path = os.path.join(output_dir, f'{column}_distribution.png')
        plt.savefig(temp_file_path, dpi=150)  # Save at higher DPI temporarily
        plt.close()

        # Open the temporary PNG file and save it as JPEG with reduced quality
        with Image.open(temp_file_path) as img:
            # Save the image as JPEG with lower quality
            img = img.convert('RGB')  # Ensure it's in RGB mode for JPEG
            img.save(
                os.path.join(output_dir, f'{column}_distribution.jpg'),
                'JPEG',
                quality=30  # Set the JPEG quality to 30 (lower quality)
            )

        # Optionally, delete the temporary PNG file
        os.remove(temp_file_path)


@retry(wait=wait_exponential(), stop=stop_after_attempt(5))
def generate_narrative(analysis):
    """Generate narrative using LLM."""
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = f"Provide a detailed analysis based on the following data summary: {analysis}"
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = httpx.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        raise
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze datasets and generate insights.")
    parser.add_argument("file_path", help="Path to the dataset CSV file.")
    parser.add_argument("-o", "--output_dir", default="output", help="Directory to save outputs.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load data
    df = load_data(args.file_path)

    # Analyze data
    analysis = analyze_data(df)

    # Visualize data
    visualize_data(df, args.output_dir)

    # Generate narrative
    narrative = generate_narrative(analysis)

    # Save narrative
    with open(os.path.join(args.output_dir, 'README.md'), 'w') as f:
        f.write(narrative)

if __name__ == "__main__":
    main()
