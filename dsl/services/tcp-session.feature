# TcpSession — persistent async TCP for --follow polling.
# Source: src/biome_mcp/transport/persistent.py

FEATURE tcpSession USES service
  STATE reader : any? = None
  STATE writer : any? = None
  FACT host : text
  FACT port : number

  ACTION connect
  ACTION close
  ACTION call
  ACTION reconnect

  DECISION is_connected

  SHOW host, port
  EXAMPLES tcpSession.examples
END
