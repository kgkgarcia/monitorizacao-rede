OIDS_DISPONIVEIS = [
    # Standard (funcionam em UDM Pro e USW 24 PoE)
    {"nome": "uptime",              "oid": "1.3.6.1.2.1.1.3.0",            "marca": "Standard"},
    {"nome": "nome_sistema",        "oid": "1.3.6.1.2.1.1.5.0",            "marca": "Standard"},
    {"nome": "descricao",           "oid": "1.3.6.1.2.1.1.1.0",            "marca": "Standard"},
    {"nome": "localizacao",         "oid": "1.3.6.1.2.1.1.6.0",            "marca": "Standard"},
    {"nome": "contacto",            "oid": "1.3.6.1.2.1.1.4.0",            "marca": "Standard"},
    {"nome": "num_interfaces",      "oid": "1.3.6.1.2.1.2.1.0",            "marca": "Standard"},
    {"nome": "trafico_entrada",     "oid": "1.3.6.1.2.1.2.2.1.10.1",       "marca": "Standard"},
    {"nome": "trafico_saida",       "oid": "1.3.6.1.2.1.2.2.1.16.1",       "marca": "Standard"},
    {"nome": "erros_entrada",       "oid": "1.3.6.1.2.1.2.2.1.14.1",       "marca": "Standard"},
    {"nome": "erros_saida",         "oid": "1.3.6.1.2.1.2.2.1.20.1",       "marca": "Standard"},
    {"nome": "estado_interface",    "oid": "1.3.6.1.2.1.2.2.1.8.1",        "marca": "Standard"},

    # UniFi (UDM Pro e USW 24 PoE)
    {"nome": "cpu_1min",            "oid": "1.3.6.1.4.1.10002.1.1.1.4.2.1.3.1",  "marca": "UniFi"},
    {"nome": "cpu_5min",            "oid": "1.3.6.1.4.1.10002.1.1.1.4.2.1.3.2",  "marca": "UniFi"},
    {"nome": "cpu_15min",           "oid": "1.3.6.1.4.1.10002.1.1.1.4.2.1.3.3",  "marca": "UniFi"},
    {"nome": "ram_total",           "oid": "1.3.6.1.4.1.10002.1.1.1.1.1.0",       "marca": "UniFi"},
    {"nome": "ram_livre",           "oid": "1.3.6.1.4.1.10002.1.1.1.1.2.0",       "marca": "UniFi"},
]