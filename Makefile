# Unified Makefile for Bulk Validator

.PHONY: api seed batch test docker clean

api:
	uvicorn app.main:app --reload

seed:
	python seed_accounts.py

batch:
	python seed_accounts.py
	python batch_ingest.py seed_accounts.csv --type csv
	python batch_ingest.py seed_accounts.json --type json
	python batch_ingest.py seed_accounts.xml --type xml

view-tokens:
	python view_decrypted_token_map.py --file output/token_map.json

test:
	pytest

docker:
	docker-compose up --build

clean:
	rm -rf output/*.csv output/*.json output/*.xlsx output/*.log output/token_map.json
