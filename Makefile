# .ENV
setup-env:
	@touch .env
	@sed -i '/^NAME=/d' .env
	@sed -i '/^ENV=/d' .env
	@temp_file=$$(mktemp); \
	owner=$$(stat -c '%u' .env); \
	group=$$(stat -c '%g' .env); \
	echo "NAME=$(repo_name)" > $$temp_file; \
	echo "ENV=$(branch_name)" >> $$temp_file; \
	cat .env >> $$temp_file; \
	mv $$temp_file .env; \
	chmod 664 .env; \
	chown $$owner:$$group .env

load-env: setup-env
	$(eval NAME=$(shell grep -E '^NAME=' .env | cut -d '=' -f 2))
	$(eval ENV=$(shell grep -E '^ENV=' .env | cut -d '=' -f 2))
	$(eval DOCKER_HUB_URL=$(shell grep -E '^DOCKER_HUB_URL=' .env | cut -d '=' -f 2))

# Docker
build: load-env
	@docker build -t $(DOCKER_HUB_URL)/$(NAME):$(ENV) -f docker/Dockerfile .

push: build
	@docker push $(DOCKER_HUB_URL)/$(NAME):$(ENV)

pull: load-env
	@docker pull $(DOCKER_HUB_URL)/$(NAME):$(ENV)

clean: load-env
	@docker rmi $(DOCKER_HUB_URL)/$(NAME):$(ENV)

# Run
stop: load-env
	@cp -f .env docker/$(ENV)/.env
	@docker compose -f docker/$(ENV)/docker-compose.yml -p $(NAME)-$(ENV) down

start: stop
	@docker compose -f docker/$(ENV)/docker-compose.yml -p $(NAME)-$(ENV) up -d

deploy: pull start