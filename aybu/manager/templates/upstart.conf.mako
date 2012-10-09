description "Aybu Environment ${env.name}"
start on stopped aybu_create_cgroups
stop on runlevel [06]
setuid ${env.os_config.user}
setgid ${env.os_config.group}
respawn
respawn limit 10 5
<%
  import os.path
  cgroups = ["--cgroup %s" % os.path.join(ctrl, env.name) for ctrl in env.paths.cgroups]
%>\
exec ${uwsgi.bin} --fastrouter ${uwsgi.fastrouter.address}:${uwsgi.fastrouter.port} --fastrouter-subscription-server ${uwsgi.subscription_server.address}:${uwsgi.subscription_server.port} --master --emperor ${env.paths.configs.uwsgi} ${" ".join(cgroups)} --fastrouter-stats ${uwsgi.fastrouter_stats_server.address}:${uwsgi.fastrouter_stats_server.port} --emperor-stats ${uwsgi.emperor_stats_server.address}:${uwsgi.emperor_stats_server.port} --die-on-term --logto ${env.paths.logs.emperor}