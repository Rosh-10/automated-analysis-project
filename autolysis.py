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
# ///import osimport os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import openai
import subprocess
import shutil
import logging

# Constants
LLM_MODEL = "gpt-4o-mini"
DEFAULT_OUTPUT_DIR = "output"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Ensure AI Proxy Token is set
API_KEY = os.getenv("AIPROXY_TOKEN")
if not API_KEY:
    raise ValueError("Missing AIPROXY_TOKEN environment variable")
openai.api_key = API_KEY

def load_data(file_path):
    """Load dataset from the provided file path."""
    try:
        data = pd.read_csv(file_path)
        logger.info(f"Dataset loaded successfully with {data.shape[0]} rows and {data.shape[1]} columns.")
        return data
    except Exception as e:
        msg = f"Error loading dataset from {file_path}."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def perform_analysis(data):
    """Perform basic statistical and exploratory data analysis."""
    try:
        summary = data.describe(include='all')
        logger.info("Generated statistical summary.")
        return summary
    except Exception as e:
        msg = "Error performing data analysis."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def generate_visualizations(data, output_dir):
    """Generate and save visualizations for the dataset."""
    try:
        os.makedirs(output_dir, exist_ok=True)

        # Example visualization: Correlation heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(data.corr(), annot=True, cmap="coolwarm", fmt=".2f")
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.title("Correlation Heatmap")
        plt.savefig(heatmap_path)
        logger.info(f"Saved heatmap to {heatmap_path}")
        
        return [heatmap_path]
    except Exception as e:
        msg = "Error generating visualizations."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def generate_narrative(data_summary, visualization_paths):
    """Generate insights and narrative using an LLM."""
    try:
        prompt = (
            "Analyze the following data summary and visualizations, then provide a detailed narrative. "
            "Focus on key insights, statistical observations, and their implications."
            f"\n\nData Summary:\n{data_summary.to_string()}\n\n"
            f"Visualizations: {', '.join(visualization_paths)}"
        )

        response = openai.Completion.create(
            engine=LLM_MODEL,
            prompt=prompt,
            max_tokens=1024
        )

        narrative = response.choices[0].text.strip()
        logger.info("Generated narrative using LLM.")
        return narrative
    except Exception as e:
        msg = "Error generating narrative using LLM."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def save_results(narrative, output_dir):
    """Save the narrative to a Markdown file."""
    try:
        md_file_path = os.path.join(output_dir, "results.md")
        with open(md_file_path, "w") as f:
            f.write("# Analysis Results\n\n")
            f.write(narrative)
        logger.info(f"Saved narrative to {md_file_path}")
    except Exception as e:
        msg = "Error saving narrative to Markdown file."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def run_uv_script(script_path, input_csv):
    """Run the script using uv and handle outputs."""
    try:
        command = ["uv", "run", script_path, input_csv]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        logger.info(result.stdout)
        if result.returncode != 0:
            msg = f"Error running script {script_path}."
            logger.error(f"{msg} UNEXPECTED FAILURE: {result.stderr}")
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        msg = "The script timed out."
        logger.error(f"{msg} UNEXPECTED FAILURE")
        sys.exit(1)
    except Exception as e:
        msg = "Unexpected error while running script."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def clean_up_directory(repo_path):
    """Attempt to delete a directory and handle errors."""
    try:
        shutil.rmtree(repo_path, ignore_errors=False)
        logger.info(f"Successfully cleaned up the repository at {repo_path}")
    except PermissionError as e:
        msg = f"Permission denied while trying to remove {repo_path}."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        msg = f"Error cleaning up the repository at {repo_path}."
        logger.error(f"{msg} UNEXPECTED FAILURE: {e}")
        sys.exit(1)

def main():
    """Main function to orchestrate the analysis pipeline."""
    if len(sys.argv) != 3:
        print("Usage: python autolysis.py <input_csv> <output_dir>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = sys.argv[2]

    # Load data
    data = load_data(input_csv)

    # Analyze data
    data_summary = perform_analysis(data)

    # Generate visualizations
    visualization_paths = generate_visualizations(data, output_dir)

    # Generate narrative
    narrative = generate_narrative(data_summary, visualization_paths)

    # Save results
    save_results(narrative, output_dir)

    # Run uv script for additional processing
    run_uv_script(os.path.join(output_dir, "autolysis.py"), input_csv)

    # Clean up (example of where the permission issue might happen)
    repo_path = "path_to_repo"
    clean_up_directory(repo_path)

if __name__ == "__main__":
    main()
