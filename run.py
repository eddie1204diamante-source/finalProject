from app import create_app

app = create_app()

if __name__ == '__main__':
    # El debug=True es para que cada cambio que hagas se vea al instante
    app.run(debug=True, port=8085) 