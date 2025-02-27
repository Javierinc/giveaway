
import psycopg2
import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def conectar_db():
    """Establece la conexión a la base de datos PostgreSQL"""
    return psycopg2.connect(DATABASE_URL)

def crear_base_datos():
    """Crea las tablas si no existen"""
    conn = conectar_db()
    c = conn.cursor()

    # Crear tabla de eventos
    c.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) UNIQUE NOT NULL,
            fecha DATE NOT NULL,
            descripcion TEXT
        )
    ''')

    # Crear tabla de participantes
    c.execute('''
        CREATE TABLE IF NOT EXISTS participantes (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            evento_id INT REFERENCES eventos(id) ON DELETE CASCADE,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Crear tabla de ganadores
    c.execute('''
        CREATE TABLE IF NOT EXISTS ganadores (
            id SERIAL PRIMARY KEY,
            participante_id INT REFERENCES participantes(id) ON DELETE CASCADE,
            evento_id INT REFERENCES eventos(id) ON DELETE CASCADE,
            fecha_ganador TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def guardar_evento(nombre, fecha, descripcion=None):
    """Guarda un evento en la base de datos"""
    conn = conectar_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO eventos (nombre, fecha, descripcion) VALUES (%s, %s, %s) RETURNING id",
                  (nombre, fecha, descripcion))
        evento_id = c.fetchone()[0]
        conn.commit()
        return {"id": evento_id, "nombre": nombre, "fecha": fecha, "descripcion": descripcion}
    except psycopg2.IntegrityError:
        conn.rollback()
        return {"error": "El evento ya existe"}
    finally:
        conn.close()

def obtener_todos_los_eventos():
    """Devuelve una lista con todos los eventos registrados"""
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id, nombre, fecha, descripcion FROM eventos")
    eventos = c.fetchall()
    conn.close()

    # Convertir los resultados a una lista de diccionarios
    return [{"id": e[0], "nombre": e[1], "fecha": e[2].strftime("%Y-%m-%d"), "descripcion": e[3]} for e in eventos]


def obtener_evento_id(evento_nombre):
    """Devuelve el ID de un evento dado su nombre"""
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id FROM eventos WHERE nombre = %s", (evento_nombre,))
    evento = c.fetchone()
    conn.close()
    return evento[0] if evento else None

def guardar_participante(nombre, evento_nombre):
    """Guarda un participante en la base de datos con su evento"""
    evento_id = obtener_evento_id(evento_nombre)
    if not evento_id:
        return {"error": "El evento no existe"}

    conn = conectar_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO participantes (nombre, evento_id) VALUES (%s, %s) RETURNING id",
                  (nombre, evento_id))
        participante_id = c.fetchone()[0]
        conn.commit()
        return {"id": participante_id, "nombre": nombre, "evento": evento_nombre}
    except psycopg2.IntegrityError:
        conn.rollback()
        return {"error": "El participante ya está registrado"}
    finally:
        conn.close()

def obtener_participantes_evento(evento_nombre):
    """Recupera los participantes de un evento específico"""
    evento_id = obtener_evento_id(evento_nombre)
    if not evento_id:
        return {"error": "El evento no existe"}

    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT nombre FROM participantes WHERE evento_id = %s", (evento_id,))
    participantes = [{"nombre": row[0]} for row in c.fetchall()]
    conn.close()
    return participantes

def guardar_ganador(nombre, evento_nombre):
    """Guarda un ganador en la tabla ganadores"""
    evento_id = obtener_evento_id(evento_nombre)
    if not evento_id:
        return {"error": "El evento no existe"}

    conn = conectar_db()
    c = conn.cursor()

    # Verificar si el participante está en el evento
    c.execute("SELECT id FROM participantes WHERE nombre = %s AND evento_id = %s", (nombre, evento_id))
    participante = c.fetchone()
    if not participante:
        conn.close()
        return {"error": "El participante no está en este evento"}

    participante_id = participante[0]

    try:
        c.execute("INSERT INTO ganadores (participante_id, evento_id) VALUES (%s, %s)",
                  (participante_id, evento_id))
        conn.commit()
        return {"message": f"{nombre} registrado como ganador en {evento_nombre}"}
    except psycopg2.IntegrityError:
        conn.rollback()
        return {"error": "El participante ya ha ganado"}
    finally:
        conn.close()

def obtener_ganadores(evento_nombre):
    """Recupera los ganadores de un evento específico"""
    evento_id = obtener_evento_id(evento_nombre)
    if not evento_id:
        return {"error": "El evento no existe"}

    conn = conectar_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.nombre, g.fecha_ganador 
        FROM ganadores g
        JOIN participantes p ON g.participante_id = p.id
        WHERE g.evento_id = %s
    """, (evento_id,))
    ganadores = [{"nombre": row[0], "fecha": row[1]} for row in c.fetchall()]
    conn.close()
    return ganadores





def obtener_eventos_hoy():
    """Devuelve la lista de eventos programados para el día en curso."""
    hoy = date.today().strftime("%Y-%m-%d")

    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id, nombre, fecha, descripcion FROM eventos WHERE fecha = %s", (hoy,))
    eventos = c.fetchall()
    conn.close()

    return [{"id": e[0], "nombre": e[1], "fecha": e[2].strftime("%Y-%m-%d"), "descripcion": e[3]} for e in eventos]

def obtener_eventos_hoy():
    """Devuelve la lista de eventos programados para el día en curso."""
    hoy = date.today().strftime("%Y-%m-%d")

    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT id, nombre, fecha, descripcion FROM eventos WHERE fecha = %s", (hoy,))
    eventos = c.fetchall()
    conn.close()

    return [{"id": e[0], "nombre": e[1], "fecha": e[2].strftime("%Y-%m-%d"), "descripcion": e[3]} for e in eventos]
