[program:aybu_${env.name}]
<%
  import os.path
  cgroups = ["--cgroup %s" % os.path.join(ctrl, env.name) for ctrl in env.paths.cgroups]
%>\
command=${uwsgi.bin} --fastrouter ${uwsgi.fastrouter.address}:${uwsgi.fastrouter.port} --fastrouter-subscription-server ${uwsgi.subscription_server.address}:${uwsgi.subscription_server.port} -M --emperor ${env.paths.configs.uwsgi} ${" ".join(cgroups)}
stopsignal=INT
user=${env.os_config.user}
group=${env.os_config.group}
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=${env.paths.logs.emperor}

