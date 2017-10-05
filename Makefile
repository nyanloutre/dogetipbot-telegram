.PHONY: build
build:
	docker build -t dogetipbot .

.PHONY: run
run: build
	docker run --rm --name dogetipbot --env-file api_keys.env dogetipbot
