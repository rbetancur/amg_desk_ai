#!/usr/bin/env python3
"""Script para verificar que las tablas se crearon correctamente en Supabase"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def verify_tables():
    """Verifica que las tablas HLP_CATEGORIAS y HLP_PETICIONES existan"""
    try:
        # Convertir URL async a síncrona para verificación
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Verificar que las tablas existan
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('HLP_CATEGORIAS', 'HLP_PETICIONES')
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            print("=== Verificación de Tablas ===")
            print()
            
            if 'HLP_CATEGORIAS' in tables:
                print("✅ Tabla HLP_CATEGORIAS existe")
            else:
                print("❌ Tabla HLP_CATEGORIAS NO existe")
            
            if 'HLP_PETICIONES' in tables:
                print("✅ Tabla HLP_PETICIONES existe")
            else:
                print("❌ Tabla HLP_PETICIONES NO existe")
            
            print()
            
            # Verificar datos seed
            if 'HLP_CATEGORIAS' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM HLP_CATEGORIAS"))
                count = result.scalar()
                print(f"📊 Registros en HLP_CATEGORIAS: {count}")
                
                if count > 0:
                    result = conn.execute(text("SELECT CODCATEGORIA, CATEGORIA FROM HLP_CATEGORIAS ORDER BY CODCATEGORIA"))
                    print("   Datos:")
                    for row in result:
                        print(f"   - {row[0]}: {row[1]}")
                else:
                    print("   ⚠️  No hay datos seed")
            
            print()
            
            # Verificar estructura de HLP_PETICIONES
            if 'HLP_PETICIONES' in tables:
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = 'HLP_PETICIONES'
                """))
                col_count = result.scalar()
                print(f"📊 Columnas en HLP_PETICIONES: {col_count}")
                
                result = conn.execute(text("SELECT COUNT(*) FROM HLP_PETICIONES"))
                row_count = result.scalar()
                print(f"📊 Registros en HLP_PETICIONES: {row_count}")
            
            print()
            print("✅ Verificación completada")
            
    except Exception as e:
        print(f"❌ Error al verificar tablas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_tables()
