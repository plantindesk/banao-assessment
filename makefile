help:
    @echo.
    @echo Available commands:
    @echo   install    - Sync dependencies using uv
    @echo   run        - Run the Django development server on port 8000
    @echo   migrate    - Apply database migrations
    @echo   migrations - Create new database migrations
    @echo   superuser  - Create a Django superuser
    @echo   typecheck  - Run PyRefly type checker on the project
    @echo   clean      - Remove __pycache__ directories and .venv folder
    @echo   help       - Display this help message
    @echo.

# Install dependencies using uv
install:
    @echo Installing dependencies...
    uv sync

# Run the Django development server
run:
    @echo Starting Django development server...
    uv run python manage.py runserver

# Apply database migrations
migrate:
    @echo Applying database migrations...
    uv run python manage.py migrate

# Create new database migrations
migrations:
    @echo Creating new database migrations...
    uv run python manage.py makemigrations

# Create a Django superuser
superuser:
    @echo Creating Django superuser...
    uv run python manage.py createsuperuser

# Run PyRefly type checker
typecheck:
    @echo Running PyRefly type checker...
    uv run pyrefly check

# Clean up generated files
clean:
    @echo Cleaning up generated files...
    @echo Removing __pycache__ directories...
    for /d /r . %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"
    @echo Removing .venv folder...
    if exist .venv rmdir /s /q .venv
    @echo Removing compiled Python files...
    del /s /q *.pyc 2>nul
