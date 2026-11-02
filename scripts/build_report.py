"""Generate the editable academic report and its Markdown source."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
OUT.mkdir(exist_ok=True)
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin, sec.bottom_margin = Cm(1.9), Cm(1.8)
sec.left_margin = sec.right_margin = Cm(2)
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(10.5)
style.paragraph_format.space_after = Pt(7)
style.paragraph_format.line_spacing = 1.12
for key, size in [('Title', 29), ('Subtitle', 15), ('Heading 1', 20), ('Heading 2', 12)]:
    st = doc.styles[key]
    st.font.name = 'Calibri'
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor.from_string('000000' if key == 'Title' else '111111')
    st.paragraph_format.space_after = Pt(11)
footer = sec.footer.paragraphs[0]
footer.alignment = 2
run = footer.add_run('Raíz    ·    ')
run.font.size = Pt(9)
fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); footer._p.append(fld)
md = []

def p(text, style=None):
    doc.add_paragraph(text, style)
    md.append(text + '\n')

def h(text):
    doc.add_heading(text, 2); md.append('## ' + text + '\n')

def page(title):
    doc.add_page_break()
    doc.add_heading(title, 1)
    md.append('\n# ' + title + '\n')

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.autofit = False
    t.style = 'Table Grid'
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        border=OxmlElement('w:'+edge);border.set(qn('w:val'),'single');border.set(qn('w:sz'),'3');border.set(qn('w:color'),'E3E3E3');borders.append(border)
    t._tbl.tblPr.append(borders)
    for i, label in enumerate(headers): t.rows[0].cells[i].text = label
    repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
    for row in t.rows:
        no_split = OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(no_split)
        for i, cell in enumerate(row.cells):
            if widths: cell.width = Cm(widths[i])
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(5)
                para.paragraph_format.space_before = Pt(4)
                for run in para.runs: run.font.size = Pt(9.3)
    md.append('| ' + ' | '.join(headers) + ' |')
    md.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
    md.extend('| ' + ' | '.join(str(v) for v in row) + ' |' for row in rows)
    md.append('')

def mobile_evidence():
    captures = [
        ('01-acceso', 'Acceso a la app', 'Inicio de sesión en el teléfono con correo y contraseña.'),
        ('02-resumen', 'Resumen del negocio', 'Vista inicial con cobros, pendientes y navegación inferior.'),
        ('03-productos', 'Productos e inventario', 'Catálogo móvil con búsqueda, filtros y existencias por producto.'),
        ('04-clientes', 'Gestión de clientes', 'Listado de contactos y acceso al registro de clientes.'),
        ('05-ventas', 'Ventas y cobros', 'Consulta de importes y estados de las ventas desde el teléfono.'),
        ('06-cobro', 'Registro del cobro', 'Formulario móvil con referencia y confirmación manual del abono.'),
    ]
    titles = ['Capturas móviles de acceso y resumen', 'Capturas móviles de productos y clientes', 'Capturas móviles de ventas y cobros']
    for pair in range(3):
        page(titles[pair])
        p('Interfaz vertical de 390 × 844 píxeles, ejecutada en navegador con emulación móvil y datos de demostración.')
        t = doc.add_table(rows=1, cols=2)
        t.autofit = False
        borders = OxmlElement('w:tblBorders')
        for edge in ['top','left','bottom','right','insideH','insideV']:
            b = OxmlElement('w:' + edge); b.set(qn('w:val'), 'nil'); borders.append(b)
        t._tbl.tblPr.append(borders)
        no_split = OxmlElement('w:cantSplit'); t.rows[0]._tr.get_or_add_trPr().append(no_split)
        for col in range(2):
            i = pair * 2 + col
            file, title, description = captures[i]
            cell = t.cell(0, col); cell.width = Cm(8.5)
            title_p = cell.paragraphs[0]
            title_p.paragraph_format.space_after = Pt(8)
            r = title_p.add_run(f'Figura {i + 1}  {title}'); r.bold = True; r.font.size = Pt(11); r.font.color.rgb = RGBColor.from_string('111111')
            image_p = cell.add_paragraph(); image_p.paragraph_format.space_after = Pt(8)
            picture = image_p.add_run().add_picture(str(OUT / 'evidencias' / 'movil-blanco-negro' / f'{file}.png'), width=Cm(7.15))
            picture._inline.docPr.set('descr', title + '. ' + description)
            caption = cell.add_paragraph(description)
            caption.paragraph_format.space_after = Pt(0)
            for r in caption.runs: r.font.size = Pt(9.5)
            md.append(f'## Figura {i + 1} {title}\n\n![{title}](evidencias/movil-blanco-negro/{file}.png)\n\n{description}\n')

def diagram():
    im=Image.new('RGB',(1600,860),'#FFFFFF'); d=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/calibri.ttf',30)
    bold=ImageFont.truetype('C:/Windows/Fonts/calibrib.ttf',31)
    def box(x,y,w,ht,text,fill):
        d.rounded_rectangle((x,y,x+w,y+ht),radius=22,fill=fill)
        lines=[]
        for line in text.split('\n'):lines.extend(textwrap.wrap(line, int(w/16)))
        yy=y+(ht-len(lines)*38)/2
        for line in lines:
            d.text((x+w/2,yy),line,font=font,fill='#343434',anchor='mt');yy+=38
    for x in [40,560,1080]:
        d.line((x+240,260,x+240,300,800,300,800,345),fill='#8F8F8F',width=4)
        d.line((x+240,610,x+240,560,800,560,800,515),fill='#8F8F8F',width=4)
    for x, text in zip([40,560,1080],['Cobros pendientes\ndifíciles de identificar','Decisiones con poca\ninformación del negocio','Tiempo adicional para\nrevisar ventas y stock']):box(x,90,480,170,text,'#EAEAEA')
    box(190,345,1220,170,'Dificultad para gestionar productos, ventas y cobros\nen MYPES y talleres artesanales locales','#E5E5E5')
    for x, text in zip([40,560,1080],['Registros dispersos\nen papel y mensajes','Control manual de\nexistencias y precios','Abonos sin vínculo\ncon cada venta']):box(x,610,480,170,text,'#EEEEEE')
    d.text((45,40),'EFECTOS',font=bold,fill='#7C7C7C')
    d.text((45,810),'CAUSAS',font=bold,fill='#7C7C7C')
    path=OUT/'arbol_problemas.png';im.save(path)
    return path

doc.add_paragraph('Plataforma de gestión y pagos digitales\npara MYPES y artesanos locales', 'Title')
doc.add_paragraph('Informe de desarrollo de la aplicación Raíz', 'Subtitle')
p('Aplicación móvil multiplataforma con React Native y backend de servicios REST')
p('Trabajo académico de proyección social', 'Heading 2')
table(['Datos académicos', 'Información'], [('Institución','Completar'),('Curso','Completar'),('Estudiante o integrantes','Completar'),('Docente','Completar'),('Fecha','1 de noviembre de 2026')], [5,12])
h('Resumen del proyecto')
p('Raíz reúne catálogo, existencias, clientes, ventas y registro de cobros para pequeños negocios y talleres artesanales. La solución implementa un flujo completo: crear productos, registrar una venta, descontar stock y confirmar el abono recibido. El objetivo social es facilitar tareas de gestión a emprendedores que necesitan herramientas comprensibles y de bajo costo de acceso.')
p('La aplicación usa React Native con Expo para compartir la interfaz entre Android, iOS y web. El backend utiliza Express y SQLite. Los pagos se registran manualmente con fines demostrativos; la plataforma no transfiere dinero ni consulta saldos bancarios. La evaluación técnica incluye pruebas de integración del backend y compilación web; la validación con beneficiarios y en dispositivos físicos forma parte del plan de evaluación.')
h('Organización del informe')
p('Se presenta el contexto, el árbol de problemas, los requisitos, las interfaces, la arquitectura y los componentes del framework. Las seis capturas de la interfaz móvil se encuentran en las páginas 6 a 8, dentro de la sección de diseño. Luego se describe la implementación, el cronograma de dos semanas, la verificación y el uso de la aplicación.')

page('1 Contexto y objetivos')
h('Problema y población beneficiaria')
p('El proyecto se dirige a responsables de MYPES y artesanos locales que venden productos en talleres, ferias o mediante contacto directo. Su operación puede incluir pedidos por mensajes, pagos por billeteras digitales y anotaciones separadas del inventario. La hipótesis de trabajo es que esta dispersión dificulta relacionar un abono con una venta, conocer existencias y reconocer saldos pendientes.')
p('PRODUCE informó que las micro y pequeñas empresas representaban el 99,1 % de las empresas formales al cierre de 2024 [1]. Este dato respalda la relevancia del segmento empresarial; no demuestra que todos sus negocios tengan el mismo problema. El BCRP describe la conexión entre billeteras y cuentas mediante su estrategia de interoperabilidad [2]. Ese contexto justifica registrar diversos medios de cobro en una misma herramienta.')
h('Objetivo general')
p('Desarrollar una aplicación multiplataforma que permita a MYPES y artesanos locales organizar productos, existencias, clientes, ventas y cobros en un registro centralizado y fácil de consultar.')
h('Objetivos específicos')
for text in [
 'Mantener un catálogo con precio, categoría, existencias y umbral de reposición para cada producto.',
 'Registrar ventas con varios productos y actualizar el inventario mediante una operación atómica.',
 'Relacionar cada venta con su estado de pago y con la referencia del abono cuando corresponda.',
 'Mostrar un resumen de cobros, ventas pendientes y productos con stock bajo.',
 'Aplicar componentes de React Native que permitan formularios y navegación consistentes en las plataformas objetivo.'
]: p(text,'List Bullet')
h('Alcance y delimitación')
p('El producto mínimo atiende a una persona responsable por negocio. Cada cuenta administra sus propios datos. Se incluyen ventas directas, cobros completos y anulación de ventas pendientes. Se requiere conexión con la API para consultar y guardar información. Quedan como ampliaciones la facturación electrónica, pagos parciales, roles de colaboradores, sincronización offline y conciliación automática con proveedores de pago.')

page('2 Árbol de problemas y respuesta funcional')
p('El árbol organiza las causas operativas y sus posibles consecuencias. Se utiliza como modelo inicial para orientar la solución y preparar la consulta con beneficiarios; las relaciones deberán contrastarse durante el piloto local.')
doc.add_picture(str(diagram()),width=Cm(17))
md.append('![Árbol de problemas](arbol_problemas.png)\n')
h('Del problema a las funcionalidades')
table(['Causa identificada','Respuesta implementada','Efecto esperado'],[
('Registros dispersos','Catálogo y listado central de ventas','Encontrar la información en un mismo espacio'),
('Control manual de existencias','Descuento de stock y alerta de mínimos','Reducir ventas de unidades no disponibles'),
('Abonos desvinculados de ventas','Cobro asociado a una venta y su referencia','Reconocer ventas pagadas y pendientes'),
('Poca visibilidad del negocio','Resumen y gráfico de siete días','Facilitar la revisión de los movimientos')],[4.5,6,6.5])
h('Árbol de objetivos')
p('El objetivo central consiste en mejorar el control operativo de ventas e inventario. Sus medios son centralizar los registros, automatizar el cálculo de totales y vincular el cobro con su venta. Los fines esperados son mayor claridad del negocio y menor esfuerzo de revisión. Estos fines se evaluarán mediante tareas observables; no se atribuye al prototipo un incremento económico ya comprobado.')

page('3 Requisitos y criterios de aceptación')
p('El responsable del negocio es el actor de la aplicación. El cliente es una entidad de la venta y no necesita cuenta. Los siguientes requisitos establecen conductas verificables y su vínculo con el problema operativo.')
table(['Código','Requisito funcional','Criterio de aceptación'],[
('RF01','Registrar cuenta e iniciar sesión','Una cuenta nueva empieza vacía y solo accede a sus datos.'),
('RF02','Administrar productos','Crear, editar y retirar sin borrar el detalle de ventas previas.'),
('RF03','Consultar existencias','Mostrar cantidad y señalar productos bajo su umbral mínimo.'),
('RF04','Administrar clientes','Guardar nombre y contacto opcional; buscar por nombre o teléfono.'),
('RF05','Registrar venta','Elegir productos y cantidades; calcular precio autorizado en servidor.'),
('RF06','Validar stock','Rechazar una venta que supere existencias sin cambios parciales.'),
('RF07','Registrar cobro','Exigir referencia digital y permitir un cobro completo por venta.'),
('RF08','Anular venta pendiente','Reponer el inventario una vez y conservar el registro anulado.'),
('RF09','Consultar resumen','Ver cobrado hoy, pendiente, ventas, alertas y serie de siete días.'),
('RF10','Compartir constancia','Mostrar detalle, total y estado como constancia interna.'),
('RF11','Actualizar negocio','Guardar responsable, nombre comercial, teléfono y ubicación.')],[1.6,5.1,10.3])
h('Requisitos no funcionales')
table(['Código','Condición de diseño'],[
('RNF01','Compartir el código de interfaz para Android, iOS y web con React Native y Expo.'),
('RNF02','Guardar datos en SQLite y conservarlos después del reinicio del servidor.'),
('RNF03','Usar contraseñas derivadas con sal y sesiones con vencimiento y revocación.'),
('RNF04','Mostrar mensajes de validación y de conexión sin descartar el formulario.'),
('RNF05','Adaptar navegación y distribución a pantallas pequeñas y grandes.'),
('RNF06','Usar centavos enteros y transacciones para evitar inconsistencias de dinero y stock.')],[1.6,15.4])

page('4 Diseño de las interfaces')
p('La interfaz combina glassmorphism y neumorphism con una paleta de blanco y negro, con grises para distinguir superficies. El cristal se representa con paneles translúcidos, desenfoque y bordes luminosos; el relieve utiliza sombras claras y oscuras. Los importes se muestran en soles y los estados incluyen texto. Los formularios conservan etiquetas visibles y nombres de accesibilidad.')
table(['Pantalla','Función ligada al árbol de problemas'],[
('Acceso y registro','Crear el espacio privado del responsable del negocio.'),
('Mi resumen','Concentrar cobros, pendientes, alertas y últimos movimientos.'),
('Mis productos','Organizar precios y existencias para evitar registros dispersos.'),
('Mis clientes','Seleccionar destinatarios frecuentes sin reescribir sus datos.'),
('Ventas y cobros','Relacionar productos vendidos, cliente, importe y estado del pago.'),
('Mi emprendimiento','Mantener la identificación y el contacto del responsable.')],[4,13])
h('Flujo de venta')
p('Resumen → Nueva venta → Elegir cliente o cliente general → Agregar cantidades → Revisar total → Crear venta pendiente → Seleccionar medio de cobro → Ingresar referencia → Confirmar abono recibido. El inventario se descuenta al crear la venta; al anular una venta pendiente se repone. La confirmación manual comunica claramente el alcance del registro de pagos.')
h('Navegación y adaptación')
p('La aplicación móvil utiliza navegación inferior para acceder al resumen, productos, ventas, clientes y negocio. La selección activa tiene un relieve hundido y se reconoce por el color y el texto. Las tres páginas siguientes presentan seis capturas verticales de la interfaz móvil, con cristal y relieve, dentro de esta sección de diseño.')
h('Presentación de los formularios')
p('Los campos de entrada tienen sombras interiores y un borde de enfoque; los botones presentan elevación y cambian al pulsarlos. Las ventanas de registro y edición utilizan cristal y permiten desplazamiento. Antes de registrar un cobro se solicita la referencia digital y la confirmación de recepción del importe completo. El contraste de los textos se mantiene sobre fondos claros.')

mobile_evidence()

page('5 Arquitectura y modelo de datos')
p('La solución sigue una arquitectura cliente servidor. React Native presenta formularios y consultas; un cliente HTTP central agrega la sesión a las peticiones. Express valida cada entrada, aplica reglas del negocio y escribe en SQLite. El servidor calcula los totales y decide si una operación es admisible, aunque el cliente también valide para facilitar el uso.')
table(['Capa','Tecnología','Responsabilidad'],[
('Presentación','React Native y Expo SDK 57','Pantallas, navegación, estilos y controles.'),
('Estado y acceso a datos','Context, hooks y fetch','Sesión, carga compartida y peticiones HTTP.'),
('Servicios','Node.js 24 y Express 5','API REST, autenticación y reglas de negocio.'),
('Validación','Zod','Esquemas de registro, producto, cliente, venta y cobro.'),
('Persistencia','SQLite y node:sqlite','Tablas relacionadas, restricciones y transacciones.')],[3,5,9])
h('Relaciones de las entidades')
table(['Entidad','Datos principales y relaciones'],[
('users','Identidad, correo único, contraseña derivada y datos del negocio.'),
('sessions','Hash del token, usuario y vencimiento; varias sesiones por usuario.'),
('products','Propietario, categoría, precio en centavos, stock y estado activo.'),
('customers','Propietario, nombre y contactos opcionales.'),
('sales','Propietario, cliente opcional, total, estado, fecha y UUID de solicitud.'),
('sale_items','Venta, producto, nombre y precio histórico, cantidad.'),
('payments','Una venta como máximo por cobro; método, referencia, importe y fecha.')],[3,14])
h('Decisiones de implementación')
p('El esquema representa un negocio por usuario. Se conservan nombre y precio del producto dentro del detalle de la venta, por lo que un cambio posterior de catálogo no altera el historial. El retiro de productos es lógico. Las claves foráneas protegen las relaciones y el diario WAL permite el uso previsto de SQLite. La API ejecuta consultas síncronas de corta duración, una decisión adecuada al alcance local; mayores cargas exigirían revisar el servidor y la persistencia.')

page('6 Investigación de los componentes del framework')
p('React Native ofrece componentes que se traducen a las interfaces de cada plataforma [3]. Expo agrega herramientas y módulos compatibles con su SDK [4]. La selección se relaciona con las tareas del emprendimiento y con el tamaño de las listas del prototipo.')
table(['Componente o API','Aplicación en Raíz','Motivo de uso'],[
('View y Text','Tarjetas, importes, etiquetas y estados','Estructurar el contenido y mantener una jerarquía legible.'),
('TextInput','Datos del negocio, precios y referencias','Capturar texto y elegir teclado decimal, numérico o de correo.'),
('Pressable','Acciones, categorías y selección de productos','Responder a pulsaciones y representar estados deshabilitados.'),
('ScrollView','Pantallas y formularios','Permitir desplazamiento en el conjunto acotado de registros.'),
('Modal','Alta y edición; venta y cobro','Concentrar una tarea y admitir cierre desde el sistema.'),
('KeyboardAvoidingView','Acceso y formularios en iOS','Ajustar el espacio al aparecer el teclado.'),
('ActivityIndicator','Recuperación inicial de la sesión','Comunicar que la aplicación está cargando.'),
('StyleSheet','Paleta y estilos compartidos','Mantener consistencia visual y reutilizar reglas.'),
('BlurView y BlurTargetView','Cristal en paneles, menús y ventanas','Desenfocar un fondo compartido; en Android anterior a 12 se utiliza transparencia [4].'),
('LinearGradient y boxShadow','Fondo, reflejos y relieve de controles','Combinar degradados con sombras dobles e interiores para el neumorphism.'),
('useWindowDimensions','Menú lateral o navegación inferior','Adaptar la distribución al ancho disponible.'),
('Share','Constancia de venta','Invocar opciones de compartir disponibles en cada plataforma.'),
('Expo Router','Rutas y grupo de pantallas privadas','Gestionar navegación mediante archivos y enlaces [5].'),
('SafeAreaView','Contenedor de la aplicación','Respetar áreas del dispositivo reservadas por el sistema.'),
('SecureStore y Crypto','Sesión móvil y UUID de la venta','Guardar el token mediante el sistema y generar identificadores.')],[4,5.3,7.7])
h('Estado compartido y crecimiento')
p('useState mantiene formularios y filtros; useContext comparte datos autenticados; useCallback conserva funciones de consulta. La aplicación renueva las listas después de una mutación. Para catálogos grandes se debe incorporar paginación de API y FlatList, que renderiza listas de forma gradual. La versión actual usa ScrollView para mantener sencilla la demostración y no promete rendimiento con catálogos extensos.')

page('7 Backend y reglas del negocio')
h('Servicios disponibles')
p('La API expone salud, registro, inicio y cierre de sesión, perfil, catálogo, clientes, ventas, cobros y resumen. Los recursos privados exigen un token Bearer. El contrato completo y ejemplos JSON se encuentran en docs/API.md. Las respuestas distinguen validaciones, sesión inválida, recurso inexistente y conflicto de estado.')
table(['Operación','Ruta principal','Regla aplicada'],[
('Acceso','POST /api/auth/login','Credenciales válidas y límite de intentos por IP.'),
('Catálogo','POST /api/products','Precio positivo y stock entero no negativo.'),
('Venta','POST /api/sales','Stock suficiente y precios obtenidos en servidor.'),
('Cobro','POST /api/sales/:id/pay','Venta pendiente y referencia digital obligatoria.'),
('Anulación','POST /api/sales/:id/cancel','Solo pendiente; reposición una vez.'),
('Resumen','GET /api/dashboard','Datos de la cuenta y día definido en America/Lima.')],[3,6.3,7.7])
h('Consistencia de las operaciones')
p('Crear una venta agrupa las líneas repetidas del mismo producto. Luego valida las existencias, calcula el total, inserta venta y detalle y descuenta stock dentro de una transacción. Si falla, se revierte el conjunto. Un UUID de solicitud único por cuenta evita descontar existencias dos veces cuando el cliente reintenta la misma venta. Para otra venta se debe generar un UUID diferente.')
p('Los estados permitidos son pendiente, pagada y anulada. Pendiente puede pasar a pagada o anulada. La base impide más de un cobro por venta. Las ventas pagadas no se anulan mediante este flujo; una devolución es una funcionalidad futura que debe incluir la trazabilidad del movimiento de dinero.')
h('Sesión y límites de los pagos')
p('Las contraseñas se derivan con scrypt y una sal individual. Cada sesión usa un token aleatorio de 32 bytes cuyo hash SHA-256 se guarda en la base; caduca a los siete días y se revoca al salir. Los tokens móviles se guardan con SecureStore y los web en sessionStorage. Cada consulta filtra el identificador del propietario.')
p('Yape, Plin y transferencia se registran como medios de cobro manual. La referencia no se consulta con el proveedor ni es única entre ventas. El operador confirma el abono completo antes de guardarlo. Para operación comercial se requiere integrar un proveedor real, verificar notificaciones del servidor y definir conciliación, devoluciones y manejo de fallos. Las constancias emitidas son registros internos.')

page('8 Plan de desarrollo en dos semanas')
p('El siguiente cronograma distribuye el trabajo de la práctica en catorce días. Es una propuesta de ejecución y seguimiento; las evidencias técnicas de la entrega se describen en el apartado siguiente. La consulta a beneficiarios debe orientar ajustes del vocabulario y del flujo de cobro.')
table(['Día','Actividad','Entregable verificable'],[
('1','Delimitar problema y beneficiarios','Descripción del problema y preguntas de validación.'),
('2','Revisar requisitos y diseño previo','Matriz de requisitos priorizados.'),
('3','Definir árbol y navegación','Árbol de problemas y flujo de venta.'),
('4','Preparar React Native y backend','Estructura ejecutable y conexión de salud.'),
('5','Implementar acceso y aislamiento','Registro, login, sesiones y datos por cuenta.'),
('6','Construir catálogo e inventario','Alta, edición, retiro y alerta de mínimos.'),
('7','Implementar clientes y ventas','Detalle y cálculo autorizado de importes.'),
('8','Implementar cobros y anulación','Estados, referencias y reposición de stock.'),
('9','Integrar resumen y constancia','Indicadores, gráfico y opción de compartir.'),
('10','Revisar presentación adaptable','Interfaz en anchos de móvil y escritorio.'),
('11','Probar API y reglas del negocio','Resultados de integración y correcciones.'),
('12','Ejecutar piloto y pruebas en equipos','Observaciones de beneficiarios y dispositivos.'),
('13','Ajustar interfaz y documentación','Informe, manual y contrato de API.'),
('14','Preparar exposición y entrega','Demostración reproducible y código organizado.')],[1.3,7.2,8.5])
h('Gestión de riesgos del proyecto')
p('La conectividad puede limitar el acceso a la API; por ello los formularios conservan sus datos y muestran un error de conexión. La confirmación manual puede registrar un abono incorrecto; se exige una referencia digital y confirmación explícita del responsable. El alcance debe mantenerse en ventas directas y cobros completos para que las funciones esenciales se puedan demostrar durante la práctica.')

page('9 Verificación técnica y evaluación')
p('Las pruebas del backend usan node:test, una API HTTP real y una base SQLite en memoria. Su objetivo es revisar reglas observables, incluidas operaciones inválidas y el aislamiento entre negocios. La base temporal evita alterar los datos de demostración durante esas pruebas.')
table(['Grupo de prueba','Conducta comprobada','Resultado'],[
('Autenticación','Rechazo de acceso anónimo y contraseña incorrecta.','Aprobado'),
('Cuentas y catálogo','Registro, validación y aislamiento entre propietarios.','Aprobado'),
('Cálculo de venta','Precio del servidor, suma de líneas repetidas e idempotencia.','Aprobado'),
('Existencias','Rechazo sin stock, sin cambios parciales.','Aprobado'),
('Cobros','Referencia obligatoria; rechazo de acceso ajeno y duplicados.','Aprobado'),
('Anulación e historial','Reposición una vez y conservación del detalle histórico.','Aprobado'),
('Perfil y sesión','Edición de clientes, perfil, resumen y revocación del token.','Aprobado')],[3.5,11,2.5])
h('Comprobaciones de la interfaz')
p('La revisión incluye análisis TypeScript, lint y exportación web. El recorrido automatizado en navegador ejecuta acceso, alta de producto, venta, registro del cobro, navegación a un ancho de 390 píxeles y retiro del producto. Las capturas de evidencias corresponden a la ejecución web; una captura angosta no equivale a una prueba del binario nativo.')
h('Evaluación con beneficiarios')
p('Se propone una sesión con tres a cinco comerciantes o artesanos que acepten participar. Cada persona deberá registrar un producto, crear una venta y reconocer si está pagada. Se medirá tiempo por tarea, errores y capacidad de explicar el estado del cobro. Una meta inicial propuesta es que cuatro de cinco participantes completen ambas tareas principales sin asistencia. Esta meta no representa un resultado obtenido.')
h('Validación pendiente en dispositivos')
p('En Android e iOS deben verificarse instalación o apertura en Expo Go compatible, teclado, zonas seguras, recuperación de sesión, navegación y compartir constancias. El guion docs/DEMOSTRACION.md incluye casos con estado pendiente. La entrega del código y la compilación web no acreditan por sí solas una validación en equipos físicos ni una publicación en las tiendas.')

page('10 Instalación y guía de uso')
h('Puesta en marcha')
p('Se necesita Node.js 24 y npm. Desde la carpeta del proyecto se instalan dependencias con npm --prefix backend install y npm --prefix mobile install. En una terminal se ejecuta npm run backend; en otra, npm run mobile. Se abre el proyecto en un teléfono con Expo Go compatible con SDK 57 o en un emulador. La API se consulta en http://localhost:4000/api/health.')
p('La cuenta de demostración es demo@raiz.pe y la contraseña es Raiz2026!. La primera ejecución crea backend/data/raiz.db con ejemplos. Para usar un teléfono físico se configura EXPO_PUBLIC_API_URL en mobile/.env con la dirección local de la computadora y el puerto 4000; ambos equipos deben compartir red. Luego se ejecuta npm run mobile y se abre el proyecto con un entorno compatible con Expo SDK 57.')
h('Recorrido de demostración')
for text in [
 'Entrar a la cuenta demo y observar cobros del día, pendientes y productos con stock bajo.',
 'Registrar un producto con precio S/ 30, cinco unidades y stock mínimo de dos.',
 'Agregar un cliente y crear una venta de dos unidades. Verificar total S/ 60 y stock restante de tres.',
 'Abrir la venta pendiente, elegir un medio de cobro, registrar una referencia de ejemplo y confirmar recepción del abono.',
 'Consultar la venta pagada y compartir su constancia cuando la plataforma lo permita.',
 'Crear otra venta de una unidad y anularla. Confirmar que el inventario vuelva a tres.',
 'Crear una cuenta adicional para comprobar que empieza sin los productos del otro negocio.'
]:p(text,'List Number')
h('Persistencia y mantenimiento local')
p('SQLite conserva los registros al reiniciar el servidor. Se debe respaldar la base antes de cambiarla o eliminarla. Las variables opcionales del backend definen puerto, ruta de base, orígenes CORS y carga demo. Al crear una instancia sin ejemplos se define SEED_DEMO=false antes del primer arranque. Los comandos npm test, npm run typecheck y npm --prefix mobile run lint reproducen las comprobaciones principales.')

page('11 Proyección social y conclusiones')
h('Aporte esperado a la comunidad')
p('La contribución propuesta es facilitar una rutina de gestión accesible desde el teléfono y la web. Relacionar venta y cobro puede ayudar al responsable a identificar obligaciones pendientes. Las alertas de stock permiten preparar reposiciones y las constancias facilitan compartir el detalle con el cliente. El impacto deberá medirse en el piloto; los beneficios económicos no se dan por demostrados.')
p('Una actividad de proyección social puede combinar una breve capacitación, práctica con datos ficticios y acompañamiento para configurar el negocio. El vocabulario debe revisarse con los participantes. Solo deben solicitarse los contactos de clientes necesarios para la operación; la herramienta no necesita claves bancarias, números de tarjeta ni acceso a las billeteras.')
h('Conclusiones')
p('La implementación cubre el flujo mínimo entre producto, venta, inventario y cobro. La lógica del servidor concentra el cálculo de importes y el control de existencias, lo que permite rechazar operaciones inválidas sin dejar cambios parciales. Las pruebas de integración acreditan las reglas incluidas en sus escenarios; la verificación web añade evidencia del recorrido de la interfaz.')
p('React Native y Expo permiten organizar las pantallas en una base común con navegación adaptable. Los componentes seleccionados responden a tareas concretas: entradas de formularios, selección de productos, presentación de estados y compartición de constancias. El backend con SQLite mantiene un despliegue local simple para la práctica.')
p('El registro manual de pagos delimita el alcance de la entrega. La evaluación con emprendedores y las pruebas nativas siguen siendo necesarias para valorar comprensión, accesibilidad y uso en condiciones reales. Como evolución se propone integrar un proveedor de pagos, añadir auditoría de cambios, paginación y una estrategia de operación con conectividad intermitente.')
h('Criterio para la siguiente iteración')
p('Se debe priorizar el ajuste que reduzca los errores observados en las tareas del piloto. Si los participantes confunden registrar un pago con transferir dinero, se revisarán primero el texto y la confirmación del cobro. Si encuentran dificultad al buscar productos, se ajustará la selección y se evaluará paginación antes de ampliar el catálogo. Estas decisiones deben basarse en observaciones registradas.')

page('12 Referencias y recursos de la entrega')
refs=[
('[1] Ministerio de la Producción','PRODUCE Perú cerró el 2024 con 2.34 millones de empresas formales','https://www.gob.pe/institucion/produce/noticias/1168972-produce-peru-cerro-el-2024-con-2-34-millones-de-empresas-formales'),
('[2] Banco Central de Reserva del Perú','Avances en la fase 3 de la estrategia de interoperabilidad','https://investigacion.bcrp.gob.pe/es/investigaciones/revista-moneda/2025-06-30/moneda-202-04'),
('[3] React Native','Core Components and APIs','https://reactnative.dev/docs/components-and-apis'),
('[4] Expo','SDK 57 Reference','https://docs.expo.dev/versions/v57.0.0/'),
('[5] Expo','Introduction to Expo Router','https://docs.expo.dev/router/introduction/'),
('[6] Node.js','SQLite y API de acceso a bases de datos','https://nodejs.org/api/sqlite.html'),
('[7] Express','Documentación del framework','https://expressjs.com/'),
('[8] Expo','SecureStore','https://docs.expo.dev/versions/v57.0.0/sdk/securestore/')]
for author,title,url in refs:
    h(author);p(title);para=doc.add_paragraph(url);para.paragraph_format.space_after=Pt(9)
    for run in para.runs:run.font.size=Pt(8.5)
    md.append(url+'\n')
p('Fecha de consulta de recursos en línea 1 de noviembre de 2026.')
h('Archivos de apoyo')
p('README.md describe instalación y alcance. docs/API.md especifica el contrato HTTP. docs/DEMOSTRACION.md contiene el guion y los casos de validación en dispositivos. backend/test/api.test.js conserva las pruebas reproducibles. scripts/check_web.cjs documenta el recorrido automatizado del navegador. El código de la interfaz se encuentra en mobile/src y el servidor en backend/src.')

# Use monochrome table accents and grayscale diagrams throughout the report.
for t in doc.tables:
    if t.rows[0].cells[0].text.startswith('Figura '):
        continue
    for cell in t.rows[0].cells:
        props=cell._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EDEDED');props.append(shade)
        for para in cell.paragraphs:
            for run in para.runs:run.bold=True;run.font.color.rgb=RGBColor.from_string('343434')
doc.core_properties.title='Plataforma de gestión y pagos digitales para MYPES y artesanos locales'
doc.core_properties.subject='Informe de desarrollo de Raíz con React Native'
doc.core_properties.author=''
# Remove inherited Word title rules and all paragraph border residue.
for root in [doc._element, doc.styles.element]:
    for border in list(root.iter(qn('w:pBdr'))): border.getparent().remove(border)
doc.save(OUT/'Informe_Raiz.docx')
doc.save(OUT/'Informe_Raiz_Movil.docx')
doc.save(OUT/'Informe_Raiz_Blanco_Negro.docx')
(OUT/'Informe_Raiz.md').write_text('\n'.join(md),encoding='utf-8')
print('Created docs/Informe_Raiz.docx and docs/Informe_Raiz.md')
