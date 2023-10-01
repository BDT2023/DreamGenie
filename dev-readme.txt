Assumptions:
	Folder structure:

	.
	├── Dockerfile
	├── DreamGenie
	├── docker-compose.yml
	└── nginx
		├── nginx.conf
		└── nginx_cert
			├── nginx-selfsigned.crt
			└── nginx-selfsigned.key
	

selfsigned generated with:
openssl req -x509 -nodes -days 750 -newkey rsa:2048 -keyout nginx-selfsigned.key -out nginx-selfsigned.crt

The docker build copies the my_secret files from the DreamGenie folders.