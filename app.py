import streamlit as st
import os
import zipfile
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageOps
import tempfile
import gc
import re 

# Diseño de la página web
st.set_page_config(page_title="DUB x stfu | Collage Creator", page_icon="🗂️", layout="centered")

# --- CONFIGURACIÓN BASE ---
A3_WIDTH = 4960
A3_HEIGHT = 3508
MARGIN_EXTERIOR = 120 
HEADER_HEIGHT = 450 # El espacio extra arriba para los logos y el título
COLOR_FONDO = (245, 245, 245) # Un gris perla muy sutil por defecto

def obtener_fuente(nombre_archivo, tamano):
    try:
        if "Por defecto" not in nombre_archivo:
            return ImageFont.truetype(nombre_archivo, tamano)
    except:
        pass
    return ImageFont.load_default()

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Configuración DUB x stfu")
st.sidebar.write("Ajusta el estilo del collage.")

fuentes_disponibles = [f for f in os.listdir('.') if f.lower().endswith(('.ttf', '.otf'))]
if not fuentes_disponibles:
    fuentes_disponibles = ["Por defecto (Sube un .ttf a GitHub)"]

opcion_fuente = st.sidebar.selectbox("1. Selecciona la Tipografía:", fuentes_disponibles)
hex_color = st.sidebar.color_picker("2. Selecciona el Color del Título:", "#2D2963") # Azul oscuro DUB por defecto
color_rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
tamanio_fuente_inicial = st.sidebar.slider("3. Tamaño máximo del Texto:", 100, 2000, 550, 50)

formato_texto = st.sidebar.radio(
    "4. Formato del Título:",
    ("MAYÚSCULAS", "Tipo Título"),
    index=0 # Mayúsculas por defecto para esta app
)

espaciado_fotos = st.sidebar.slider("5. Espaciado entre fotos:", 0, 150, 30, 10)

st.sidebar.write("---")

# --- VISTA PREVIA INDIVIDUAL ---
st.sidebar.write("👀 **Vista previa de la fuente:**")
try:
    preview_img = Image.new('RGB', (600, 200), COLOR_FONDO)
    draw_preview = ImageDraw.Draw(preview_img)
    fuente_preview = obtener_fuente(opcion_fuente, 70)
    
    if formato_texto == "MAYÚSCULAS":
        texto_test = "PREVIEW'S"
    else:
        texto_test = "Preview's"
    
    draw_preview.text((300, 100), texto_test, fill=color_rgb, font=fuente_preview, anchor="mm")
    st.sidebar.image(preview_img, use_container_width=True)
except Exception:
    st.sidebar.write("Sube una fuente para ver la vista previa.")

st.sidebar.write("---")

# --- PANEL PRINCIPAL ---
st.title("🗂️ DUB x stfu | Collage Creator")
st.write("Generador automatizado de presentaciones de colección en formato A3.")
st.info("⚠️ Asegúrate de tener 'dub.png' y 'stfu.png' subidos a tu GitHub para que aparezcan los logos en las esquinas.")

def limpiar_nombre_desfile(carpeta):
    nombre = carpeta.replace("___", " & ")
    partes = nombre.split("_")
    if len(partes) > 1 and partes[-1].islower() and len(partes[-1]) <= 5:
        partes = partes[:-1]
    nombre_limpio = " ".join(partes).replace("  ", " ")
    return nombre_limpio

archivo_zip_subido = st.file_uploader("Arrastra aquí el archivo ZIP de las colecciones", type="zip")

