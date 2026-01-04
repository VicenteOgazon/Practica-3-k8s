# Docker
restart:
	sudo systemctl restart docker

start:
	sudo docker start $(c)

stop:
	sudo docker stop $(c)

ps:
	sudo docker ps

# Imágenes de la aplicación web
build-dev:
	sudo docker build --no-cache -f dockerfile/dev_Dockerfile -t app:dev .
	sudo k3d image import app:dev -c practica3

build-pro:
	sudo docker build --no-cache -f dockerfile/pro_Dockerfile -t app:pro .
	sudo k3d image import app:pro -c practica3

help:
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make restart                       - Reinicia el servicio de Docker"
	@echo "  make start c=CONTAINER_ID          - Inicia un contenedor especificado"
	@echo "  make stop c=CONTAINER_ID           - Para un contenedor especificado"
	@echo "  make ps                            - Muestra todos los contenedores en ejecución"
	@echo ""
	@echo "  make build-dev                     - Construye la imagen de desarrollo (app:dev)"
	@echo "  make build-prod                    - Construye la imagen de producción (app:prod)"
	@echo ""
	@echo "  make init-dev                      - Inicializa el entorno de desarrollo"
	@echo "  make plan-dev                      - Muestra el plan de ejecución para dev"
	@echo "  make apply-dev                     - Aplica la configuración para dev"
	@echo "  make down-dev                      - Destruye el entorno de desarrollo"
	@echo "  make restart-dev                   - Recrea completamente el entorno dev"
	@echo "  make clean-dev                     - Destruye dev y limpia recursos Docker"
	@echo ""
	@echo "  make init-prod                     - Inicializa el entorno de producción"
	@echo "  make plan-prod                     - Muestra el plan de ejecución para prod"
	@echo "  make apply-prod                    - Aplica la configuración para prod"
	@echo "  make down-prod                     - Destruye el entorno de producción"
	@echo "  make restart-prod                  - Recrea completamente el entorno prod"
	@echo "  make clean-prod                    - Destruye prod y limpia recursos Docker"
	@echo ""