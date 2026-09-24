import base64
import datetime
import json
import requests
import streamlit as st

# Configuración de la página web (adaptable a celulares)
st.set_page_config(
    page_title="Control de Avances de Obra", page_icon="🏗️", layout="centered"
)

# --- CONFIGURACIÓN DE GITHUB ---
try:
  GITHUB_TOKEN = st.secrets["github_token"]
  GITHUB_REPO = st.secrets["github_repo"]  # Ejemplo: "tu_usuario/tu_repositorio"
except Exception as e:
  st.error(
      "Faltan configurar los secretos de GitHub en Streamlit. Revisa la"
      " sección Secrets."
  )
  GITHUB_TOKEN = ""
  GITHUB_REPO = ""

HEADERS_GH = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "vnd.github.v3+json",
}

# Listas de campos
column_1_actividades = [
    "Cimentación",
    "PB Cadenas",
    "PB Escalera",
    "PB Losa",
    "PB Bloqueo",
    "PB Albañilerías",
    "PB Aplanados",
    "PB Losetas",
    "PB Inst. Obra Negra",
    "PB Muretes",
    "PB Inst. Finales",
    "P1 Cadenas",
    "P1 Losa",
    "P1 Bloqueo",
    "P1 Albañilería",
    "P1 Aplanados",
    "P1 Losetas",
    "P1 Inst. Negra",
    "P1 Inst. Finales",
    "Pretil",
    "Calcreto",
    "Bases Tinaco",
    "Impermeabilizante",
    "Tinacos",
    "Pintura",
    "Puertas",
    "Ventanas",
    "Muebles Baño",
    "Gas",
    "Complem2",
    "Complem3",
    "Complem4",
]

column_2_dias = [
    "Jueves",
    "Viernes",
    "Sabado",
    "Domingo",
    "Lunes",
    "Martes",
    "Miercoles",
]

todos_los_campos = column_1_actividades + column_2_dias


def leer_archivo_github(nombre_archivo):
  """Lee el contenido y el SHA de un archivo .txt desde GitHub."""
  if not GITHUB_TOKEN or not GITHUB_REPO:
    return "", None
  url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/AP_OBRAS/{nombre_archivo}"
  response = requests.get(url, headers=HEADERS_GH)
  if response.status_code == 200:
    data = response.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]
  return "", None


def guardar_archivo_github(nombre_archivo, contenido_texto, sha=None):
  """Guarda o actualiza un archivo .txt en GitHub haciendo un commit automático."""
  if not GITHUB_TOKEN or not GITHUB_REPO:
    return False
  url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/AP_OBRAS/{nombre_archivo}"
  content_encoded = base64.b64encode(contenido_texto.encode("utf-8")).decode(
      "utf-8"
  )
  data = {
      "message": f"Actualización de avances: {nombre_archivo}",
      "content": content_encoded,
  }
  if sha:
    data["sha"] = sha
  response = requests.put(url, headers=HEADERS_GH, json=data)
  return response.status_code in [200, 201]


def obtener_lista_residentes_github():
  """Escanea los archivos en la carpeta AP_OBRAS de GitHub para detectar residentes."""
  residentes_encontrados = {}
  if not GITHUB_TOKEN or not GITHUB_REPO:
    return {
        "Ing. Marcos": [f"ED{i}" for i in range(4, 9)],
        "Ing. Raúl": ["ED10", "ED21", "ED22"],
        "Ing. Abdiel": ["ED1", "ED2"],
    }

  url = (
      f"https://api.github.com/repos/{GITHUB_REPO}/contents/AP_OBRAS"
  )
  response = requests.get(url, headers=HEADERS_GH)
  if response.status_code == 200:
    for archivo in response.json():
      nombre_archivo = archivo["name"]
      if nombre_archivo.startswith("avances_obra_captura_") and nombre_archivo.endswith(".txt"):
        contenido, _ = leer_archivo_github(nombre_archivo)
        edificios_del_txt = set()
        nombre_residente_detectado = None

        for linea in contenido.splitlines():
          partes = linea.strip().split(",")
          if len(partes) >= 3:
            if not nombre_residente_detectado and partes[1].strip():
              nombre_residente_detectado = partes[1].strip()
            if partes[2].strip():
              edificios_del_txt.add(partes[2].strip())

        if not nombre_residente_detectado:
          nombre_bruto = (
              nombre_archivo.replace("avances_obra_captura_", "")
              .replace(".txt", "")
          )
          nombre_residente_detectado = nombre_bruto.replace("_", " ")
          if nombre_residente_detectado.lower().startswith("ing "):
            nombre_residente_detectado = "Ing. " + nombre_residente_detectado[4:]

        if not edificios_del_txt:
          edificios_del_txt = {f"ED{i}" for i in range(4, 9)}

        residentes_encontrados[nombre_residente_detectado] = sorted(
            list(edificios_del_txt)
        )

  if not residentes_encontrados:
    residentes_encontrados = {
        "Ing. Marcos": [f"ED{i}" for i in range(4, 9)],
        "Ing. Raúl": ["ED10", "ED21", "ED22"],
        "Ing. Abdiel": ["ED1", "ED2"],
    }

  return residentes_encontrados


