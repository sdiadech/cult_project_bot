.EXPORT_ALL_VARIABLES:

DOTENV_BASE_FILE ?= .env-local
DOTENV_CUSTOM_FILE ?= .env-custom

POETRY_EXPORT_OUTPUT = requirements.txt
POETRY_EXTRAS =
POETRY_GROUPS = --with dev
POETRY_PUBLISH_PRERELEASE ?= false
POETRY_VERSION = 1.8.3
POETRY_VIRTUALENVS_CREATE ?= true
POETRY ?= $(HOME)/.local/bin/poetry

PYTHON_INSTALL_PACKAGES_USING ?= poetry
PYTHON_VERSION ?= 3.12

# Paths
PROJECT_ROOT := $(shell pwd)

# Paths
BOT_SCRIPT := $(PROJECT_ROOT)/app/bot.py
export PYTHONPATH=$(PWD)

# Alembic configuration file path
ALEMBIC_CONFIG_PATH=app/migrations/alembic.ini

-include $(DOTENV_BASE_FILE)
-include $(DOTENV_CUSTOM_FILE)

.PHONY: install-poetry
install-poetry:
ifeq ($(POETRY_PREINSTALLED), true)
	$(POETRY) self update $(POETRY_VERSION)
else
	curl -sSL https://install.python-poetry.org | python -
endif

.PHONY: configure-poetry
configure-poetry:
ifeq ($(POETRY_VIRTUALENVS_CREATE), true)
	$(POETRY) env use $(PYTHON_VERSION)
endif

.PHONY: install-packages
install-packages:
ifeq ($(PYTHON_INSTALL_PACKAGES_USING), poetry)
	$(POETRY) install -vv $(POETRY_EXTRAS) $(POETRY_GROUPS) $(opts)
else
	$(POETRY) run pip install \
		--no-index \
		--requirement=$(POETRY_EXPORT_OUTPUT)
endif

.PHONY: install
install: install-poetry configure-poetry install-packages

lint:
	@echo "Running linting..."
	$(POETRY) run flake8 app/

format:
	@echo "Formatting code..."
	$(POETRY) run black app/

test:
	@echo "Running tests..."
	$(POETRY) run pytest tests/

run:
	@echo "Running the bot locally..."
	$(POETRY) run python app/bot.py

clean:
	@echo "Cleaning up..."
	rm -rf __pycache__ *.pyc $(LOG_DIR)/*.log


# Target to create a new Alembic revision automatically
migrations:
	@echo "Creating new Alembic revision..."
	$(POETRY) run alembic --config $(ALEMBIC_CONFIG_PATH) revision --autogenerate -m "$(MESSAGE)"

# Target to upgrade database to the latest migration
migrate:
	@echo "Upgrading database..."
	$(POETRY) run alembic --config $(PROJECT_ROOT)/$(ALEMBIC_CONFIG_PATH) upgrade head
	$(POETRY) run alembic --config $(PROJECT_ROOT)/$(ALEMBIC_CONFIG_PATH) current

# Target to downgrade database to the previous revision
downgrade:
	@echo "Downgrading database..."
	$(POETRY) run alembic --config $(ALEMBIC_CONFIG_PATH) downgrade -1

current:
	$(POETRY) run alembic current --config $(ALEMBIC_CONFIG_PATH)
