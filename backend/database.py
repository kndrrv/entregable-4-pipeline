from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Configuración de la base de datos
Base = declarative_base()

class Mascota(Base):
    """
    Modelo para representar las mascotas en el refugio
    """
    __tablename__ = 'mascotas'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    imagen_url = Column(String(500), nullable=False)
    raza = Column(String(100), default='desconocida')
    edad = Column(Integer)
    descripcion = Column(Text)
    adoptado = Column(Boolean, default=False)
    fecha_ingreso = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación con adopciones (una mascota puede tener una adopción)
    adopcion = relationship("Adopcion", back_populates="mascota", uselist=False)

    def __repr__(self):
        return f"<Mascota(id={self.id}, nombre='{self.nombre}', raza='{self.raza}')>"

class Adopcion(Base):
    """
    Modelo para registrar las adopciones de mascotas
    """
    __tablename__ = 'adopciones'

    id = Column(Integer, primary_key=True)
    mascota_id = Column(Integer, ForeignKey('mascotas.id'), unique=True, nullable=False)
    adoptante_nombre = Column(String(100), nullable=False)
    adoptante_email = Column(String(100), nullable=False)
    adoptante_telefono = Column(String(20), nullable=False)
    fecha_adopcion = Column(DateTime, default=datetime.now)
    notas = Column(Text)
    
    # Relación con mascota
    mascota = relationship("Mascota", back_populates="adopcion")

    def __repr__(self):
        return f"<Adopcion(mascota_id={self.mascota_id}, adoptante='{self.adoptante_nombre}')>"

class Usuario(Base):
    """
    Modelo para usuarios del sistema (opcional para futuras expansiones)
    """
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.now)
    rol = Column(String(20), default='usuario')

    def __repr__(self):
        return f"<Usuario(username='{self.username}', email='{self.email}')>"

# Configuración de la conexión a la base de datos
def configurar_base_datos():
    # Usar SQLite para desarrollo (se crea en el directorio actual)
    DATABASE_URL = "sqlite:///database.db"
    
    # Configuración para PostgreSQL (descomentar para producción)
    # DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:contraseña@localhost/refugio_mascotas")
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

# Crear tablas si no existen
def crear_tablas(engine):
    Base.metadata.create_all(bind=engine)

# Datos iniciales para desarrollo
def insertar_datos_iniciales(session):
    # Solo insertar si no hay mascotas
    if not session.query(Mascota).first():
        mascotas_iniciales = [
            Mascota(
                nombre="Max",
                imagen_url="https://images.unsplash.com/photo-1615751072497-5f5169febe17?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80",
                raza="Golden Retriever",
                edad=3,
                descripcion="Perro juguetón y cariñoso"
            ),
            Mascota(
                nombre="Luna",
                imagen_url="https://images.unsplash.com/photo-1586671267731-da2cf3ceeb80?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80",
                raza="Labrador",
                edad=2,
                descripcion="Perra inteligente y obediente"
            )
        ]
        
        session.add_all(mascotas_iniciales)
        session.commit()

# Configuración inicial al importar
engine, SessionLocal = configurar_base_datos()
crear_tablas(engine)

# Para desarrollo: insertar datos iniciales al ejecutar directamente
if __name__ == "__main__":
    db = SessionLocal()
    try:
        insertar_datos_iniciales(db)
        print("✅ Base de datos inicializada con datos de prueba")
    except Exception as e:
        print(f"❌ Error al inicializar datos: {e}")
    finally:
        db.close()