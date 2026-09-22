.PHONY: help venv install run clean demo

PYTHON = python3
SRC = doc_tpu
VENV = .venv
BIN = $(VENV)/bin

help: ## Показать справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## Создать виртуальное окружение
	$(PYTHON) -m venv $(VENV)

install: venv ## Установить зависимости
	$(BIN)/pip install click python-docx fpdf2

run: ## Запустить doc-tpu (make run ARGS="-t template.snj -b content.json -f docx -p out.docx")
	$(BIN)/python -m $(SRC).cli $(ARGS)

clean: ## Удалить сгенерированные файлы и venv
	rm -f *.docx *.pdf *.pptx
	rm -rf $(VENV)

demo: ## Сгенерировать демо-документ
	$(BIN)/python -m $(SRC).cli -t template.snj -b examples/content.json -f docx -p demo.docx

report: ## Сгенерировать с личными данными (make report ARGS="-b content.json -p output.docx")
	$(BIN)/python -m $(SRC).cli -r statics/report.json $(ARGS)
