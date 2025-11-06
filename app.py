from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<h1>Whasaaaaa!!!! 🤪!</h1>"

@app.route("/api/negocios")
def get_negocios():
    df = pd.read_csv("bk_excel_db/bk_establecimientos.csv")
    data_json = df.head().to_dict(orient='records')
    return jsonify(data_json)
    

@app.route("/api/negocios/<id_negocio>")
def get_negocio_by_id(id_negocio):
    id_float = float(id_negocio)
    df = pd.read_csv('bk_excel_db/bk_establecimientos.csv')
    df_filtrado = df[df["id"] == id_float]
    data_json = df_filtrado.to_dict(orient="records")
    return jsonify(data_json)

if __name__ == "__main__":
    app.run(debug=True)