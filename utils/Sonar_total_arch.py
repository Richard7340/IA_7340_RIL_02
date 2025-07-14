import psutil
import platform
import socket
import os
import datetime
import time
import shutil
import getpass
import subprocess
import sys
import pkg_resources
import importlib.util
import locale
import json
import winreg

try:
    import GPUtil
    gpu_available = True
except ImportError:
    gpu_available = False
    print("Sonar_total_arch: GPUtil no disponible, GPU no será detectada")

try:
    from screeninfo import get_monitors
    screeninfo_available = True
except ImportError:
    screeninfo_available = False
    print("Sonar_total_arch: screeninfo no disponible, pantallas no serán detectadas")

class SonarTotal:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.reporte = {}

    def info_sistema(self):
        print("Sonar_total_arch: Recolectando info_sistema")
        try:
            info = {
                "timestamp": self.timestamp,
                "usuario": self.username,
                "host": self.hostname,
                "sistema_operativo": f"{platform.system()} {platform.release()} ({platform.version()})",
                "arquitectura": platform.machine(),
                "procesador": platform.processor(),
                "ruta_sistema": os.environ.get('SystemRoot', 'Desconocido'),
                "directorio_actual": os.getcwd(),
                "version_python": f"{platform.python_version()} ({sys.executable})",
                "locale": locale.getdefaultlocale(),
                "variables_entorno": dict(os.environ)
            }
            self.reporte['sistema'] = info
            print("=== INFORMACIÓN DEL SISTEMA ===")
            for k, v in info.items():
                if k == "variables_entorno":
                    print("\nVariables de entorno:")
                    for key, value in v.items():
                        print(f"  {key} = {value}")
                else:
                    print(f"{k.replace('_', ' ').title()}: {v}")
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_sistema: {str(e)}")

    def info_hardware(self):
        print("Sonar_total_arch: Recolectando info_hardware")
        try:
            info = {
                "cpu_logicos": psutil.cpu_count(logical=True),
                "cpu_fisicos": psutil.cpu_count(logical=False),
                "cpu_frecuencia": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "discos": [],
                "gpus": [],
                "cuda_version": None
            }

            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    info["discos"].append({"dispositivo": part.device, "montaje": part.mountpoint, "total_gb": round(usage.total / (1024 ** 3), 2)})
                except Exception as e:
                    print(f"Sonar_total_arch: Error en disco {part.device}: {str(e)}")
                    continue

            if gpu_available:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    info["gpus"].append({"nombre": gpu.name, "memoria_mb": gpu.memoryTotal, "uso_%": round(gpu.load * 100, 1)})

            try:
                result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    info["cuda_version"] = result.stdout.strip()
            except FileNotFoundError:
                print("Sonar_total_arch: nvcc no encontrado")

            self.reporte['hardware'] = info
            print("=== HARDWARE ===")
            print(f"Núcleos (lógicos): {info['cpu_logicos']}")
            print(f"Núcleos (físicos): {info['cpu_fisicos']}")
            print(f"Frecuencia CPU: {info['cpu_frecuencia']:.2f} MHz" if info['cpu_frecuencia'] else "Frecuencia CPU: No disponible")
            print(f"RAM Total: {info['ram_gb']} GB")
            print("\nEspacio en disco:")
            for d in info['discos']:
                print(f" - {d['dispositivo']} ({d['montaje']}): {d['total_gb']} GB totales")
            print("\nGPU:")
            if info['gpus']:
                for g in info['gpus']:
                    print(f" - {g['nombre']} | Memoria: {g['memoria_mb']}MB | Utilización: {g['uso_%']}%")
            else:
                print("No se detecta uso activo de GPU.")
            print("\nVersión de CUDA:")
            print(info['cuda_version'] or "CUDA no está instalada o nvcc no está en el PATH.")
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_hardware: {str(e)}")

    def info_pantallas(self):
        print("Sonar_total_arch: Recolectando info_pantallas")
        try:
            pantallas = []
            if screeninfo_available:
                for monitor in get_monitors():
                    descripcion = f"{monitor.width}x{monitor.height} (posición: {monitor.x},{monitor.y})"
                    print(f"- {monitor.name}: {descripcion}")
                    pantallas.append({"nombre": monitor.name, "ancho": monitor.width, "alto": monitor.height, "pos_x": monitor.x, "pos_y": monitor.y})
            else:
                print("Sonar_total_arch: screeninfo no está disponible")
            self.reporte['pantallas'] = pantallas
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_pantallas: {str(e)}")

    def info_frameworks_ia(self):
        print("Sonar_total_arch: Recolectando info_frameworks_ia")
        try:
            frameworks = [
                ("torch", "PyTorch"),
                ("tensorflow", "TensorFlow"),
                ("transformers", "Transformers (HuggingFace)"),
                ("onnx", "ONNX"),
                ("xgboost", "XGBoost"),
                ("sklearn", "Scikit-learn"),
                ("lightgbm", "LightGBM"),
            ]
            estados = {}
            for pkg, name in frameworks:
                spec = importlib.util.find_spec(pkg)
                status = "Instalado" if spec else "No encontrado"
                estados[name] = status
                print(f" - {name}: {'✅' if spec else '❌'} {status}")
            self.reporte['frameworks_ia'] = estados
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_frameworks_ia: {str(e)}")

    def info_software(self):
        print("Sonar_total_arch: Recolectando info_software")
        try:
            procesos = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'create_time']):
                try:
                    start_time = datetime.datetime.fromtimestamp(proc.info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                    procesos.append({"pid": proc.info['pid'], "nombre": proc.info['name'], "usuario": proc.info['username'], "inicio": start_time})
                    print(f"PID: {proc.info['pid']}, Nombre: {proc.info['name']}, Usuario: {proc.info['username']}, Iniciado: {start_time}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self.reporte['procesos'] = procesos
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_software: {str(e)}")

    def info_programas_instalados(self):
        print("Sonar_total_arch: Recolectando info_programas_instalados")
        try:
            programas = []
            claves = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            for clave in claves:
                for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    try:
                        reg_key = winreg.OpenKey(root, clave, 0, winreg.KEY_READ)
                        for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
                            subkey_name = winreg.EnumKey(reg_key, i)
                            subkey = winreg.OpenKey(reg_key, subkey_name, 0, winreg.KEY_READ)
                            try:
                                nombre = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if "DisplayVersion" in [winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else "N/A"
                                ruta = winreg.QueryValueEx(subkey, "InstallLocation")[0] if "InstallLocation" in [winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else "Desconocido"
                                programas.append({"nombre": nombre, "version": version, "ruta": ruta})
                                print(f" - {nombre} | Versión: {version} | Ruta: {ruta}")
                            except FileNotFoundError:
                                continue
                            finally:
                                winreg.CloseKey(subkey)
                        winreg.CloseKey(reg_key)
                    except FileNotFoundError:
                        continue
            self.reporte['programas_instalados'] = programas
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_programas_instalados: {str(e)}")

    def info_red(self):
        print("Sonar_total_arch: Recolectando info_red")
        try:
            interfaces = {}
            try:
                ip = socket.gethostbyname(self.hostname)
                print(f"IP Local: {ip}")
            except Exception as e:
                ip = None
                print(f"Sonar_total_arch: No se pudo obtener IP local: {str(e)}")

            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for iface in addrs:
                interfaces[iface] = {"direcciones": [], "velocidad": stats[iface].speed if iface in stats else None}
                print(f"Interface: {iface}")
                for addr in addrs[iface]:
                    interfaces[iface]["direcciones"].append({"direccion": addr.address, "familia": str(addr.family)})
                    print(f"  - Dirección: {addr.address} ({addr.family.name if hasattr(addr.family, 'name') else addr.family})")
                if iface in stats:
                    print(f"  - Velocidad: {stats[iface].speed} Mbps")

            self.reporte['red'] = {"ip_local": ip, "interfaces": interfaces}
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_red: {str(e)}")

    def info_usuarios(self):
        print("Sonar_total_arch: Recolectando info_usuarios")
        try:
            usuarios = []
            for user in psutil.users():
                inicio = datetime.datetime.fromtimestamp(user.started)
                usuarios.append({"usuario": user.name, "terminal": user.terminal, "host": user.host, "inicio": str(inicio)})
                print(f"Usuario: {user.name}, Terminal: {user.terminal}, Host: {user.host}, Inicio sesión: {inicio}")
            self.reporte['usuarios'] = usuarios
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_usuarios: {str(e)}")

    def info_bateria(self):
        print("Sonar_total_arch: Recolectando info_bateria")
        try:
            battery = psutil.sensors_battery()
            if battery:
                estado = {"porcentaje": battery.percent, "en_carga": battery.power_plugged}
                print(f"Porcentaje: {battery.percent}%, En carga: {battery.power_plugged}")
            else:
                estado = "No disponible"
                print("Sonar_total_arch: No hay batería o no se puede acceder")
            self.reporte['bateria'] = estado
        except Exception as e:
            print(f"Sonar_total_arch: Error en info_bateria: {str(e)}")
            self.reporte['bateria'] = "Error al obtener datos"

    def guardar_reporte(self, ruta="sonar_total_reporte.json"):
        print(f"Sonar_total_arch: Guardando reporte en {ruta}")
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(self.reporte, f, indent=4, ensure_ascii=False)
            print(f"Sonar_total_arch: Reporte guardado en: {ruta}")
        except Exception as e:
            print(f"Sonar_total_arch: Error guardando reporte: {str(e)}")

    def ejecutar_sonar(self):
        print("\n--- SONAR TOTAL: INICIO ---\n")
        self.info_sistema()
        self.info_hardware()
        self.info_pantallas()
        self.info_frameworks_ia()
        self.info_software()
        self.info_programas_instalados()
        self.info_red()
        self.info_usuarios()
        self.info_bateria()
        self.guardar_reporte()
        print("\n--- SONAR TOTAL: FIN ---\n")

if __name__ == "__main__":
    sonar = SonarTotal()
    sonar.ejecutar_sonar()