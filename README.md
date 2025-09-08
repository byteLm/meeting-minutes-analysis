# Meeting Minutes Analysis

## Overview
This project analyzes meeting minutes ("atas") from the CBH committee, extracting insights and organizing the data for further text mining and analysis. It processes PDF files, generates structured datasets, and provides tools for exploring the content of the meetings.

## Features
- Extracts text from PDF meeting minutes
- Organizes and cleans meeting data
- Prepares datasets for text mining and LLM analysis
- Includes scripts and notebooks for data processing

## Setup
1. **Clone the repository:**
	```powershell
	git clone https://github.com/byteLm/meeting-minutes-analysis.git
	cd meeting-minutes-analysis
	```
2. **Create a Python environment (optional but recommended):**
	```powershell
	python -m venv venv
	.\venv\Scripts\Activate
	```
3. **Install dependencies:**
	```powershell
	pip install -r requirements.txt
	```
4. **Setup ollama (if using LLM features):**
   - Follow instructions at [Ollama](https://ollama.com/docs/installation) to install and set up the local LLM client.
   - Download and set up the desired model (e.g., was tested with `qwen3:8b`).
   - Ensure the model is running locally, serve it with:
     ```powershell
     ollama serve qwen3:8b # by default, it will be available at http://localhost:11434
     ```
## How to Run
### Use Jupyter Notebooks
Explore and analyze the dataset using the provided notebook:
```powershell
jupyter notebook notebooks/get_organized_dataset.ipynb
```

## Data
Original PDFs are located in the `CBH_LN/` folders, wich can be used as e.g.

## Requirements
- Python 3.8+
- pip

## License
MIT