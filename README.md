# Raíz — Gestión y pagos para MYPES y artesanos

Proyecto académico multiplataforma con **React Native + Expo + TypeScript**, API REST con **Node.js + Express** y persistencia en **SQLite**. Interfaz en español, moneda PEN y resumen diario con zona horaria de Lima.

## Requisitos

- Node.js **24 LTS** y npm (el backend utiliza `node:sqlite`).
- Navegador para la versión web; Expo Go compatible con SDK 57 para un teléfono, o un emulador Android.
- Para compilar iOS de forma local se necesita macOS y Xcode; también se puede usar EAS Build.

## Ejecutar

Desde esta carpeta, instala una vez:

```powershell
npm --prefix backend install
npm --prefix mobile install
```

En una terminal:

```powershell
npm run backend
```

En otra terminal:

```powershell
npm run web
```

Abre [http://localhost:8081](http://localhost:8081). API: [http://localhost:4000/api/health](http://localhost:4000/api/health).

Para Android o iOS:

```powershell
npm run mobile
```

**Teléfono físico:** copia `mobile/.env.example` a `mobile/.env` y cambia `EXPO_PUBLIC_API_URL` por `http://IP_LOCAL_DE_TU_PC:4000/api`. Ambos equipos deben estar en la misma red. Permite el acceso a los puertos 4000 y 8081 en el firewall de la red privada y reinicia Expo después de modificar `.env`. El emulador Android utiliza `10.0.2.2` automáticamente. En iOS Simulator se utiliza `localhost`.

## Cuenta de demostración

| Campo | Valor |
| --- | --- |
| Correo | demo@raiz.pe |
| Contraseña | Raiz2026! |
| Negocio | Tejidos de mi Tierra |

La primera ejecución crea `backend/data/raiz.db` con productos, clientes y ventas de ejemplo. Cada cuenta nueva empieza vacía y tiene sus propios datos. Para una base sin datos demo configura `SEED_DEMO=false` antes de la primera ejecución. No publiques una instancia con las credenciales demo habilitadas.

## Funciones

- Registro, inicio y cierre de sesión con caducidad de siete días.
- Resumen de cobros de hoy, pendientes, productos activos y últimos movimientos.
- Gráfico de cobros de siete días y alertas de stock mínimo.
- Crear, editar y retirar productos; búsqueda y filtros por categoría o stock bajo.
- Crear y editar clientes; búsqueda por nombre o teléfono.
- Venta con varios productos, cliente opcional y descuento automático del inventario.
- Cobro completo por Yape, Plin, transferencia o efectivo; referencia obligatoria en medios digitales.
- Anular una venta pendiente y devolver sus existencias una sola vez.
- Compartir una constancia interna mediante la función del dispositivo o navegador compatible.
- Editar los datos del negocio; menú lateral en escritorio y navegación inferior en móvil.
- Diseño en blanco y negro con glassmorphism y neumorphism: paneles con desenfoque, degradados neutros, bordes luminosos, botones elevados y campos con sombras interiores. Se utiliza Expo Blur con un fondo compartido; en Android anterior a 12 el cristal utiliza transparencia para evitar el coste de desenfoque.

**Alcance de pagos:** se registra manualmente un abono que el comerciante confirma haber recibido. La app no mueve dinero ni verifica operaciones en Yape, Plin o bancos. Las constancias no son comprobantes SUNAT. No existe integración con pasarelas ni generación de QR bancario.

## Organización

```text
backend/
  src/app.js          Rutas, autenticación, validación y operaciones
  src/database.js     Esquema SQLite y datos de demostración
  src/server.js       Arranque HTTP
  test/api.test.js    Pruebas de integración con SQLite en memoria
mobile/
  src/app/           Rutas Expo Router y pantallas
  src/components/    Componentes compartidos y estilos
  src/lib/           Estado, cliente HTTP y tipos
docs/
  Informe_Raiz.docx   Informe editable con capturas móviles
  Informe_Raiz_Movil.docx   Copia identificada con vistas móviles en páginas 6 a 8
  Informe_Raiz_Blanco_Negro.docx   Edición monocroma con seis capturas móviles nuevas
  Informe_Raiz.md     Contenido en texto
  API.md             Contrato HTTP
  DEMOSTRACION.md     Recorrido de exposición y validación en dispositivos
scripts/
  build_report.py    Generador del informe con python-docx
```

## Comprobaciones

```powershell
npm test
npm run typecheck
npm --prefix mobile run lint
npm --prefix mobile run export:web
```

La compilación web no sustituye pruebas en dispositivos Android e iOS. El documento de demostración incluye los casos pendientes en dispositivos físicos. Los formularios conservan sus datos mientras se envían y muestran errores de red; las escrituras requieren conexión con el backend. No hay sincronización offline.

Consulta `docs/VERIFICACION.md` para el alcance de las comprobaciones y el estado de los avisos de dependencias del SDK.

## Configuración del backend

Copia opcionalmente `backend/.env.example` a `backend/.env`. Variables: `PORT`, `DATABASE_PATH`, `CORS_ORIGIN` (orígenes web separados por coma), `SEED_DEMO`. La ruta de base se resuelve desde el directorio de ejecución del backend. No guardes `.env` ni bases con datos reales en Git. Para uso público se deben configurar HTTPS, copias de seguridad y operación con un proveedor real de pagos. Esta entrega está preparada para ejecución académica local.

Las contraseñas se derivan con scrypt y sal individual; los tokens aleatorios se almacenan como SHA-256 en SQLite. En móvil el token se guarda con SecureStore; en web, en sessionStorage. El servidor filtra todas las operaciones por cuenta. Los importes se calculan con centavos enteros y el precio autorizado procede del servidor.

## Sustento y documentación

El diseño propuesto relaciona el problema de registros dispersos con catálogo, stock, ventas y cobros. Los materiales previos del curso no se encuentran en esta carpeta: al incorporarlos, se debe contrastar su especificación con la matriz del informe. Las necesidades locales se presentan como hipótesis para validar, sin atribuir entrevistas inexistentes.

Referencias técnicas: [React Native](https://reactnative.dev/docs/components-and-apis), [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), [Expo Router](https://docs.expo.dev/router/introduction/), [Express](https://expressjs.com/), [SQLite en Node.js](https://nodejs.org/api/sqlite.html).
