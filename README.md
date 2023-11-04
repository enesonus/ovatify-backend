# ovatify-backend

## Development

1. Create a new python 3.11 virtual environment if it does not exist
	Steps to create virtual environment:
	1. Navigate to the project root directory
	2. Run `python -m venv venv`
2. !!! IMPORTANT - Make sure the virtual environment is active - (venv) should be seen in the terminal !!!
3. Run `pip install -r requirements.txt` to install dependencies
4. Run `uvicorn main:app --reload` or `python main.py` to start the server

Note: Make sure to run `pip freeze > requirements.txt` after installing/uninstalling packages to ensure everyone is running on the same version of packages