import base64
import datetime
import json
import requests
import streamlit as st

# Configuración de la página web (adaptable a celulares)
st.set_page_config(
    page_title="Control de Avances de Obra", page_icon="🏗️", layout="centered"
)

# --- INYECCIÓN DE CSS PARA AGRANDAR ETIQUETA Y SELECTBOX DE EDIFICIOS ---
st.markdown(
    """
    <style>
        /* Agrandar la etiqueta (label) que está arriba del selectbox de edificios */
        div[data-testid="stSelectbox"] label p {
            font-size: 18px !important;
            font-weight: bold !important;
            color: #ffffff !important;
        }
        /* Agrandar el texto seleccionado dentro de la caja del selectbox de edificios */
        div[data-baseweb="select"] > div {
            font-size: 20px !important;
            font-weight: bold !important;
        }
        /* Ajustar tamaño de texto en la lista desplegable */
        li[role="option"] {
            font-size: 18px !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CONFIGURACIÓN DE CONTRASEÑA DE ADMINISTRADOR ---
PASSWORD_ADMIN = "admin123"


def verificar_password():
  """Muestra un campo para ingresar la contraseña de administrador."""
  pwd = st.text_input(
      "🔑 Contraseña de Administrador:", type="password", key="pwd_input_admin"
  )
  if pwd == PASSWORD_ADMIN:
    return True
  elif pwd != "":
    st.error("Contraseña incorrecta.")
  return False


# --- CONFIGURACIÓN DE GITHUB ---
try:
  GITHUB_TOKEN = st.secrets["github_token"]
  GITHUB_REPO = st.secrets["github_repo"]
except Exception as e:
  st.error(
      "Faltan configurar los secretos de GitHub en Streamlit. Revisa la sección"
      " Secrets."
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
  if not GITHUB_TOKEN or not GITHUB_REPO:
    return False
  url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/AP_OBRAS/{nombre_archivo}"
  content_encoded = base64.b64encode(contenido_texto.encode("utf-8")).decode(
      "utf-8"
  )
  data = {
      "message": f"Actualización de configuración/avances: {nombre_archivo}",
      "content": content_encoded,
  }
  if sha:
    data["sha"] = sha
  response = requests.put(url, headers=HEADERS_GH, json=data)
  return response.status_code in [200, 201]


def eliminar_archivo_github(nombre_archivo):
  if not GITHUB_TOKEN or not GITHUB_REPO:
    return False
  _, sha = leer_archivo_github(nombre_archivo)
  if not sha:
    return True

  url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/AP_OBRAS/{nombre_archivo}"
  headers = HEADERS_GH.copy()
  data = {
      "message": f"Eliminando archivo huérfano por baja de residente: {nombre_archivo}",
      "sha": sha,
  }
  response = requests.delete(url, headers=headers, json=data)
  return response.status_code in [200, 204]


def cargar_configuracion_residentes():
  contenido, sha = leer_archivo_github("config_residentes.json")
  if contenido:
    try:
      return json.loads(contenido), sha
    except:
      pass

  default_config = {
      "Ing. Marcos": [f"ED{i}" for i in range(4, 9)],
      "Ing. Raúl": ["ED10", "ED21", "ED22"],
      "Ing. Abdiel": ["ED1", "ED2"],
  }
  return default_config, None


def guardar_configuracion_residentes(diccionario_residentes):
  _, sha = leer_archivo_github("config_residentes.json")
  contenido_json = json.dumps(
      diccionario_residentes, indent=4, ensure_ascii=False
  )
  return guardar_archivo_github("config_residentes.json", contenido_json, sha)


residentes_guardados, _ = cargar_configuracion_residentes()
if "residentes" not in st.session_state:
  st.session_state.residentes = residentes_guardados

LISTA_RESIDENTES = list(st.session_state.residentes.keys())

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
    nombre_residente_actual.replace(" ", "_")
    .replace(".", "")
    .replace("Â", "")
)
nombre_archivo_txt = f"avances_obra_captura_{nombre_limpio}.txt"
EDIFICIOS_DISPONIBLES = st.session_state.residentes.get(
    nombre_residente_actual, []
)

# --- MODALES / PANELES PROTEGIDOS CON CONTRASEÑA ---
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
    st.info(
        "Se requiere contraseña de administrador para dar de alta un ingeniero."
    )
    if verificar_password():
      nuevo_ing_txt = st.text_input("Nombre completo del ingeniero")
      edis_nuevos_txt = st.text_input(
          "Edificios iniciales asignados (separados por comas)", value="P1, P2, P3"
      )
      col_n1, col_n2 = st.columns(2)
      with col_n1:
        if st.button("Guardar Nuevo Ingeniero", use_container_width=True):
          nombre_ing_limpio = nuevo_ing_txt.strip()
          if nombre_ing_limpio:
            if nombre_ing_limpio not in st.session_state.residentes:
              lista_edis_ini = [
                  e.strip() for e in edis_nuevos_txt.split(",") if e.strip()
              ]
              if not lista_edis_ini:
                lista_edis_ini = ["ED1"]

              st.session_state.residentes[nombre_ing_limpio] = lista_edis_ini
              exito_config = guardar_configuracion_residentes(
                  st.session_state.residentes
              )

              if exito_config:
                st.success(
                    f"Ingeniero '{nombre_ing_limpio}' guardado con éxito."
                )
                st.session_state.panel_activo = None
                st.rerun()
              else:
                st.error("Error al guardar la configuración en GitHub.")
            else:
              st.warning("Este ingeniero ya está registrado.")
          else:
            st.error("Escribe un nombre válido.")
      with col_n2:
        if st.button("Cancelar", use_container_width=True, key="cancel_nuevo"):
          st.session_state.panel_activo = None
          st.rerun()
    else:
      if st.button("Cancelar", key="cancel_pwd_nuevo"):
        st.session_state.panel_activo = None
        st.rerun()

elif st.session_state.panel_activo == "ajustar":
  with st.expander(
      f"⚙️ Ajustar datos de: {nombre_residente_actual}", expanded=True
  ):
    st.info("Se requiere contraseña de administrador para modificar ajustes.")
    if verificar_password():
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
            st.session_state.residentes[target_name] = (
                st.session_state.residentes.pop(nombre_residente_actual)
            )

          lista_edis = [
              e.strip() for e in nuevos_edis_str.split(",") if e.strip()
          ]
          st.session_state.residentes[target_name] = lista_edis

          exito_config = guardar_configuracion_residentes(
              st.session_state.residentes
          )
          if exito_config:
            st.success("¡Cambios y edificios actualizados con éxito!")
            st.session_state.panel_activo = None
            st.rerun()
          else:
            st.error("Error al actualizar la configuración en GitHub.")
      with col_a2:
        if st.button(
            "Cancelar", use_container_width=True, key="cancel_ajustar"
        ):
          st.session_state.panel_activo = None
          st.rerun()
    else:
      if st.button("Cancelar", key="cancel_pwd_ajustar"):
        st.session_state.panel_activo = None
        st.rerun()

elif st.session_state.panel_activo == "eliminar":
  with st.expander(f"🗑️ Eliminar a: {nombre_residente_actual}", expanded=True):
    st.warning(
        f"Se requiere contraseña de administrador para eliminar a"
        f" **{nombre_residente_actual}** y su archivo de registros asociado."
    )
    if verificar_password():
      col_del1, col_del2 = st.columns(2)
      with col_del1:
        if st.button("Sí, Eliminar Definitivamente", use_container_width=True):
          if len(st.session_state.residentes) > 1:
            nombre_limpio_borrar = (
                nombre_residente_actual.replace(" ", "_")
                .replace(".", "")
                .replace("Â", "")
            )
            archivo_txt_a_borrar = (
                f"avances_obra_captura_{nombre_limpio_borrar}.txt"
            )
            eliminar_archivo_github(archivo_txt_a_borrar)

            st.session_state.residentes.pop(nombre_residente_actual)
            guardar_configuracion_residentes(st.session_state.residentes)

            st.success(
                f"Ingeniero '{nombre_residente_actual}' y su archivo de"
                " registros fueron eliminados correctamente."
            )
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
    else:
      if st.button("Cancelar", key="cancel_pwd_eliminar"):
        st.session_state.panel_activo = None
        st.rerun()

st.divider()

# --- CARGA DE DATOS DE AVANCES DESDE GITHUB ---
if (
    "residente_actual_memoria" not in st.session_state
    or st.session_state.residente_actual_memoria != nombre_residente_actual
):
  st.session_state.residente_actual_memoria = nombre_residente_actual
  st.session_state.base_datos = {}
  contenido_txt, _ = leer_archivo_github(nombre_archivo_txt)
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

          obs_val = (
              valores[len(todos_los_campos)]
              if len(valores) > len(todos_los_campos)
              else ""
          )

          st.session_state.base_datos[fec][edi] = {
              "valores": d_temp,
              "observaciones": obs_val,
          }
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
    val = (
        st.session_state.base_datos[mejor_fecha_str][edi]["valores"]
        .get(campo, "0")
    )
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
          v_ant = edificios[edi]["valores"].get(campo, "0")
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


# --- CONTROLES DE FECHA Y EDIFICIO (REORGANIZADOS) ---
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

  if st.button(
      "🗑️ Borrar Fecha Actual", use_container_width=True, key="btn_borrar_fecha"
  ):
    st.session_state.panel_borrar_fecha = True

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

# --- PANEL DE CONFIRMACIÓN PARA BORRAR FECHA ACTUAL ---
if st.session_state.get("panel_borrar_fecha", False):
  st.warning(
      f"¿Eliminar todos los registros del edificio '{edi_actual}' en la fecha"
      f" {fec_str}?"
  )
  st.info(
      "Se requiere contraseña de administrador para eliminar registros de una"
      " fecha."
  )
  if verificar_password():
    if st.button("Confirmar Borrado de Fecha"):
      try:
        contenido_actual, sha_actual = leer_archivo_github(nombre_archivo_txt)
        lineas_existentes = contenido_actual.splitlines(keepends=True)
        nuevas_lineas = []
        for l in lineas_existentes:
          partes = l.strip().split(",")
          if len(partes) >= 3 and partes[0] == fec_str and partes[2] == edi_actual:
            continue
          nuevas_lineas.append(l if l.endswith("\n") else l + "\n")

        contenido_final = "".join(nuevas_lineas)
        exito = guardar_archivo_github(
            nombre_archivo_txt, contenido_final, sha_actual
        )
        if exito:
          if fec_str in st.session_state.base_datos and edi_actual in st.session_state.base_datos[fec_str]:
            del st.session_state.base_datos[fec_str][edi_actual]
          st.success("¡Registros de esta fecha eliminados correctamente!")
          st.session_state.panel_borrar_fecha = False
          st.rerun()
        else:
          st.error("Error al actualizar en GitHub.")
      except Exception as e:
        st.error(f"Error: {e}")
  if st.button("Cancelar Borrado Fecha"):
    st.session_state.panel_borrar_fecha = False
    st.rerun()

if edi_actual != "Sin Edificio":
  if fec_str not in st.session_state.base_datos:
    st.session_state.base_datos[fec_str] = {}
  if edi_actual not in st.session_state.base_datos[fec_str]:
    st.session_state.base_datos[fec_str][edi_actual] = {
        "valores": {campo: "0" for campo in todos_los_campos},
        "observaciones": "",
    }

  st.subheader(f"Capturando: {edi_actual} — Fecha: {fec_str}")

  col_c1, col_c2 = st.columns(2)
  registro_actual = st.session_state.base_datos[fec_str][edi_actual]
  valores_actuales = registro_actual["valores"]
  nuevos_valores = {}

  with col_c1:
    st.markdown("### Actividades de Obra")
    for campo in column_1_actividades:
      val_ant = obtener_valor_anterior(edi_actual, campo, fec_str)
      if val_ant == "0":
        val_ant = ""

      bloqueado = verificar_si_ya_llego_a_100_en_pasado(
          edi_actual, campo, fec_str
      )

      val_actual = "100" if bloqueado else valores_actuales.get(campo, "0")
      if val_actual == "1":
        val_actual = "100"

      val_input_display = "" if val_actual == "0" else val_actual

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
          captura_ingresada = st.text_input(
              f"val_{campo}",
              value="100",
              disabled=True,
              label_visibility="collapsed",
          )
        else:
          captura_ingresada = st.text_input(
              f"val_{campo}",
              value=val_input_display,
              label_visibility="collapsed",
          )

        nuevos_valores[campo] = (
            "0" if captura_ingresada.strip() == "" else captura_ingresada.strip()
        )

  with col_c2:
    st.markdown("### Días de la Semana")
    for campo in column_2_dias:
      val_actual = valores_actuales.get(campo, "0")
      val_input_display = "" if val_actual == "0" else val_actual

      st.markdown(f"**{campo}**")
      captura_ingresada = st.text_input(
          f"val_{campo}", value=val_input_display, label_visibility="collapsed"
      )
      nuevos_valores[campo] = (
          "0" if captura_ingresada.strip() == "" else captura_ingresada.strip()
      )

    # --- CAMPO DE OBSERVACIONES ---
    st.markdown("### 📝 Observaciones")
    obs_actual = registro_actual.get("observaciones", "")
    nuevas_observaciones = st.text_area(
        "Escribe las observaciones generales:",
        value=obs_actual,
        height=180,
        label_visibility="collapsed",
    )
    st.session_state.base_datos[fec_str][edi_actual][
        "observaciones"
    ] = nuevas_observaciones

  st.session_state.base_datos[fec_str][edi_actual]["valores"] = nuevos_valores

st.divider()

# --- BOTONES DE ACCIÓN (GUARDAR EN GITHUB) ---
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
  if (
      st.button(
          "💾 Guardar Edificio", type="primary", use_container_width=True
      )
      and edi_actual != "Sin Edificio"
  ):
    try:
      contenido_actual, sha_actual = leer_archivo_github(nombre_archivo_txt)
      lineas_existentes = contenido_actual.splitlines(keepends=True)

      datos = [fec_str, nombre_residente_actual, edi_actual]
      for campo in todos_los_campos:
        valor_ingresado = (
            st.session_state.base_datos[fec_str][edi_actual]["valores"][campo]
            .strip()
        )
        if campo in column_1_actividades:
          try:
            if float(valor_ingresado) == 1.0:
              valor_ingresado = "100"
          except ValueError:
            pass
        datos.append(valor_ingresado)

      obs_a_guardar = (
          st.session_state.base_datos[fec_str][edi_actual]
          .get("observaciones", "")
          .replace("\n", " ")
      )
      datos.append(obs_a_guardar)

      linea_nueva = ",".join(datos) + "\n"

      nuevas_lineas = []
      encontrado = False
      for l in lineas_existentes:
        partes = l.strip().split(",")
        if len(partes) >= 3 and partes[0] == fec_str and partes[2] == edi_actual:
          nuevas_lineas.append(linea_nueva)
          encontrado = True
        else:
          nuevas_lineas.append(l if l.endswith("\n") else l + "\n")
      if not encontrado:
        nuevas_lineas.append(linea_nueva)

      contenido_final = "".join(nuevas_lineas)
      exito = guardar_archivo_github(
          nombre_archivo_txt, contenido_final, sha_actual
      )
      if exito:
        st.success(
            f"¡Edificio {edi_actual} y observaciones guardados correctamente en"
            " GitHub!"
        )
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
      st.session_state.base_datos[fec_str][edi_actual]["valores"][campo] = "0"
    st.session_state.base_datos[fec_str][edi_actual]["observaciones"] = ""
    st.rerun()

with col_btn3:
  if st.button("📂 Ver Archivo en GitHub", use_container_width=True):
    contenido_txt, _ = leer_archivo_github(nombre_archivo_txt)
    if contenido_txt:
      st.code(contenido_txt)
    else:
      st.info("Aún no hay registros de avances en GitHub para este residente.")