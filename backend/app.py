from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os
import logging
import requests

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización de Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    future=True
)

# Declaración de modelos
Base = declarative_base()

class Mascota(Base):
    __tablename__ = 'mascotas'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    imagen_url = Column(String(500), nullable=False)
    raza = Column(String(100), default='Desconocida')
    edad = Column(Integer, nullable=True)
    descripcion = Column(Text)
    adoptado = Column(Boolean, default=False)
    fecha_ingreso = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    adopcion = relationship("Adopcion", back_populates="mascota", uselist=False)

class Adopcion(Base):
    __tablename__ = 'adopciones'

    id = Column(Integer, primary_key=True)
    mascota_id = Column(Integer, ForeignKey('mascotas.id'), unique=True, nullable=False)
    adoptante_nombre = Column(String(100), nullable=False)
    adoptante_email = Column(String(100), nullable=False)
    adoptante_telefono = Column(String(20), nullable=False)
    fecha_adopcion = Column(DateTime, default=datetime.now)
    notas = Column(Text)

    mascota = relationship("Mascota", back_populates="adopcion")

# Crear tablas
def create_tables():
    Base.metadata.create_all(engine)
    logger.info("Tablas verificadas o creadas")

create_tables()

# Sesión DB
SessionLocal = sessionmaker(bind=engine, future=True)

@app.before_request
def before_request():
    request.db = SessionLocal()

@app.teardown_request
def teardown_request(exception=None):
    db = getattr(request, 'db', None)
    if db is not None:
        db.close()

# Error handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Error no manejado: {str(e)}", exc_info=True)
    return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        request.db.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# ✅ Obtener perro aleatorio
@app.route('/api/dogs/random', methods=['GET'])
def get_random_dog():
    try:
        response = requests.get('https://dog.ceo/api/breeds/image/random')
        data = response.json()
        if response.status_code == 200 and data.get("status") == "success":
            return jsonify({"image_url": data["message"]})
        else:
            raise Exception("API externa no devolvió una imagen válida")
    except Exception as e:
        logger.error(f"Error al obtener perro aleatorio: {str(e)}")
        return jsonify({"error": "No se pudo obtener un perro aleatorio"}), 500

# ✅ Obtener razas predefinidas
@app.route('/api/dogs/breeds', methods=['GET'])
def get_breeds():
    try:
        breeds = [
            "Labrador", "Golden Retriever", "Pug", "Pastor Alemán",
            "Chihuahua", "Bulldog", "Beagle", "Husky", "Rottweiler",
            "Dálmata", "Shih Tzu", "Border Collie", "Schnauzer"
        ]
        return jsonify({"breeds": breeds})
    except Exception as e:
        logger.error(f"Error al obtener razas: {str(e)}")
        return jsonify({"error": "No se pudo cargar la lista de razas"}), 500

# ✅ Obtener mascotas guardadas
@app.route('/api/mascotas', methods=['GET'])
def get_mascotas():
    try:
        mascotas = request.db.query(Mascota).all()
        return jsonify([{
            "id": m.id,
            "nombre": m.nombre,
            "imagen_url": m.imagen_url,
            "raza": m.raza,
            "edad": m.edad,
            "descripcion": m.descripcion,
            "adoptado": m.adoptado,
            "fecha_ingreso": m.fecha_ingreso.isoformat() if m.fecha_ingreso else None
        } for m in mascotas])
    except Exception as e:
        return jsonify({"error": "Error al obtener mascotas"}), 500

# ✅ Guardar nueva mascota
@app.route('/api/mascotas', methods=['POST'])
def create_mascota():
    try:
        data = request.get_json()
        nueva = Mascota(
            nombre=data['nombre'],
            imagen_url=data['imagen_url'],
            raza=data.get('raza', 'Desconocida'),
            edad=0,
            descripcion="Añadida desde el frontend"
        )
        request.db.add(nueva)
        request.db.commit()
        return jsonify({"message": "Mascota creada"}), 201
    except Exception as e:
        request.db.rollback()
        logger.error(f"Error al crear mascota: {str(e)}")
        return jsonify({"error": "No se pudo crear la mascota"}), 500

# ✅ Eliminar mascota
@app.route('/api/mascotas/<int:mascota_id>', methods=['DELETE'])
def delete_mascota(mascota_id):
    try:
        mascota = request.db.query(Mascota).filter_by(id=mascota_id).first()
        if mascota:
            request.db.delete(mascota)
            request.db.commit()
            return jsonify({"message": "Mascota eliminada"}), 200
        else:
            return jsonify({"error": "Mascota no encontrada"}), 404
    except Exception as e:
        request.db.rollback()
        return jsonify({"error": "No se pudo eliminar la mascota"}), 500

# ✅ Registrar adopción
@app.route('/api/adopciones', methods=['POST'])
def registrar_adopcion():
    try:
        data = request.get_json()
        adopcion = Adopcion(
            mascota_id=data['mascota_id'],
            adoptante_nombre=data['nombre'],
            adoptante_email=data['email'],
            adoptante_telefono=data['telefono'],
            notas=data.get('notas', '')
        )
        # Marcar mascota como adoptada
        mascota = request.db.query(Mascota).filter_by(id=data['mascota_id']).first()
        if mascota:
            mascota.adoptado = True

        request.db.add(adopcion)
        request.db.commit()
        return jsonify({"message": "Adopción registrada"}), 201
    except Exception as e:
        request.db.rollback()
        return jsonify({"error": "No se pudo registrar la adopción"}), 500

# Datos iniciales
def insert_initial_data():
    try:
        db = SessionLocal()
        if not db.query(Mascota).first():
            mascotas = [
                Mascota(
                    nombre="Max",
                    imagen_url="https://images.unsplash.com/photo-1615751072497-5f5169febe17",
                    raza="Golden Retriever",
                    edad=3,
                    descripcion="Perro juguetón y cariñoso"
                ),
                Mascota(
                    nombre="Luna",
                    imagen_url="https://images.unsplash.com/photo-1586671267731-da2cf3ceeb80",
                    raza="Labrador",
                    edad=2,
                    descripcion="Perra inteligente y obediente"
                )
            ]
            db.add_all(mascotas)
            db.commit()
            logger.info("Datos iniciales insertados")
    except Exception as e:
        logger.error(f"Error al insertar datos iniciales: {str(e)}")
    finally:
        db.close()

if __name__ == '__main__':
    insert_initial_data()
    app.run(host='0.0.0.0', port=5000, debug=True)
