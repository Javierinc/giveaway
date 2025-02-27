import random
import re
from datetime import datetime
from urllib.parse import unquote
import os
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from dotenv import load_dotenv
from db import crear_base_datos, guardar_participante, guardar_ganador, guardar_evento, obtener_todos_los_eventos, obtener_participantes_evento, obtener_ganadores, obtener_evento_id, obtener_eventos_hoy

load_dotenv()
app = Flask(__name__)


crear_base_datos()

@app.route('/')
def formulario():
    eventos_hoy = obtener_eventos_hoy()
    return render_template("registro-participantes.html", eventos=eventos_hoy)

@app.route('/sorteando')
def simular_sorteo():
    
    return render_template("sorteo.html")

@app.route('/administrador')
def registro_eventos():
    return render_template("registro-eventos.html")

@app.route('/registrar_evento', methods=['POST'])
def registrar_evento():
    nombre_evento = request.form.get("nombre_evento", "").strip().title()
    fecha_evento = request.form.get("fecha_evento", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    # Validación básica para el nombre del evento
    patron_nombre = r"^[a-zA-Z0-9áéíóúüÁÉÍÓÚÜñÑ\s\-,\.]{3,100}$"

    if not re.match(patron_nombre, nombre_evento):
        return render_template("registro-eventos.html", 
                        mensaje="Nombre inválido. Solo se permiten letras, espacios, '-' y '.'",
                        mensaje_tipo="error")

    # Validación de fecha
    try:
        fecha_evento = datetime.strptime(fecha_evento, "%Y-%m-%d")
    except ValueError:
        return render_template("registro-eventos.html",
                               mensaje="Fecha inválidad. Usa el formato YYYY-MM-DD",
                               mensaje_tipo="error")
    

    # Guardar evento en la base de datos
    resultado = guardar_evento(nombre_evento, fecha_evento, descripcion)
    # Desestructurar el resultado
    evento_id = resultado["id"]
    nombre_evento = resultado["nombre"]
    fecha_evento = resultado["fecha"].strftime("%Y-%m-%d")

    mensaje = f"Genial, tu evento '{nombre_evento}' con fecha {fecha_evento} ha sido registrado con éxito con la ID {evento_id}."

    if "error" in resultado:
        flash(resultado["error"], "error")
    else:
        return render_template("registro-eventos.html",
                        mensaje=mensaje,
                        mensaje_tipo="success")

    return redirect(url_for('administrador'))

@app.route('/eventos', methods=['GET'])
def listar_eventos():
    """Endpoint para obtener todos los eventos registrados"""
    eventos = obtener_todos_los_eventos()
    
    if not eventos:
        return jsonify({"mensaje": "No hay eventos registrados"}), 404
    
    return jsonify(eventos), 200

@app.route('/registrar_participante', methods=['POST'])
def registrar_participante():
    nombre = request.form.get("nombre").strip().title()
    evento_nombre = request.form.get("evento")  # Nombre del evento desde el formulario
        # Validación básica para el nombre del evento
    patron_nombre = r"^[a-zA-Z0-9áéíóúüÁÉÍÓÚÜñÑ\s\-,\.]{3,100}$"

    if not re.match(patron_nombre, nombre):
        return render_template("registro-participantes.html", 
                        mensaje='Nombre inválido. Solo se permiten letras y espacios',
                        mensaje_tipo="error")

    print(f"Tipo de evento_nombre: {type(evento_nombre)}, Valor: {evento_nombre}")

    
    resultado = guardar_participante(nombre, evento_nombre)

    if "error" in resultado:
        return render_template("registro-participantes.html",
                               mensaje=resultado["error"],
                               mensaje_tipo="error")

    
        # En caso de éxito, se arma un mensaje amigable.
    mensaje = (f"Genial, {resultado['nombre']} ha sido registrado exitosamente en el evento "
               f"{resultado['evento']} (ID de registro: {resultado['id']}).")
    
    return render_template("registro-participantes.html",
                           eventos=eventos_hoy,
                           mensaje=mensaje,
                           mensaje_tipo="success")


@app.route('/participantes/<evento>', methods=['GET'])
def obtener_participantes(evento):
    evento_nombre = unquote(evento)
    if not evento:
        return jsonify({"message": "Debes proporcionar un evento"}), 400

    participantes = obtener_participantes_evento(evento_nombre)  # Obtener solo los participantes de ese evento
    return jsonify({"evento": evento_nombre, "participantes": participantes}), 200


@app.route('/api/participantes', methods=['GET'])
def obtener_participante():
    evento = "Sofofa"
    if not evento:
        return jsonify({"message": "Debes proporcionar un evento"}), 400

    participantes = obtener_participantes_evento(evento)  # Obtener solo los participantes de ese evento
    return jsonify({"success": True, "participantes": participantes})



# @app.route('/sorteo', methods=['GET'])
# def sorteo():
#     evento = session.get('evento_actual')  # Recuperamos el evento actual

#     if not evento:
#         return jsonify({"message": "No se ha seleccionado un evento."}), 400

#     participantes = obtener_participantes_evento(evento)  # Cargar solo los participantes de este evento
#     if len(participantes) < 10:
#         return jsonify({"message": "No hay suficientes participantes para el sorteo"}), 400
    
#     participantes_ya_ganadores = [g['nombre'] for g in cargar_ganadores(evento)]
#     participantes_validos = [p for p in participantes if p['nombre'] not in participantes_ya_ganadores]

#     if len(participantes_validos) < 5:
#         return jsonify({"message": "No hay suficientes participantes restantes para el sorteo"}), 400

#     ganadores = random.sample(participantes_validos, 5)

#     from datetime import datetime
#     fecha_actual = datetime.now()
#     for ganador in ganadores:
#         guardar_ganador(ganador['nombre'], evento, fecha_actual)

#     return jsonify({"evento": evento, "ganadores": [g['nombre'] for g in ganadores]})

@app.route('/api/sorteo/<string:nombre_evento>/<int:cantidad_ganadores>', methods=['GET'])
def sorteo(nombre_evento, cantidad_ganadores):
    nombre_evento = unquote(nombre_evento)
    # Validar que el evento exista
    evento_id = obtener_evento_id(nombre_evento)
    if not evento_id:
        return jsonify({"message": f"El evento '{nombre_evento}' no existe."}), 400

    # Validar que la cantidad de ganadores sea positiva
    if cantidad_ganadores <= 0:
        return jsonify({"message": "La cantidad de ganadores debe ser un número positivo."}), 400

    # Cargar los participantes del evento especificado
    participantes = obtener_participantes_evento(nombre_evento)
    
    # Verificar que haya participantes
    if not participantes:
        return jsonify({"message": f"No hay participantes registrados para el evento '{nombre_evento}'."}), 400
    
    # Obtener la lista de participantes que ya ganaron en este evento
    participantes_ya_ganadores = [g['nombre'] for g in obtener_ganadores(nombre_evento)]
    
    # Filtrar los participantes que aún no han ganado
    participantes_validos = [p for p in participantes if p['nombre'] not in participantes_ya_ganadores]
    
    # Verificar que haya suficientes participantes válidos
    if len(participantes_validos) < cantidad_ganadores:
        return jsonify({
            "message": f"No hay suficientes participantes disponibles. Se requieren {cantidad_ganadores}, pero solo hay {len(participantes_validos)} participantes que aún no han ganado."
        }), 400
    
    # Seleccionar ganadores aleatorios
    ganadores = random.sample(participantes_validos, cantidad_ganadores)
    
    # Guardar cada ganador
    for ganador in ganadores:
        resultado = guardar_ganador(ganador['nombre'], nombre_evento)
        if "error" in resultado:
            return jsonify({"message": resultado["error"]}), 400
    
    # Retornar la respuesta
    return jsonify({
        "evento": nombre_evento, 
        "cantidad_solicitada": cantidad_ganadores,
        "ganadores": [g['nombre'] for g in ganadores]
    })


@app.route('/ganadores/<string:nombre_evento>', methods=['GET'])
def obtener_ganadores_por_evento(nombre_evento):
    """Obtiene la lista de ganadores para un evento específico."""
    
    # Validar que se ha proporcionado un evento
    if not nombre_evento:
        return jsonify({"message": "Debes proporcionar un evento"}), 400

    # Obtener los ganadores del evento
    ganadores = obtener_ganadores(nombre_evento)

    # Verificar si el evento existe o si hay ganadores
    if isinstance(ganadores, dict) and "error" in ganadores:
        return jsonify({"message": ganadores["error"]}), 404

    if not ganadores:
        return jsonify({"message": f"No hay ganadores registrados para el evento {nombre_evento}"}), 404

    # Extraer la fecha del sorteo (se asume que la fecha es la misma para todos los ganadores)
    fecha_sorteo = ganadores[0].get("fecha") if ganadores else None

    # Construir la respuesta
    respuesta = {
        "evento": nombre_evento,
        "fecha": fecha_sorteo,
        "ganadores": [{"nombre": g["nombre"]} for g in ganadores]
    }

    return jsonify(respuesta), 200




# if __name__ == '__main__':
#     app.run(debug=True)
# if __name__ == '__main__':
#     app.run(debug=True, host='localhost', port=8000)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))  # Usar el puerto asignado por Railway o 8000 si no está disponible
    app.run(debug=True, host='0.0.0.0', port=port)
