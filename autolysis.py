# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "httpx",
#   "chardet",
#   "python-dotenv",
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

def visualize_data(df, output_dir):
    """Generate and save visualizations."""
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns
    for column in numeric_columns:
        plt.figure()
        sns.histplot(df[column].dropna(), kde=True)
        plt.title(f'Distribution of {column}')
        plt.savefig(os.path.join(output_dir, f'{column}_distribution.png'))
        plt.close()

def generate_narrative(analysis):
    """Generate narrative using LLM."""
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = f"Provide a detailed analysis based on the following data summary: {analysis}"
    prompt = f"""
Provide a detailed analysis based on the following data summary: {analysis}.

Please ensure that your analysis includes the following:

1. **Repository Requirements:**
   - Verify that your repository is **public** and has an **MIT License**.
   - Ensure the following files are present:
     - `autolysis.py`
     - `<dataset_name>/README.md` and `<dataset_name>/*.png` (replace <dataset_name> with the dataset's name, e.g., "goodreads", "happiness", "media", etc.)

2. **Execution Requirements:**
   - Confirm that running `uv run autolysis.py <dataset_name>.csv` works **without errors** using the instructor's `AIPROXY_TOKEN` environment variable.
   - Ensure that the following runs successfully and generates the correct output for any dataset:
     - `uv run autolysis.py <dataset_name>.csv` (Creates `<dataset_name>/README.md` and `<dataset_name>/*.png` files)
   
3. **Code Quality:**
   - Make sure your code is well structured, logically organized, and adheres to a **consistent coding style**.
   - Utilize appropriate **statistical methods** and **innovative analysis** in your code. The analysis should adapt dynamically based on the dataset's characteristics.
   - Use effective **visualizations** that have titles, axis labels, and legends, and incorporate appropriate color schemes. The visualizations should be meaningful for any dataset.

4. **Narrative Crafting:**
   - Craft a clear, context-rich narrative that provides an in-depth description of the data, the analysis performed, the insights gained, and their implications. This should be adaptable to any dataset.
   - Properly **format the narrative** in Markdown with well-structured sections (e.g., data description, analysis, insights, etc.).
   - Integrate the **visualizations** at relevant points in the narrative to enhance the understanding of the findings.

5. **LLM Usage:**
   - Minimize token usage by sending concise prompts and avoid sending large data in the prompt.
   - Implement dynamic prompts and function calls to guide the LLM efficiently.
   - If applicable, utilize **vision capabilities** and **multiple LLM calls** for agentic workflows to improve the analysis.

Please ensure the output files (`README.md` and `.png`) generated are well-designed and relevant, illustrating key findings of your analysis, and that they adapt to the characteristics of any dataset.
"""

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
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return "Narrative generation failed due to an error."

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
