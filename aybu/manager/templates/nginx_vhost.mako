server {
	listen ${settings['nginx.port']};
	server_name ${instance.domain} ${" ".join([a.domain for a in instance.aliases])};
	error_log ${instance.paths.logs.nginx} info;
	set $themes ${instance.environment.paths.themes};
	set $instance ${instance.paths.instance_dir};
<%
    chain = list(instance.themes_chain)
    num_themes = len(chain)
%>
	location /static {
		root $instance;
		% if instance.theme:
		try_files $uri @${instance.theme.name};
		% else:
		try_files $uri =404;
		% endif
		expires max;
	}

	% for i, theme in enumerate(chain):
	location @${theme.name} {
		root $themes/${theme.name};
	% if i != num_themes - 1:
		try_files $uri @${chain[i+1].name};
	% else:
		try_files $uri =404;
	% endif
		expires max;
	}

	% endfor
	location / {
		include /etc/nginx/uwsgi_params;
		uwsgi_param UWSGI_FASTROUTER_KEY $host;
		uwsgi_pass ${instance.environment.uwsgi_config.fastrouter.address}:${instance.environment.uwsgi_config.fastrouter.port};
	}
}
