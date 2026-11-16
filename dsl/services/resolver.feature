# ConnectionResolver — priority chain for connection source.
# Source: src/biome_mcp/cli/resolver.py

FEATURE connectionResolver USES service
  FACT cli_port : number?
  FACT cli_host : text?
  FACT env_port : number?
  FACT env_host : text?
  FACT config_port : number?
  FACT config_host : text?
  FACT port_file_available : bool = false
  FACT port_file_port : number?
  FACT lock_available : bool = false
  FACT lock_port : number?
  FACT project_path : text?

  ACTION resolve

  DECISION connection_source

  SHOW cli_port, env_port, config_port, port_file_port, lock_port
END
