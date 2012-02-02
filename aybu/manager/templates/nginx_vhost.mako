server {
	listen ${settings['nginx.port']};
	server_name ${instance.domain} ${" ".join([a.domain for a in instance.aliases])} ${" ".join([r.source for r in instance.redirects])};
	access_log off;
	error_log ${instance.paths.logs.nginx} info;
	set $themes ${instance.environment.paths.themes};
	set $instance ${instance.paths.instance_dir};
	<%
	chain = list(instance.themes_chain)
	num_themes = len(chain)
	%>

	% for redirect in instance.redirects:
	if ($host == "${redirect.source}") {
		rewrite ^ http://${redirect.instance.domain}${redirect.target_path} ${"permanent" if redirect.http_code < 302 else "redirect"};
	}
	% endfor

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
