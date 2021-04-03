from bff_api.app import create_app

app = create_app('bff_api.config')
app.run(debug=True, port=5001)