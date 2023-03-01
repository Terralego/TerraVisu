build_admin:
	rm -rf ./public/admin
	git submodule update --init
	git submodule update --remote
	docker compose -f .docker/admin/docker-compose.yml pull
	docker compose -f .docker/admin/docker-compose.yml run --rm admin bash -c "npm ci --legacy-peer-deps && npx react-scripts --openssl-legacy-provider build"
	cp -r ./admin/build/ ./public/admin
	sudo rm -rf ./admin/build
	sudo rm -rf ./admin/node_modules