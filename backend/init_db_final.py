"""
Script para inicializar la base de datos final con todos los datos necesarios
"""
from app.database import SessionLocal, engine, Base
from app.models_extended import (
    User, Client, Category, Supplier, Product, 
    Quotation, QuotationItem, Sale, SaleItem, Rental, InventoryMovement
)
from app.auth import get_password_hash
from datetime import datetime, timedelta
import random

def init_database():
    """Crea las tablas y datos iniciales completos"""
    print("🔧 Creando tablas de base de datos extendida...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️  La base de datos ya contiene datos. No se agregarán datos de ejemplo.")
            return
        
        print("👤 Creando usuarios de ejemplo...")
        # Crear usuarios con diferentes roles
        users = [
            User(
                email="admin@empresa.com",
                username="admin",
                full_name="Administrador del Sistema",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
                phone="809-555-0001"
            ),
            User(
                email="vendedor@empresa.com",
                username="vendedor",
                full_name="Juan Pérez - Vendedor",
                hashed_password=get_password_hash("vendedor123"),
                role="vendedor",
                is_active=True,
                phone="809-555-0002"
            ),
            User(
                email="almacen@empresa.com",
                username="almacen",
                full_name="María García - Almacén",
                hashed_password=get_password_hash("almacen123"),
                role="almacen",
                is_active=True,
                phone="809-555-0003"
            ),
            User(
                email="empleado@empresa.com",
                username="empleado",
                full_name="Carlos Rodríguez - Empleado",
                hashed_password=get_password_hash("empleado123"),
                role="empleado",
                is_active=True,
                phone="809-555-0004"
            )
        ]
        for user in users:
            db.add(user)
        db.commit()
        
        print("👥 Creando clientes de ejemplo...")
        # Crear clientes
        clients = [
            Client(
                name="Hospital General",
                client_type="hospital",
                status="activo",
                rnc="101-12345-6",
                email="compras@hospitalgeneral.com",
                phone="809-555-1001",
                address="Av. Principal #123",
                city="Santo Domingo",
                contact_person="Dr. Carlos Rodríguez",
                credit_limit=50000,
                credit_days=30,
                is_recurrent=True
            ),
            Client(
                name="Dr. Ana Martínez",
                client_type="medico",
                status="activo",
                rnc="001-23456-7",
                email="ana.martinez@email.com",
                phone="809-555-1002",
                mobile="829-555-1002",
                address="Consultorio Médico, Calle 5 #45",
                city="Santiago",
                is_recurrent=True
            ),
            Client(
                name="Clínica Santa María",
                client_type="empresa",
                status="activo",
                rnc="101-34567-8",
                email="admin@clinicasantamaria.com",
                phone="809-555-1003",
                address="Av. Independencia #789",
                city="Santo Domingo",
                contact_person="Lic. Pedro Gómez",
                credit_limit=30000,
                credit_days=15,
                is_recurrent=True
            ),
            Client(
                name="José Fernández",
                client_type="particular",
                status="activo",
                rnc="001-45678-9",
                email="jose.fernandez@email.com",
                phone="809-555-1004",
                mobile="829-555-1004",
                city="La Vega"
            ),
            Client(
                name="Centro Médico Especializado",
                client_type="hospital",
                status="activo",
                rnc="101-56789-0",
                email="compras@centromedico.com",
                phone="809-555-1005",
                address="Av. Winston Churchill #456",
                city="Santo Domingo",
                contact_person="Dra. María González",
                credit_limit=75000,
                credit_days=45,
                is_recurrent=True
            )
        ]
        for client in clients:
            db.add(client)
        db.commit()
        
        print("📁 Creando categorías de ejemplo...")
        # Crear categorías
        categories = [
            Category(name="Equipos Quirúrgicos", description="Equipos médicos para cirugías"),
            Category(name="Instrumental Médico", description="Instrumentos médicos diversos"),
            Category(name="Equipos de Diagnóstico", description="Equipos para diagnóstico médico"),
            Category(name="Consumibles", description="Productos de un solo uso"),
            Category(name="Mobiliario Médico", description="Muebles y mobiliario para hospitales"),
            Category(name="Equipos de Monitoreo", description="Equipos para monitoreo de pacientes"),
            Category(name="Equipos de Rehabilitación", description="Equipos para terapia física")
        ]
        for cat in categories:
            db.add(cat)
        db.commit()
        
        print("🚚 Creando proveedores de ejemplo...")
        # Crear proveedores
        suppliers = [
            Supplier(
                name="MedEquip Internacional",
                contact_name="Roberto Silva",
                email="ventas@medequip.com",
                phone="809-555-2001",
                address="Zona Industrial, Santo Domingo",
                rnc="101-55555-5",
                payment_terms="30 días"
            ),
            Supplier(
                name="Suministros Médicos RD",
                contact_name="Laura Pérez",
                email="info@suministrosmedicos.com",
                phone="809-555-2002",
                address="Av. 27 de Febrero, Santo Domingo",
                rnc="101-66666-6",
                payment_terms="15 días"
            ),
            Supplier(
                name="Global Medical Supply",
                contact_name="Michael Johnson",
                email="sales@globalmedical.com",
                phone="+1-305-555-3001",
                address="Miami, FL, USA",
                payment_terms="Prepago"
            ),
            Supplier(
                name="Equipos Médicos del Caribe",
                contact_name="Carmen Rodríguez",
                email="ventas@equiposmedicos.com",
                phone="809-555-2004",
                address="Av. Máximo Gómez #789",
                city="Santiago",
                rnc="101-77777-7",
                payment_terms="20 días"
            )
        ]
        for supplier in suppliers:
            db.add(supplier)
        db.commit()
        
        print("📦 Creando productos de ejemplo...")
        # Crear productos (venta y alquiler)
        products = [
            Product(
                sku="EQ-001",
                name="Monitor de Signos Vitales",
                description="Monitor multiparamétrico para signos vitales",
                product_type="ambos",
                category_id=3,
                supplier_id=1,
                price=15000,
                rental_price_daily=500,
                rental_price_weekly=3000,
                rental_price_monthly=10000,
                cost=12000,
                stock=5,
                stock_available=3,
                min_stock=2,
                location="Almacén A-1",
                warranty_months=24,
                is_active=True
            ),
            Product(
                sku="EQ-002",
                name="Desfibrilador Portátil",
                description="Desfibrilador automático externo (DEA)",
                product_type="venta",
                category_id=1,
                supplier_id=1,
                price=25000,
                cost=20000,
                stock=3,
                stock_available=3,
                min_stock=1,
                location="Almacén A-2",
                warranty_months=36,
                is_active=True
            ),
            Product(
                sku="INS-001",
                name="Set de Instrumental Quirúrgico",
                description="Set completo de 25 piezas para cirugía general",
                product_type="venta",
                category_id=2,
                supplier_id=2,
                price=8500,
                cost=6500,
                stock=10,
                stock_available=10,
                min_stock=3,
                location="Almacén B-1",
                warranty_months=12,
                is_active=True
            ),
            Product(
                sku="EQ-003",
                name="Cama Hospitalaria Eléctrica",
                description="Cama eléctrica de 3 posiciones con barandas",
                product_type="alquiler",
                category_id=5,
                supplier_id=1,
                price=35000,
                rental_price_daily=300,
                rental_price_weekly=1800,
                rental_price_monthly=6000,
                cost=28000,
                stock=8,
                stock_available=6,
                min_stock=2,
                location="Almacén C-1",
                warranty_months=24,
                is_active=True
            ),
            Product(
                sku="CON-001",
                name="Guantes Quirúrgicos (Caja 100 unidades)",
                description="Guantes estériles de látex, talla M",
                product_type="venta",
                category_id=4,
                supplier_id=2,
                price=450,
                cost=300,
                stock=50,
                stock_available=50,
                min_stock=20,
                location="Almacén D-1",
                is_active=True
            ),
            Product(
                sku="EQ-004",
                name="Oxímetro de Pulso",
                description="Oxímetro digital portátil",
                product_type="venta",
                category_id=3,
                supplier_id=3,
                price=1200,
                cost=800,
                stock=15,
                stock_available=15,
                min_stock=5,
                location="Almacén A-3",
                warranty_months=12,
                is_active=True
            ),
            Product(
                sku="EQ-005",
                name="Concentrador de Oxígeno",
                description="Concentrador de oxígeno portátil 5L/min",
                product_type="ambos",
                category_id=1,
                supplier_id=1,
                price=18000,
                rental_price_daily=600,
                rental_price_weekly=3500,
                rental_price_monthly=12000,
                cost=14000,
                stock=4,
                stock_available=2,
                min_stock=1,
                location="Almacén A-4",
                warranty_months=24,
                is_active=True
            ),
            Product(
                sku="INS-002",
                name="Estetoscopio Profesional",
                description="Estetoscopio de doble campana",
                product_type="venta",
                category_id=2,
                supplier_id=2,
                price=850,
                cost=600,
                stock=20,
                stock_available=20,
                min_stock=8,
                location="Almacén B-2",
                warranty_months=12,
                is_active=True
            ),
            Product(
                sku="EQ-006",
                name="Ventilador Mecánico",
                description="Ventilador mecánico portátil para cuidados intensivos",
                product_type="alquiler",
                category_id=1,
                supplier_id=3,
                price=45000,
                rental_price_daily=800,
                rental_price_weekly=5000,
                rental_price_monthly=18000,
                cost=35000,
                stock=2,
                stock_available=1,
                min_stock=1,
                location="Almacén A-5",
                warranty_months=36,
                is_active=True
            ),
            Product(
                sku="CON-002",
                name="Mascarillas N95 (Caja 50 unidades)",
                description="Mascarillas de protección respiratoria N95",
                product_type="venta",
                category_id=4,
                supplier_id=2,
                price=350,
                cost=200,
                stock=100,
                stock_available=100,
                min_stock=50,
                location="Almacén D-2",
                is_active=True
            )
        ]
        for product in products:
            db.add(product)
        db.commit()
        
        print("📋 Creando cotizaciones de ejemplo...")
        # Crear algunas cotizaciones de ejemplo
        for i in range(5):
            quotation = Quotation(
                quotation_number=f"COT-2024{random.randint(1, 12):02d}-{i+1:04d}",
                client_id=random.randint(1, len(clients)),
                created_by=random.randint(1, len(users)),
                status=random.choice(["pendiente", "aceptada", "rechazada"]),
                quotation_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                valid_until=datetime.now() + timedelta(days=random.randint(7, 30)),
                subtotal=random.randint(5000, 50000),
                tax_rate=18,
                tax_amount=0,
                discount_percent=random.randint(0, 15),
                discount_amount=0,
                total=0,
                notes=f"Cotización de ejemplo #{i+1}"
            )
            # Calcular totales
            quotation.tax_amount = quotation.subtotal * (quotation.tax_rate / 100)
            quotation.discount_amount = quotation.subtotal * (quotation.discount_percent / 100)
            quotation.total = quotation.subtotal + quotation.tax_amount - quotation.discount_amount
            
            db.add(quotation)
        db.commit()
        
        print("💰 Creando ventas de ejemplo...")
        # Crear algunas ventas de ejemplo
        for i in range(8):
            sale = Sale(
                sale_number=f"VEN-2024{random.randint(1, 12):02d}-{i+1:04d}",
                invoice_number=f"FAC-2024{random.randint(1, 12):02d}-{i+1:04d}",
                client_id=random.randint(1, len(clients)),
                created_by=random.randint(1, len(users)),
                status=random.choice(["completada", "pendiente_pago", "parcial"]),
                sale_date=datetime.now() - timedelta(days=random.randint(1, 60)),
                subtotal=random.randint(3000, 40000),
                tax_rate=18,
                tax_amount=0,
                discount_amount=random.randint(0, 2000),
                total=0,
                paid_amount=0,
                balance=0,
                payment_method=random.choice(["efectivo", "transferencia", "tarjeta", "credito"]),
                notes=f"Venta de ejemplo #{i+1}"
            )
            # Calcular totales
            sale.tax_amount = sale.subtotal * (sale.tax_rate / 100)
            sale.total = sale.subtotal + sale.tax_amount - sale.discount_amount
            
            if sale.payment_method == "credito":
                sale.paid_amount = random.randint(0, int(sale.total * 0.5))
            else:
                sale.paid_amount = sale.total
                
            sale.balance = sale.total - sale.paid_amount
            
            db.add(sale)
        db.commit()
        
        print("🏥 Creando alquileres de ejemplo...")
        # Crear algunos alquileres de ejemplo
        for i in range(6):
            start_date = datetime.now() - timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=random.randint(7, 30))
            
            rental = Rental(
                rental_number=f"ALQ-2024{random.randint(1, 12):02d}-{i+1:04d}",
                client_id=random.randint(1, len(clients)),
                product_id=random.randint(1, len(products)),
                created_by=random.randint(1, len(users)),
                status=random.choice(["activo", "devuelto", "vencido"]),
                start_date=start_date,
                end_date=end_date,
                rental_period=random.choice(["daily", "weekly", "monthly"]),
                rental_price=random.randint(300, 2000),
                deposit=random.randint(1000, 5000),
                total_cost=0,
                paid_amount=0,
                balance=0,
                notes=f"Alquiler de ejemplo #{i+1}"
            )
            
            # Calcular costo total
            days = (rental.end_date - rental.start_date).days
            if rental.rental_period == "daily":
                rental.total_cost = rental.rental_price * days
            elif rental.rental_period == "weekly":
                weeks = days / 7
                rental.total_cost = rental.rental_price * weeks
            elif rental.rental_period == "monthly":
                months = days / 30
                rental.total_cost = rental.rental_price * months
            
            rental.paid_amount = rental.deposit
            rental.balance = rental.total_cost - rental.paid_amount
            
            db.add(rental)
        db.commit()
        
        print("📊 Creando movimientos de inventario de ejemplo...")
        # Crear algunos movimientos de inventario
        for i in range(20):
            movement = InventoryMovement(
                product_id=random.randint(1, len(products)),
                user_id=random.randint(1, len(users)),
                movement_type=random.choice(["entrada", "salida", "ajuste"]),
                quantity=random.randint(1, 10),
                previous_stock=random.randint(0, 50),
                new_stock=0,
                reason=f"Movimiento de ejemplo #{i+1}",
                created_at=datetime.now() - timedelta(days=random.randint(1, 90))
            )
            
            if movement.movement_type == "entrada":
                movement.new_stock = movement.previous_stock + movement.quantity
            elif movement.movement_type == "salida":
                movement.new_stock = max(0, movement.previous_stock - movement.quantity)
            else:  # ajuste
                movement.new_stock = movement.quantity
                
            db.add(movement)
        db.commit()
        
        print("✅ Base de datos extendida inicializada correctamente!")
        print("\n" + "="*70)
        print("📊 DATOS DE EJEMPLO CREADOS:")
        print("="*70)
        print("\n👤 USUARIOS:")
        print("   Admin: admin / admin123")
        print("   Vendedor: vendedor / vendedor123")
        print("   Almacén: almacen / almacen123")
        print("   Empleado: empleado / empleado123")
        print(f"\n👥 Clientes: {len(clients)}")
        print(f"📁 Categorías: {len(categories)}")
        print(f"🚚 Proveedores: {len(suppliers)}")
        print(f"📦 Productos: {len(products)} (venta, alquiler y ambos)")
        print("📋 Cotizaciones: 5")
        print("💰 Ventas: 8")
        print("🏥 Alquileres: 6")
        print("📊 Movimientos: 20")
        print("="*70)
        print("\n🚀 El sistema está listo para usar!")
        print("📝 Puedes crear cotizaciones, ventas y alquileres")
        print("📈 El dashboard mostrará estadísticas reales")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()







