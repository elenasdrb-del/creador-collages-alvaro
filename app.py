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
HEADER_HEIGHT = 450 

def obtener_fuente(nombre_archivo, tamano):
    try:
        if "Por defecto" not in nombre_archivo:
            return ImageFont.truetype(nombre_archivo, tamano)
    except:
        pass
    return ImageFont.load_default()

def aplicar_opacidad(img, factor_opacidad):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    r, g, b, a = img.split()
    a = a.point(lambda p: p * factor_opacidad)
    return Image.merge('RGBA', (r, g, b, a))

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Configuración DUB x stfu")
st.sidebar.write("Ajusta el estilo del collage.")

fuentes_disponibles = [f for f in os.listdir('.') if f.lower().endswith(('.ttf', '.otf'))]
if not fuentes_disponibles:
    fuentes_disponibles = ["Por defecto (Sube un .ttf a GitHub)"]

opcion_fuente = st.sidebar.selectbox("1. Selecciona la Tipografía:", fuentes_disponibles)

hex_fondo = st.sidebar.color_picker("2. Color de Fondo:", "#1535C5") 
color_fondo_rgb = tuple(int(hex_fondo.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

hex_color_texto = st.sidebar.color_picker("3. Color del Título:", "#FFD1CB")
color_texto_rgb = tuple(int(hex_color_texto.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

tamanio_fuente_inicial = st.sidebar.slider("4. Tamaño máximo del Texto:", 100, 2000, 550, 50)

formato_texto = st.sidebar.radio(
    "5. Formato del Título:",
    ("MAYÚSCULAS", "Tipo Título"),
    index=1 
)

opacidad_logos_pct = st.sidebar.slider("6. Opacidad de Logos Laterales (%):", 5, 100, 20, 5)
opacidad_factor = opacidad_logos_pct / 100.0

espaciado_fotos = st.sidebar.slider("7. Espaciado entre fotos:", 0, 150, 30, 10)

max_fotos_pagina = st.sidebar.slider("8. Máximo de fotos por página:", 4, 20, 10, 2)

st.sidebar.write("---")

# --- VISTA PREVIA INDIVIDUAL ---
st.sidebar.write("👀 **Vista previa de la fuente:**")
try:
    preview_img = Image.new('RGB', (600, 200), color_fondo_rgb)
    draw_preview = ImageDraw.Draw(preview_img)
    fuente_preview = obtener_fuente(opcion_fuente, 70)
    
    if formato_texto == "MAYÚSCULAS":
        texto_test = "PREVIEW'S"
    else:
        texto_test = "Preview's"
    
    draw_preview.text((300, 100), texto_test, fill=color_texto_rgb, font=fuente_preview, anchor="mm")
    st.sidebar.image(preview_img, use_container_width=True)
except Exception:
    st.sidebar.write("Sube una fuente para ver la vista previa.")

st.sidebar.write("---")

# --- PANEL PRINCIPAL ---
st.title("🗂️ DUB x stfu | Collage Creator")
st.write("Generador automatizado de presentaciones de colección en formato A3.")

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
        with st.spinner('Procesando colecciones y dividiendo páginas...'):
            
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
                        texto_marca_base = texto_base_limpio.upper()
                    else:
                        texto_marca_base = texto_base_limpio.title()
                        texto_marca_base = texto_marca_base.replace("Mcc", "McC")
                        texto_marca_base = re.sub(r"\'([A-Z])\b", lambda m: "'" + m.group(1).lower(), texto_marca_base)

                    archivos_totales = [f for f in os.listdir(ruta_desfile) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif'))]
                    archivos_totales.sort()
                    
                    chunks_fotos = [archivos_totales[i:i + max_fotos_pagina] for i in range(0, len(archivos_totales), max_fotos_pagina)]
                    
                    for index_pagina, chunk_archivos in enumerate(chunks_fotos):
                        num_imagenes = len(chunk_archivos)
                        
                        lienzo = Image.new('RGB', (A3_WIDTH, A3_HEIGHT), color_fondo_rgb)
                        
                        # ZONA CABECERA: LOGOS TRANSLÚCIDOS
                        altura_logos = 250
                        ancho_reserva_izq = 0
                        ancho_reserva_der = 0
                        
                        try:
                            if os.path.exists('dub.png'):
                                logo_dub = Image.open('dub.png').convert("RGBA")
                                proporcion = altura_logos / float(logo_dub.height)
                                nuevo_ancho = int(float(logo_dub.width) * float(proporcion))
                                logo_dub = logo_dub.resize((nuevo_ancho, altura_logos), Image.Resampling.LANCZOS)
                                logo_dub = aplicar_opacidad(logo_dub, opacidad_factor)
                                lienzo.paste(logo_dub, (MARGIN_EXTERIOR, MARGIN_EXTERIOR), logo_dub)
                                ancho_reserva_izq = nuevo_ancho
                        except Exception:
                            pass

                        try:
                            if os.path.exists('stfu.png'):
                                logo_stfu = Image.open('stfu.png').convert("RGBA")
                                proporcion = altura_logos / float(logo_stfu.height)
                                nuevo_ancho = int(float(logo_stfu.width) * float(proporcion))
                                logo_stfu = logo_stfu.resize((nuevo_ancho, altura_logos), Image.Resampling.LANCZOS)
                                logo_stfu = aplicar_opacidad(logo_stfu, opacidad_factor)
                                x_stfu = A3_WIDTH - MARGIN_EXTERIOR - nuevo_ancho
                                lienzo.paste(logo_stfu, (x_stfu, MARGIN_EXTERIOR), logo_stfu)
                                ancho_reserva_der = nuevo_ancho
                        except Exception:
                            pass

                        # ZONA CABECERA: TÍTULO
                        draw = ImageDraw.Draw(lienzo)
                        current_tamanio = tamanio_fuente_inicial
                        fuente = obtener_fuente(opcion_fuente, current_tamanio)
                        
                        reserva_maxima = max(ancho_reserva_izq, ancho_reserva_der)
                        max_text_width = A3_WIDTH - (MARGIN_EXTERIOR * 2) - (reserva_maxima * 2) - 300

                        texto_marca_pagina = texto_marca_base
                        if len(chunks_fotos) > 1:
                            texto_marca_pagina = f"{texto_marca_base} Pt. {index_pagina + 1}"

                        try:
                            bbox = draw.textbbox((0, 0), texto_marca_pagina, font=fuente)
                            text_w = bbox[2] - bbox[0]
                            
                            while text_w > max_text_width and current_tamanio > 100:
                                current_tamanio -= 20
                                fuente = obtener_fuente(opcion_fuente, current_tamanio)
                                bbox = draw.textbbox((0, 0), texto_marca_pagina, font=fuente)
                                text_w = bbox[2] - bbox[0]

                            centro_x = A3_WIDTH // 2
                            centro_y = MARGIN_EXTERIOR + (altura_logos // 2)
                            draw.text((centro_x, centro_y), texto_marca_pagina, fill=color_texto_rgb, font=fuente, anchor="mm")
                        except Exception:
                            draw.text((A3_WIDTH // 2, MARGIN_EXTERIOR + 100), texto_marca_pagina, fill=color_texto_rgb, font=fuente, anchor="mm")

                        # ZONA GRID: FOTOS Y CENTRADO DE FILA INFERIOR
                        filas = 2
                        columnas = max(1, (num_imagenes + 1) // 2)
                        
                        start_y_grid = MARGIN_EXTERIOR + HEADER_HEIGHT
                        alto_disponible = A3_HEIGHT - start_y_grid - MARGIN_EXTERIOR
                        
                        espacio_x = (A3_WIDTH - (2 * MARGIN_EXTERIOR) - ((columnas - 1) * espaciado_fotos)) // columnas
                        espacio_y = (alto_disponible - ((filas - 1) * espaciado_fotos)) // filas

                        ancho_maximo_permitido = int(espacio_y * 0.75) 
                        ancho_foto = min(espacio_x, ancho_maximo_permitido)

                        for idx, archivo in enumerate(chunk_archivos):
                            ruta_img = os.path.join(ruta_desfile, archivo)
                            try:
                                with Image.open(ruta_img) as img:
                                    img_recortada = ImageOps.fit(img, (ancho_foto, espacio_y), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

                                    fila_actual = idx // columnas
                                    col_actual = idx % columnas

                                    # --- LÓGICA DE CENTRADO DINÁMICO ---
                                    # Averiguamos cuántos elementos tiene la fila en la que estamos
                                    if fila_actual == 0:
                                        items_en_esta_fila = min(num_imagenes, columnas)
                                    else:
                                        items_en_esta_fila = num_imagenes - columnas
                                    
                                    # Calculamos el espacio total del grid y el que ocupa nuestra fila
                                    ancho_total_grid = (columnas * espacio_x) + ((columnas - 1) * espaciado_fotos)
                                    ancho_fila_actual = (items_en_esta_fila * espacio_x) + (max(0, items_en_esta_fila - 1) * espaciado_fotos)
                                    
                                    # Dividimos el espacio sobrante a la mitad para empujar las fotos hacia el centro
                                    offset_x_fila = (ancho_total_grid - ancho_fila_actual) // 2

                                    # Aplicamos el offset
                                    x_columna = MARGIN_EXTERIOR + offset_x_fila + col_actual * (espacio_x + espaciado_fotos)
                                    x = x_columna + (espacio_x - ancho_foto) // 2 
                                    y = start_y_grid + fila_actual * (espacio_y + espaciado_fotos)

                                    lienzo.paste(img_recortada, (x, y))
                                    del img_recortada
                            except Exception:
                                pass

                        if len(chunks_fotos) > 1:
                            nombre_archivo_salida = f"A3_{nombre_carpeta}_Pt_{index_pagina + 1}.jpg"
                        else:
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
