import os
import csv
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, MetaData, inspect

# ---------------------------------------------------------------
# CONFIGURACIÓN INICIAL
# ---------------------------------------------------------------

def configurar_rutas():
    """Configuración robusta de rutas para el pipeline"""
    # 1. Definir rutas absolutas
    proyecto_path = Path(r"C:\Users\keive\Downloads\entregable-4")
    db_path = proyecto_path / "backend" / "database.db"
    backups_path = proyecto_path / "pipeline" / "backups"
    
    # 2. Verificar existencia
    if not db_path.exists():
        raise FileNotFoundError(f"❌ No se encontró la base de datos en: {db_path}")
    
    # 3. Crear directorio de backups si no existe
    backups_path.mkdir(parents=True, exist_ok=True)
    
    return {
        "db_url": f"sqlite:///{db_path}",
        "backups_dir": str(backups_path)
    }

# ---------------------------------------------------------------
# EXTRACCIÓN DE DATOS 
# ---------------------------------------------------------------

def extraer_datos(engine):
    """Extrae datos de todas las tablas relevantes con validación"""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    datos = {}
    tablas_requeridas = {'mascotas', 'adopciones'}
    
    # Verificar tablas existentes
    tablas_disponibles = set(metadata.tables.keys())
    faltantes = tablas_requeridas - tablas_disponibles
    
    if faltantes:
        raise ValueError(f"Tablas faltantes en la base de datos: {faltantes}")
    
    # Extraer datos
    with engine.connect() as conn:
        for tabla in tablas_requeridas:
            result = conn.execute(metadata.tables[tabla].select())
            # Convertir Row objects a diccionarios
            datos[tabla] = [dict(row._mapping) for row in result]
    
    return datos

# ---------------------------------------------------------------
# TRANSFORMACIÓN Y VALIDACIÓN
# ---------------------------------------------------------------

def transformar_datos(datos):
    """Realiza validaciones y genera reporte de calidad"""
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "estadisticas": {
            "total_mascotas": len(datos["mascotas"]),
            "mascotas_adoptadas": sum(1 for m in datos["mascotas"] if m.get("adoptado", False)),
            "total_adopciones": len(datos["adopciones"])
        },
        "problemas": []
    }
    
    # Validación 1: Edades de mascotas
    for idx, mascota in enumerate(datos["mascotas"]):
        edad = mascota.get("edad", 0)
        if not (0 <= edad <= 30):
            reporte["problemas"].append({
                "tipo": "edad_invalida",
                "tabla": "mascotas",
                "id": mascota.get("id", idx),
                "valor_actual": edad,
                "mensaje": f"Edad {edad} fuera de rango (0-30)"
            })
    
    # Validación 2: Relaciones mascota-adopción
    ids_mascotas = {m.get("id") for m in datos["mascotas"] if m.get("id") is not None}
    for adopcion in datos["adopciones"]:
        mascota_id = adopcion.get("mascota_id")
        if mascota_id not in ids_mascotas:
            reporte["problemas"].append({
                "tipo": "relacion_invalida",
                "tabla": "adopciones",
                "id": adopcion.get("id"),
                "mensaje": f"Mascota {mascota_id} no existe"
            })
    
    return datos, reporte

# ---------------------------------------------------------------
# CARGA DE RESULTADOS (BACKUPS)
# ---------------------------------------------------------------

def guardar_backups(datos, reporte, backups_dir):
    """Guarda datos en CSV y reporte en JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivos_generados = []
    
    # 1. Guardar datos tabulares
    for tabla, registros in datos.items():
        if not registros:
            print(f"  ⚠️  Tabla '{tabla}' está vacía, saltando...")
            continue
            
        archivo_csv = Path(backups_dir) / f"{tabla}_{timestamp}.csv"
        
        # Obtener las columnas de manera segura
        if isinstance(registros[0], dict):
            fieldnames = list(registros[0].keys())
        else:
            # Fallback si no es un diccionario
            fieldnames = list(registros[0]._mapping.keys())
        
        try:
            with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Escribir cada registro asegurándose de que sea un diccionario
                for registro in registros:
                    if isinstance(registro, dict):
                        writer.writerow(registro)
                    else:
                        writer.writerow(dict(registro._mapping))
            
            archivos_generados.append(str(archivo_csv))
            print(f"  ✅ {tabla}: {len(registros)} registros → {archivo_csv.name}")
            
        except Exception as e:
            print(f"  ❌ Error guardando {tabla}: {str(e)}")
    
    # 2. Guardar reporte de calidad
    archivo_json = Path(backups_dir) / f"reporte_calidad_{timestamp}.json"
    try:
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        archivos_generados.append(str(archivo_json))
        print(f"  ✅ Reporte de calidad → {archivo_json.name}")
        
    except Exception as e:
        print(f"  ❌ Error guardando reporte: {str(e)}")
    
    return {
        "archivos_generados": archivos_generados
    }

# ---------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# ---------------------------------------------------------------

def ejecutar_pipeline():
    print("\n" + "="*50)
    print("  INICIANDO PIPELINE ETL - REFUGIO DE MASCOTAS")
    print("="*50 + "\n")
    
    try:
        # 1. Configuración
        config = configurar_rutas()
        engine = create_engine(
            config["db_url"],
            connect_args={"check_same_thread": False}
        )
        
        # 2. Extracción
        print("[EXTRACCIÓN] Obteniendo datos de la base de datos...")
        datos = extraer_datos(engine)
        print(f"  → Mascotas: {len(datos['mascotas'])} registros")
        print(f"  → Adopciones: {len(datos['adopciones'])} registros")
        
        # 3. Transformación
        print("\n[TRANSFORMACIÓN] Validando datos...")
        datos_transformados, reporte = transformar_datos(datos)
        print(f"  → Problemas detectados: {len(reporte['problemas'])}")
        
        if reporte['problemas']:
            print("  ⚠️  Problemas encontrados:")
            for problema in reporte['problemas']:
                print(f"    • {problema['mensaje']}")
        
        # 4. Carga
        print("\n[CARGA] Generando archivos de backup...")
        resultado = guardar_backups(datos_transformados, reporte, config["backups_dir"])
        
        # Resultado final
        print("\n" + "="*50)
        print("  PIPELINE COMPLETADO EXITOSAMENTE")
        print("="*50)
        
        if resultado["archivos_generados"]:
            print(f"\n📁 Archivos generados en: {config['backups_dir']}")
            for archivo in resultado["archivos_generados"]:
                print(f"  → {Path(archivo).name}")
        else:
            print("\n⚠️  No se generaron archivos")
        
        # Mostrar estadísticas del reporte
        print(f"\n📊 Estadísticas:")
        for clave, valor in reporte['estadisticas'].items():
            print(f"  → {clave.replace('_', ' ').title()}: {valor}")
        
        return True
    
    except Exception as e:
        print("\n" + "="*50)
        print("  ERROR EN EL PIPELINE")
        print("="*50)
        print(f"\nDetalles del error:\n{str(e)}")
        
        # Información adicional para debugging
        import traceback
        print(f"\nTraceback completo:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    ejecutar_pipeline()