config_actual = {"residentes": obtener_lista_residentes_github()}
LISTA_RESIDENTES = list(config_actual["residentes"].keys())

# --- INTERFAZ DE USUARIO ---
st.title("🏗️ Control de Avances de Obra")

col_res1, col_res2, col_res3, col_res4 = st.columns([2.5, 1, 1, 1])

with col_res1:
  nombre_residente_actual = st.selectbox("👷 Residente", LISTA_RESIDENTES)
with col_res2:
  st.write("")
  st.write("")
  btn_ajustar = st.button("⚙️ Ajustar")
with col_res3:
  st.write("")
  st.write("")
  btn_nuevo = st.button("➕ Nuevo")
with col_res4:
  st.write("")
  st.write("")
  btn_eliminar = st.button("🗑️ Borrar", type="primary")

nombre_limpio = (
    nombre_residente_actual.replace(" ", "_").replace(".", "")
)
nombre_archivo_txt = f"avances_obra_captura_{nombre_limpio}.txt"
EDIFICIOS_DISPONIBLES = config_actual["residentes"].get(
    nombre_residente_actual, []
)

# --- MODALES / PANELES ---
if btn_nuevo:
  st.session_state.panel_activo = "nuevo"
elif btn_ajustar:
  st.session_state.panel_activo = "ajustar"
elif btn_eliminar:
  st.session_state.panel_activo = "eliminar"

if "panel_activo" not in st.session_state:
  st.session_state.panel_activo = None

if st.session_state.panel_activo == "nuevo":
  with st.expander("➕ Dar de Alta a Nuevo Ingeniero", expanded=True):
    nuevo_ing_txt = st.text_input("Nombre completo del nuevo ingeniero")
    edis_nuevos_txt = st.text_input(
        "Edificios iniciales asignados (separados por comas)", value="ED1, ED2"
    )
    col_n1, col_n2 = st.columns(2)
    with col_n1:
      if st.button("Guardar Nuevo Ingeniero", use_container_width=True):
        nombre_ing_limpio = nuevo_ing_txt.strip()
        if nombre_ing_limpio:
          if nombre_ing_limpio not in config_actual["residentes"]:
            lista_edis_ini = [
                e.strip() for e in edis_nuevos_txt.split(",") if e.strip()
            ]
            
            # Crear archivo .txt inicial en GitHub para el nuevo residente
            nombre_limpio_archivo = nombre_ing_limpio.replace(" ", "_").replace(".", "")
            nombre_archivo_nuevo = f"avances_obra_captura_{nombre_limpio_archivo}.txt"
            
            fecha_hoy_str = datetime.date.today().strftime("%d/%m/%Y")
            primer_edi = lista_edis_ini[0] if lista_edis_ini else "ED1"
            ceros_iniciales = ",".join(["0"] * len(todos_los_campos))
            contenido_inicial = f"{fecha_hoy_str},{nombre_ing_limpio},{primer_edi},{ceros_iniciales}\n"
            
            exito_creacion = guardar_archivo_github(nombre_archivo_nuevo, contenido_inicial)
            
            if exito_creacion:
              config_actual["residentes"][nombre_ing_limpio] = lista_edis_ini
              st.success(f"Ingeniero '{nombre_ing_limpio}' agregado y guardado en GitHub con éxito.")
              st.session_state.panel_activo = None
              st.rerun()
            else:
              st.error("No se pudo crear el archivo del ingeniero en GitHub. Revisa tu token.")
          else:
            st.warning("Este ingeniero ya está registrado.")
        else:
          st.error("Escribe un nombre válido.")
    with col_n2:
      if st.button("Cancelar", use_container_width=True, key="cancel_nuevo"):
        st.session_state.panel_activo = None
        st.rerun()

