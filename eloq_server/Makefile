nginx-start:
	nginx

nginx-stop:
	nginx -s stop

nginx-quit:
	nginx -s quit

nginx-reload:
	nginx -s reload

nginx-test:
	nginx -t

copy-nginx-config:
	cp eloq.conf etc/nginx/eloq.conf

run-debug:
	uvicorn src._debug_example:app