if archivo_zip_subido is not None:
    if st.button("Generar Plantillas ✨"):
        with st.spinner('Procesando colecciones...'):
            
            dir_temp = tempfile.mkdtemp()
            dir_extraccion = os.path.join(dir_temp, "extraccion")
            dir_resultados = os.path.join(dir_temp, "resultados")
            os.makedirs(dir_extraccion, exist_ok=True)
            os.makedirs(dir_resultados, exist_ok=True)

            ruta_zip_temporal = os.path.join(dir_temp, "subido.zip")
            with open(ruta_zip_temporal, "wb") as f:
                f.write(archivo_zip_subido.getbuffer())
            
            del archivo_zip_subido
            gc.collect()

            shutil.unpack_archive(ruta_zip_temporal, dir_extraccion)
            os.remove(ruta_zip_temporal)

            carpetas_con_fotos = []
            for raiz, directorios, archivos in os.walk(dir_extraccion):
                if "__MACOSX" in raiz:
                    continue
                if any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')) for f in archivos):
                    carpetas_con_fotos.append(raiz)

            if not carpetas_con_fotos:
                st.error("❌ No se han encontrado fotos en el archivo ZIP.")
            else:
                for ruta_desfile in carpetas_con_fotos:
                    nombre_carpeta = os.path.basename(ruta_desfile)
                    if nombre_carpeta == "extraccion": 
                        nombre_carpeta = "Coleccion_General"

                    texto_base_limpio = limpiar_nombre_desfile(nombre_carpeta)
                    
                    if formato_texto == "MAYÚSCULAS":
                        texto_marca = texto_base_limpio.upper()
                    else:
                        texto_marca = texto_base_limpio.title()
                        texto_marca = texto_marca.replace("Mcc", "McC")
                        texto_marca = re.sub(r"\'([A-Z])\b", lambda m: "'" + m.group(1).lower(), texto_marca)

                    archivos = [f for f in os.listdir(ruta_desfile) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif'))]
                    archivos.sort()
                    num_imagenes = len(archivos)
                    
                    lienzo = Image.new('RGB', (A3_WIDTH, A3_HEIGHT), COLOR_FONDO)
                    
                    # --- 1. ZONA CABECERA: LOGOS ---
                    altura_logos = 250
                    ancho_reserva_izq = 0
                    ancho_reserva_der = 0
                    
                    # Logo Izquierdo (DUB)
                    try:
                        if os.path.exists('dub.png'):
                            logo_dub = Image.open('dub.png').convert("RGBA")
                            proporcion = altura_logos / float(logo_dub.height)
                            nuevo_ancho = int(float(logo_dub.width) * float(proporcion))
                            logo_dub = logo_dub.resize((nuevo_ancho, altura_logos), Image.Resampling.LANCZOS)
                            lienzo.paste(logo_dub, (MARGIN_EXTERIOR, MARGIN_EXTERIOR), logo_dub)
                            ancho_reserva_izq = nuevo_ancho
                    except Exception:
                        pass

                    # Logo Derecho (stfu)
                    try:
                        if os.path.exists('stfu.png'):
                            logo_stfu = Image.open('stfu.png').convert("RGBA")
                            proporcion = altura_logos / float(logo_stfu.height)
                            nuevo_ancho = int(float(logo_stfu.width) * float(proporcion))
                            logo_stfu = logo_stfu.resize((nuevo_ancho, altura_logos), Image.Resampling.LANCZOS)
                            x_stfu = A3_WIDTH - MARGIN_EXTERIOR - nuevo_ancho
                            lienzo.paste(logo_stfu, (x_stfu, MARGIN_EXTERIOR), logo_stfu)
                            ancho_reserva_der = nuevo_ancho
                    except Exception:
                        pass

                    # --- 2. ZONA CABECERA: TÍTULO CENTRADO Y ESCALABLE ---
                    draw = ImageDraw.Draw(lienzo)
                    current_tamanio = tamanio_fuente_inicial
                    fuente = obtener_fuente(opcion_fuente, current_tamanio)
                    
                    # Calcula el espacio seguro en el medio (toma el logo más ancho para que quede simétrico)
                    reserva_maxima = max(ancho_reserva_izq, ancho_reserva_der)
                    # El ancho máximo es el A3 entero menos los márgenes, menos los logos, menos 150px de aire por cada lado
                    max_text_width = A3_WIDTH - (MARGIN_EXTERIOR * 2) - (reserva_maxima * 2) - 300

                    try:
                        bbox = draw.textbbox((0, 0), texto_marca, font=fuente)
                        text_w = bbox[2] - bbox[0]
                        
                        while text_w > max_text_width and current_tamanio > 100:
                            current_tamanio -= 20
                            fuente = obtener_fuente(opcion_fuente, current_tamanio)
                            bbox = draw.textbbox((0, 0), texto_marca, font=fuente)
                            text_w = bbox[2] - bbox[0]

                        centro_x = A3_WIDTH // 2
                        # Centramos el texto verticalmente alineado con los logos
                        centro_y = MARGIN_EXTERIOR + (altura_logos // 2)
                        draw.text((centro_x, centro_y), texto_marca, fill=color_rgb, font=fuente, anchor="mm")
                    except Exception:
                        # Si falla, simplemente lo escribe arriba al centro
                        draw.text((A3_WIDTH // 2, MARGIN_EXTERIOR + 100), texto_marca, fill=color_rgb, font=fuente, anchor="mm")

                    # --- 3. ZONA GRID: FOTOS ---
                    filas = 2
                    columnas = max(1, (num_imagenes + 1) // 2)
                    
                    # El inicio del eje Y baja para respetar la cabecera
                    start_y_grid = MARGIN_EXTERIOR + HEADER_HEIGHT
                    alto_disponible = A3_HEIGHT - start_y_grid - MARGIN_EXTERIOR
                    
                    espacio_x = (A3_WIDTH - (2 * MARGIN_EXTERIOR) - ((columnas - 1) * espaciado_fotos)) // columnas
                    espacio_y = (alto_disponible - ((filas - 1) * espaciado_fotos)) // filas

                    # Control de proporción (evita recortes extremos en pocas fotos)
                    ancho_maximo_permitido = int(espacio_y * 0.75) 
                    ancho_foto = min(espacio_x, ancho_maximo_permitido)

                    for idx, archivo in enumerate(archivos):
                        ruta_img = os.path.join(ruta_desfile, archivo)
                        try:
                            with Image.open(ruta_img) as img:
                                img_recortada = ImageOps.fit(img, (ancho_foto, espacio_y), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

                                fila_actual = idx // columnas
                                col_actual = idx % columnas

                                x_columna = MARGIN_EXTERIOR + col_actual * (espacio_x + espaciado_fotos)
                                x = x_columna + (espacio_x - ancho_foto) // 2 
                                
                                # Aplicamos el Start Y del Grid
                                y = start_y_grid + fila_actual * (espacio_y + espaciado_fotos)

                                lienzo.paste(img_recortada, (x, y))
                                del img_recortada
                        except Exception:
                            pass

                    nombre_archivo_salida = f"A3_{nombre_carpeta}.jpg"
                    ruta_salida = os.path.join(dir_resultados, nombre_archivo_salida)
                    lienzo.save(ruta_salida, quality=100, dpi=(300, 300))
                    
                    del lienzo
                    gc.collect() 

                ruta_zip_final = os.path.join(dir_temp, "Colecciones_A3_Terminadas.zip")
                with zipfile.ZipFile(ruta_zip_final, 'w') as zipf:
                    for archivo in os.listdir(dir_resultados):
                        if archivo.endswith('.jpg'):
                            zipf.write(os.path.join(dir_resultados, archivo), arcname=archivo)

                st.success("¡Completado! Documentos listos para descargar.")
                
                with open(ruta_zip_final, "rb") as fp:
                    st.download_button(
                        label="⬇️ Descargar archivos A3",
                        data=fp,
                        file_name="Plantillas_A3_DUB_stfu.zip",
                        mime="application/zip"
                    )
