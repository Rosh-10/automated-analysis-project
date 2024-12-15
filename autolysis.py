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
Analyze the data from the following dataset. , 

Your script should work with any valid CSV file.Provide a detailed analysis based on the following data summary: {analysis}

Since you don't know in advance what the data looks like, don't make assumptions. Instead, perform a generic analysis that will apply to all datasets. For example:

1. Provide summary statistics for the numeric columns (mean, median, std, min, max, etc.).
2. Count the missing values in each column.
3. Generate a correlation matrix for the numeric columns.
4. Detect and handle any outliers or anomalies in the data.
5. Apply clustering algorithms to detect groups or patterns in the data (if applicable).
6. If there are time-related columns, perform time series analysis to identify trends.
7. If location or geographic data exists, perform geographic analysis.
8. Use network analysis to detect patterns of connectivity (if relevant).
9. Provide suggestions for further analyses, such as regression analysis or feature importance.

Please keep in mind:

- Do not send the entire dataset to the LLM. Focus on sending summaries, statistics, or specific pieces of analysis that will be helpful.
- If one type of analysis doesn't work, feel free to try another or ask the LLM for further analysis suggestions.

For code:
- Ask the LLM to provide Python code for the above analyses. Use caution, as running the LLM’s code may result in errors and cause your script to fail. Ensure to catch any exceptions.
- Export the resulting visualizations (e.g., heatmaps, histograms, etc.) as PNG files, and save them with distinct file names.

For summaries:
- After performing the analysis, ask the LLM to summarize the findings. Include insights discovered, and implications of those findings (e.g., what decisions to make based on these insights).
- Write the analysis and insights into a well-structured README.md file.

For visualizations:
- Use libraries like Seaborn or Matplotlib to create and export charts. Ensure they are labeled properly with titles, axis labels, and legends.
- If the analysis includes a correlation matrix, visualize it as a heatmap. If it includes time series analysis, plot the data over time.

Please remember to save all generated charts as PNG files, and do not send the entire dataset to the LLM.
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
