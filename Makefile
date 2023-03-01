build_admin:
	docker compose -f .docker/admin/docker-compose.yml build
	docker compose -f .docker/admin/docker-compose.yml run --rm admin bash -c "npm ci --legacy-peer-deps && npx react-scripts --openssl-legacy-provider build"
	cp -r ./admin/build/ ./public/admin