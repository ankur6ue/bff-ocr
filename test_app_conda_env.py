from bff_api.app import create_app

if __name__ == '__main__':
    app = create_app('bff_api.config')
    # host must be 0.0.0.0, otherwise won't work from inside docker container
    app.run(host='0.0.0.0', debug=True, use_reloader=False, port=5001)