elif st.session_state.panel_activo == "ajustar":
  with st.expander(
      f"⚙️ Ajustar datos de: {nombre_residente_actual}", expanded=True
  ):
    nuevo_nombre_ing = st.text_input(
        "Modificar nombre del ingeniero", value=nombre_residente_actual
    )
    edificios_actuales_str = ", ".join(EDIFICIOS_DISPONIBLES)
    nuevos_edis_str = st.text_area(
        "Edificios asignados (separados por comas)",
        value=edificios_actuales_str,
    )
    col_a1, col_a2 = st.columns(2)
    with col_a1:
      if st.button("Guardar Cambios", use_container_width=True):
        target_name = nombre_residente_actual
        if (
            nuevo_nombre_ing.strip()
            and nuevo_nombre_ing != nombre_residente_actual
        ):
          target_name = nuevo_nombre_ing.strip()
          config_actual["residentes"][target_name] = config_actual["residentes"
          ].pop(nombre_residente_actual)
        lista_edis = [e.strip() for e in nuevos_edis_str.split(",") if e.strip()]
        config_actual["residentes"][target_name] = lista_edis
        st.success("¡Cambios guardados con éxito!")
        st.session_state.panel_activo = None
        st.rerun()
    with col_a2:
      if st.button("Cancelar", use_container_width=True, key="cancel_ajustar"):
        st.session_state.panel_activo = None
        st.rerun()

elif st.session_state.panel_activo == "eliminar":
  with st.expander(f"🗑️ Eliminar a: {nombre_residente_actual}", expanded=True):
    st.warning(f"¿Estás seguro de eliminar a **{nombre_residente_actual}**?")
    col_del1, col_del2 = st.columns(2)
    with col_del1:
      if st.button("Sí, Eliminar Definitivamente", use_container_width=True):
        if len(config_actual["residentes"]) > 1:
          config_actual["residentes"].pop(nombre_residente_actual)
          st.success(f"Ingeniero '{nombre_residente_actual}' eliminado.")
          st.session_state.panel_activo = None
          st.rerun()
        else:
          st.error("No puedes eliminar al único residente activo.")
    with col_del2:
      if st.button(
          "Cancelar", use_container_width=True, key="cancel_eliminar"
      ):
        st.session_state.panel_activo = None
        st.rerun()

st.divider()

# --- CARGA DE DATOS DESDE GITHUB ---
if (
    "residente_actual_memoria" not in st.session_state
    or st.session_state.residente_actual_memoria != nombre_residente_actual
):
  st.session_state.residente_actual_memoria = nombre_residente_actual
  st.session_state.base_datos = {}
  contenido_txt, sha_archivo = leer_archivo_github(nombre_archivo_txt)
  if contenido_txt:
    try:
      for linea in contenido_txt.splitlines():
        partes = linea.strip().split(",")
        if len(partes) >= 3:
          fec, res, edi = partes[0], partes[1], partes[2]
          valores = partes[3:]
          if fec not in st.session_state.base_datos:
            st.session_state.base_datos[fec] = {}
          d_temp = {}
          for i, campo in enumerate(todos_los_campos):
            val = valores[i] if i < len(valores) else "0"
            if campo in column_1_actividades and val == "1":
              val = "100"
            d_temp[campo] = val
          st.session_state.base_datos[fec][edi] = d_temp
    except Exception as e:
      st.error(f"Error al procesar datos: {e}")

