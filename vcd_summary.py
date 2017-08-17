from app import global_variable, config_section_map, Config

# this is just for gunicorn don't touch it!
app = global_variable.app

if __name__ == '__main__':
    from app import global_variable
    # I need to avoid double spawn. So let's disable debug.
    global_variable.app.debug = False
    global_variable.app.run(host=config_section_map(Config, 'flask')["bind_ip"],
                            port=int(config_section_map(Config, 'flask')["bind_port"]))
