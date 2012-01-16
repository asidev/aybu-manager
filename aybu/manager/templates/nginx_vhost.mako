server {
	listen ${settings['nginx.port']};
	server_name ${instance.domain} ${" ".join([a.domain for a in instance.aliases])};
	error_log ${instance.paths.logs.nginx} info;

	location / {
		include /etc/nginx/uwsgi_params;
		uwsgi_param UWSGI_FASTROUTER_KEY $host;
		uwsgi_pass ${uwsgi.fastrouter.address}:${uwsgi.fastrouter.port};
	}
}
