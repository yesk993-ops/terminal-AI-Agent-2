.PHONY: install uninstall install-user install-pip dev

TELL_SCRIPT := $(shell pwd)/tell
BIN_DIR := /usr/local/bin
USER_BIN_DIR := $(HOME)/.local/bin

install:
	@echo "==> Creating virtual environment..."
	python3 -m venv .venv
	@echo "==> Installing dependencies..."
	.venv/bin/pip install --upgrade pip -q
	.venv/bin/pip install -r requirements.txt -q
	@echo "==> Making tell executable..."
	chmod +x $(TELL_SCRIPT)
	@echo "==> Creating symlink (may need sudo)..."
	@if [ -w $(BIN_DIR) ]; then \
		ln -sf $(TELL_SCRIPT) $(BIN_DIR)/tell; \
	else \
		sudo ln -sf $(TELL_SCRIPT) $(BIN_DIR)/tell; \
	fi
	@echo "==> Done! Use 'tell <query>' from anywhere."

install-user:
	@echo "==> Creating virtual environment..."
	python3 -m venv .venv
	@echo "==> Installing dependencies..."
	.venv/bin/pip install --upgrade pip -q
	.venv/bin/pip install -r requirements.txt -q
	@echo "==> Making tell executable..."
	chmod +x $(TELL_SCRIPT)
	@echo "==> Creating symlink in $(USER_BIN_DIR)..."
	mkdir -p $(USER_BIN_DIR)
	ln -sf $(TELL_SCRIPT) $(USER_BIN_DIR)/tell
	@echo "==> Done! Make sure $(USER_BIN_DIR) is in your PATH."

install-pip:
	@echo "==> Installing tell via pip (editable)..."
	pip install -e .
	@echo "==> Done! Use 'tell <query>' from anywhere."

uninstall:
	@echo "==> Removing symlink..."
	@if [ -w $(BIN_DIR) ]; then \
		rm -f $(BIN_DIR)/tell; \
	else \
		sudo rm -f $(BIN_DIR)/tell; \
	fi
	rm -f $(USER_BIN_DIR)/tell
	@echo "==> Done."

dev:
	.venv/bin/python main.py
