-- Crear la base de datos (si no existe)
CREATE DATABASE IF NOT EXISTS refugio_mascotas_API 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE refugio_mascotas_API;

-- Tabla para tipos de mascotas
CREATE TABLE IF NOT EXISTS tipos_mascota (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT uc_tipo_mascota_nombre UNIQUE (nombre)
);

-- Insertar datos iniciales de tipos
INSERT INTO tipos_mascota (nombre, descripcion) VALUES
('Perro', 'Perros de todas las razas y tamaños'),
('Gato', 'Gatos domésticos y de diferentes razas'),
('Conejo', 'Conejos domésticos'),
('Otro', 'Otras mascotas pequeñas');

-- Tabla principal de mascotas
CREATE TABLE IF NOT EXISTS mascotas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo_mascota_id INT NOT NULL,
    raza VARCHAR(100) NOT NULL,
    edad INT NOT NULL,
    descripcion TEXT,
    imagen_url VARCHAR(500),
    adoptado BOOLEAN DEFAULT FALSE,
    fecha_ingreso DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Restricciones
    CONSTRAINT chk_edad_positiva CHECK (edad >= 0),
    CONSTRAINT chk_edad_maxima CHECK (edad <= 30),
    CONSTRAINT fk_tipo_mascota FOREIGN KEY (tipo_mascota_id) REFERENCES tipos_mascota(id),
    
    -- Índices
    INDEX idx_nombre (nombre),
    INDEX idx_raza (raza),
    INDEX idx_edad (edad),
    INDEX idx_adoptado (adoptado)
);

-- Datos de ejemplo
INSERT INTO mascotas (nombre, tipo_mascota_id, raza, edad, descripcion, imagen_url) VALUES
('Max', 1, 'golden retriever', 3, 'Perro juguetón y cariñoso', 'frontend\assets\max.jpg'),
('Luna', 1, 'labrador', 2, 'Perra inteligente y obediente', 'frontend\assets\luna.jpg'),
('Bella', 2, 'siamés', 1, 'Gato cariñoso y tranquilo', 'frontend\assets\Bella.jpg');

-- Vista de resumen
CREATE VIEW vista_mascotas_resumen AS
SELECT 
    m.id,
    m.nombre,
    t.nombre AS tipo,
    m.raza,
    m.edad,
    CASE 
        WHEN m.edad <= 1 THEN 'Cachorro' 
        WHEN m.edad <= 3 THEN 'Joven'
        ELSE 'Adulto'
    END AS categoria_edad,
    m.adoptado,
    m.fecha_ingreso
FROM mascotas m
JOIN tipos_mascota t ON m.tipo_mascota_id = t.id;

-- Tabla de adopciones
CREATE TABLE IF NOT EXISTS adopciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mascota_id INT NOT NULL,
    adoptante VARCHAR(100) NOT NULL,
    contacto VARCHAR(100) NOT NULL,
    fecha_adopcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_mascota_adoptada FOREIGN KEY (mascota_id) REFERENCES mascotas(id)
);

-- Procedimiento para adopciones
DELIMITER //
CREATE PROCEDURE registrar_adopcion(
    IN p_mascota_id INT,
    IN p_adoptante VARCHAR(100),
    IN p_contacto VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    INSERT INTO adopciones (mascota_id, adoptante, contacto)
    VALUES (p_mascota_id, p_adoptante, p_contacto);
    
    UPDATE mascotas SET adoptado = TRUE WHERE id = p_mascota_id;
    
    COMMIT;
END //
DELIMITER ;

-- Permisos (opcional para producción)
CREATE USER IF NOT EXISTS 'refugio_user'@'localhost' IDENTIFIED BY 'segura123';
GRANT ALL PRIVILEGES ON refugio_mascotas.* TO 'refugio_user'@'localhost';
FLUSH PRIVILEGES;