if "selected_date" not in st.session_state:
  st.session_state.selected_date = datetime.date.today()


def obtener_valor_anterior(edi, campo, fecha_actual_str):
  try:
    f_actual = datetime.datetime.strptime(fecha_actual_str, "%d/%m/%Y").date()
  except:
    return "0"

  mejor_fecha = None
  for fec_str in st.session_state.base_datos.keys():
    if edi in st.session_state.base_datos[fec_str]:
      try:
        f_reg = datetime.datetime.strptime(fec_str, "%d/%m/%Y").date()
        if f_reg < f_actual:
          if mejor_fecha is None or f_reg > mejor_fecha:
            mejor_fecha = f_reg
      except:
        continue
  if mejor_fecha:
    mejor_fecha_str = mejor_fecha.strftime("%d/%m/%Y")
    val = st.session_state.base_datos[mejor_fecha_str][edi].get(campo, "0")
    if val == "1":
      return "100"
    return val
  return "0"


def verificar_si_ya_llego_a_100_en_pasado(edi, campo, fecha_actual_str):
  try:
    f_actual = datetime.datetime.strptime(fecha_actual_str, "%d/%m/%Y").date()
  except:
    return False

  for fec_str, edificios in st.session_state.base_datos.items():
    if edi in edificios:
      try:
        f_reg = datetime.datetime.strptime(fec_str, "%d/%m/%Y").date()
        if f_reg < f_actual:
          v_ant = edificios[edi].get(campo, "0")
          if v_ant == "1" or (
              v_ant.replace(".", "", 1).isdigit() and float(v_ant) >= 100
          ):
            return True
      except:
        continue
  return False


def navegar_fechas(direccion):
  fechas_registradas = sorted(
      st.session_state.base_datos.keys(),
      key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y").date(),
  )
  if not fechas_registradas:
    return

  fechas_dt = [
      datetime.datetime.strptime(f, "%d/%m/%Y").date()
      for f in fechas_registradas
  ]
  f_actual = st.session_state.selected_date

  idx = -1
  for i, f_reg in enumerate(fechas_dt):
    if f_reg == f_actual:
      idx = i
      break
    elif f_reg > f_actual:
      idx = i - 1 if direccion < 0 else i
      break
  else:
    if f_actual > fechas_dt[-1]:
      idx = len(fechas_dt) - 1
    else:
      idx = 0

  nuevo_idx = idx + direccion
  if 0 <= nuevo_idx < len(fechas_dt):
    st.session_state.selected_date = fechas_dt[nuevo_idx]


# --- CONTROLES DE FECHA Y EDIFICIO ---
col_nav1, col_nav2, col_nav3, col_edi = st.columns([1.2, 2.2, 1.2, 3])

with col_nav1:
  if st.button("<< Anterior", use_container_width=True):
    navegar_fechas(-1)
    st.rerun()

with col_nav2:
  fecha_seleccionada = st.date_input(
      "Fecha",
      value=st.session_state.selected_date,
      label_visibility="collapsed",
  )
  if fecha_seleccionada != st.session_state.selected_date:
    st.session_state.selected_date = fecha_seleccionada

with col_nav3:
  if st.button("Siguiente >>", use_container_width=True):
    navegar_fechas(1)
    st.rerun()

fec_str = st.session_state.selected_date.strftime("%d/%m/%Y")

with col_edi:
  if EDIFICIOS_DISPONIBLES:
    edi_actual = st.selectbox("Seleccione el Edificio", EDIFICIOS_DISPONIBLES)
  else:
    st.warning("Este ing. no tiene edificios asignados.")
    edi_actual = "Sin Edificio"

if edi_actual != "Sin Edificio":
  if fec_str not in st.session_state.base_datos:
    st.session_state.base_datos[fec_str] = {}
  if edi_actual not in st.session_state.base_datos[fec_str]:
    st.session_state.base_datos[fec_str][edi_actual] = {
        campo: "0" for campo in todos_los_campos
    }

  st.subheader(f"Capturando: {edi_actual} — Fecha: {fec_str}")

  col_c1, col_c2 = st.columns(2)
  valores_actuales = st.session_state.base_datos[fec_str][edi_actual]
  nuevos_valores = {}

  with col_c1:
    st.markdown("### Actividades de Obra")
    for campo in column_1_actividades:
      val_ant = obtener_valor_anterior(edi_actual, campo, fec_str)
      bloqueado = verificar_si_ya_llego_a_100_en_pasado(
          edi_actual, campo, fec_str
      )

      val_actual = "100" if bloqueado else valores_actuales.get(campo, "0")
      if val_actual == "1":
        val_actual = "100"

      subcol1, subcol2 = st.columns([3, 2])
      with subcol1:
        st.markdown(
            f"<div style='font-size: 13px; margin-bottom: 5px;'>"
            f"<strong>{campo}</strong><br>"
            f"<span style='color: #2ecc71; font-weight: bold; font-size:"
            f" 13px;'>Ant:</span> "
            f"<span style='color: white; font-weight: bold; font-size:"
            f" 14px;'>{val_ant}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
      with subcol2:
        if bloqueado:
          nuevos_valores[campo] = st.text_input(
              f"val_{campo}",
              value="100",
              disabled=True,
              label_visibility="collapsed",
          )
        else:
          nuevos_valores[campo] = st.text_input(
              f"val_{campo}", value=val_actual, label_visibility="collapsed"
          )

  with col_c2:
    st.markdown("### Días de la Semana")
    for campo in column_2_dias:
      val_actual = valores_actuales.get(campo, "0")
      st.markdown(f"**{campo}**")
      nuevos_valores[campo] = st.text_input(
          f"val_{campo}", value=val_actual, label_visibility="collapsed"
      )

  st.session_state.base_datos[fec_str][edi_actual] = nuevos_valores

st.divider()

# --- BOTONES DE ACCIÓN (GUARDAR EN GITHUB) ---
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
  if (
      st.button("💾 Guardar Edificio", type="primary", use_container_width=True)
      and edi_actual != "Sin Edificio"
  ):
    try:
      contenido_actual, sha_actual = leer_archivo_github(nombre_archivo_txt)
      lineas_existentes = contenido_actual.splitlines(keepends=True)

      datos = [fec_str, nombre_residente_actual, edi_actual]
      for campo in todos_los_campos:
        valor_ingresado = (
            st.session_state.base_datos[fec_str][edi_actual][campo].strip()
        )
        if campo in column_1_actividades:
          try:
            num_val = float(valor_ingresado)
            if num_val == 1.0:
              valor_ingresado = "100"
          except ValueError:
            pass
        datos.append(valor_ingresado)

      linea_nueva = ",".join(datos) + "\n"

      nuevas_lineas = []
      encontrado = False
      for l in lineas_existentes:
        partes = l.strip().split(",")
        if len(partes) >= 3 and partes[0] == fec_str and partes[2] == edi_actual:
          nuevas_lineas.append(linea_nueva)
          encontrado = True
        else:
          nuevas_lineas.append(
              l if l.endswith("\n") else l + "\n"
          )
      if not encontrado:
        nuevas_lineas.append(linea_nueva)

      contenido_final = "".join(nuevas_lineas)

      exito = guardar_archivo_github(
          nombre_archivo_txt, contenido_final, sha_actual
      )
      if exito:
        st.success(f"¡Edificio {edi_actual} guardado correctamente en GitHub!")
      else:
        st.error("Error al guardar en GitHub.")
    except Exception as e:
      st.error(f"Error: {e}")

with col_btn2:
  if (
      st.button("🔄 Restablecer a 0", use_container_width=True)
      and edi_actual != "Sin Edificio"
  ):
    for campo in todos_los_campos:
      st.session_state.base_datos[fec_str][edi_actual][campo] = "0"
    st.rerun()

with col_btn3:
  if st.button("📂 Ver Archivo en GitHub", use_container_width=True):
    contenido_txt, _ = leer_archivo_github(nombre_archivo_txt)
    if contenido_txt:
      st.code(contenido_txt)
    else:
      st.info("Aún no hay registros en GitHub para este residente.")